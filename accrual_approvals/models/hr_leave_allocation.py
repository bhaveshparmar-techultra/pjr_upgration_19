from collections import defaultdict
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.tools.date_utils import get_timedelta
from odoo.addons.resource.models.utils import HOURS_PER_DAY


class HolidaysAllocation(models.Model):
  _inherit = "hr.leave.allocation"

  hr_leave_allocation_line_ids = fields.One2many(
      "hr.leave.allocation.line",
      "allocation_id",
      string="Allocation Lines",
  )

  def generate_allocation_lines(self, duration):
    for allocation in self:
      # In Odoo 19, allocation has single employee_id instead of employee_ids
      if allocation.employee_id:
        self.env['hr.leave.allocation.line'].create({
            'allocation_id': allocation.id,
            'employee_id': allocation.employee_id.id,
            'duration': duration,
        })

  def _process_accrual_plans(self, date_to=False, force_period=False, log=True):
    date_to = date_to or fields.Date.today()
    first_allocation = _("""This allocation have already ran once, any modification won't be effective to the days allocated to the employee. If you need to change the configuration of the allocation, cancel and create a new one.""")
    for allocation in self:
      level_ids = allocation.accrual_plan_id.level_ids.sorted('sequence')
      if not level_ids:
        continue
      if not allocation.nextcall:
        first_level = level_ids[0]
        first_level_start_date = allocation.date_from + get_timedelta(
            first_level.start_count,
            first_level.start_type,
        )
        if date_to < first_level_start_date:
          continue
        allocation.lastcall = max(allocation.lastcall, first_level_start_date)
        allocation.nextcall = first_level._get_next_date(allocation.lastcall)
        if len(level_ids) > 1:
          second_level_start_date = allocation.date_from + get_timedelta(
              level_ids[1].start_count, level_ids[1].start_type)
          allocation.nextcall = min(second_level_start_date, allocation.nextcall)
        if log:
          allocation._message_log(body=first_allocation)
      days_added_per_level = defaultdict(lambda: 0)
      while allocation.nextcall <= date_to:
        (current_level,
         current_level_idx) = allocation._get_current_accrual_plan_level_id(allocation.nextcall)
        if not current_level:
          break
        current_level_maximum_leave = current_level.maximum_leave if current_level.added_value_type == "days" else current_level.maximum_leave / (
            allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY)
        nextcall = current_level._get_next_date(allocation.nextcall)
        period_start = current_level._get_previous_date(allocation.lastcall)
        period_end = current_level._get_next_date(allocation.lastcall)
        if current_level_idx < (len(level_ids) -
                                1) and allocation.accrual_plan_id.transition_mode == 'immediately':
          next_level = level_ids[current_level_idx + 1]
          current_level_last_date = allocation.date_from + get_timedelta(
              next_level.start_count,
              next_level.start_type,
          )
          if allocation.nextcall != current_level_last_date:
            nextcall = min(nextcall, current_level_last_date)
        if allocation.lastcall.year < allocation.nextcall.year and\
            current_level.action_with_unused_accruals == 'postponed' and\
            current_level.postpone_max_days > 0:
          allocation_days = allocation.number_of_days - allocation.leaves_taken
          allowed_to_keep = max(0, current_level.postpone_max_days - allocation_days)
          number_of_days = min(allocation_days, current_level.postpone_max_days)
          # allocation.number_of_days = number_of_days + allocation.leaves_taken
          allocation.generate_allocation_lines(2.5)
          total_gained_days = sum(days_added_per_level.values())
          days_added_per_level.clear()
          days_added_per_level[current_level] = min(total_gained_days, allowed_to_keep)
        gained_days = allocation._process_accrual_plan_level(
            current_level,
            period_start,
            allocation.lastcall,
            period_end,
            allocation.nextcall,
        )
        days_added_per_level[current_level] += gained_days
        if current_level_maximum_leave > 0 and sum(
            days_added_per_level.values()) > current_level_maximum_leave:
          days_added_per_level[current_level] -= sum(
              days_added_per_level.values()) - current_level_maximum_leave

        allocation.lastcall = allocation.nextcall
        allocation.nextcall = nextcall
        if force_period and allocation.nextcall > date_to:
          allocation.nextcall = date_to
          force_period = False

      if days_added_per_level:
         allocation.generate_allocation_lines(2.5)

  @api.model
  def _update_accrual_custom_date(self, start_date, end_date):
    """
    Method called by the cron task in order to increment the number_of_days when
    necessary.
    start_date: 'YYYY-MM-DD' date from which the allocation will be updated
    end_date: 'YYYY-MM-DD' date until which the allocation will be updated
    """
    start_date = fields.Date.from_string(start_date)
    end_date = fields.Date.from_string(end_date)
    allocations = self.search([
        ('allocation_type', '=', 'accrual'),
        ('state', '=', 'validate'),
        ('accrual_plan_id', '!=', False),
        ('employee_id', '!=', False),
        ('date_from', '>=', start_date),
        ('date_to', '<=', end_date),
    ])
    allocations._process_accrual_plans()
