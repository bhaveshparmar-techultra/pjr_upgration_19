from odoo import models, fields, _
import toolz as T
import toolz.curried as TC
import calendar
import pytz
from datetime import datetime, date, timedelta
from dateutil.rrule import rrule, DAILY
from zoneinfo import ZoneInfo


class HrLeaveLine(models.Model):
    _name = 'hr.leave.line'
    _description = 'Leave Line'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
    )
    leave_id = fields.Many2one(
        'hr.leave',
        string='Leave',
    )
    leave_type_id = fields.Many2one(
        'hr.leave.type',
        string='Leave Type',
        related='leave_id.holiday_status_id',
    )
    leave_month = fields.Integer(string='Leave Month',)
    month_working_days = fields.Float(
        string='Month Working Days',
        compute='_compute_month_working_days',
    )
    leave_duration = fields.Float(
        string='Leave Duration',
        compute='_compute_leave_duration',
    )

    leave_duration_amount = fields.Float(
        string='Leave Duration Amount',
        compute='_compute_leave_duration_amount',
    )
    employee_salary = fields.Float(string='Employee Salary',)
    from_date = fields.Date(string='From Date',)
    to_date = fields.Date(string='To Date',)
    salary_rule_code = fields.Char(string='Salary Rule Code',)
    leave_deduction_rate = fields.Float(
        string='Leave Deduction Rate',
        default=0.0,
    )
    hr_leave_line_part_ids = fields.One2many(
        'hr.leave.line.part',
        'hr_leave_line_id',
        string='Leave Line Parts',
    )

    def _compute_month_working_days(self):
        for line in self:
            start_date = pytz.timezone('utc').localize(
                datetime.combine(
                    date(line.from_date.year, line.leave_month, 1),
                    datetime.min.time(),
                ),)
            end_date = pytz.timezone('utc').localize(
                datetime.combine(
                    date(line.to_date.year, line.leave_month,
                         calendar.monthrange(line.to_date.year, line.leave_month)[1]),
                    datetime.max.time(),
                ),)

            line.month_working_days = T.pipe(
                line.employee_id.resource_calendar_id._work_intervals_batch(
                    start_date,
                    end_date,
                    resources=line.employee_id.resource_id,
                    compute_leaves=False,
                ),
                TC.keyfilter(TC.identity),  # to remove falsey keys
                lambda resouce: resouce.values(),
                TC.concat,
                list,
                TC.groupby(lambda interval: interval[0].date()),
                TC.count,
            )

    def _compute_leave_duration_amount(self):
        for line in self:
            wage = line.employee_id.version_id.wage if line.employee_id.version_id else 0
            salary_per_say = wage / line.month_working_days if line.month_working_days else 0
            line.leave_duration_amount = salary_per_say * line.leave_duration * line.leave_deduction_rate

    def adjust_time_zone(self, date):
        adjusted_date = pytz.timezone(self.env.user.tz).localize(
            datetime.combine(
                date,
                datetime.min.time(),
            ),).astimezone(pytz.timezone('utc'))
        return adjusted_date

    def _compute_leave_duration(self):
        for line in self:
            start_date = line.from_date
            end_date = line.to_date
            minimum_leave_duration = (line.to_date - line.from_date).days + 1
            duration_days = rrule(
                DAILY,
                dtstart=start_date,
                until=end_date,
            )
            weekend_days = T.pipe(
                duration_days,
                TC.filter(
                    lambda date: str(date.weekday()) not in line.employee_id.resource_calendar_id.
                    attendance_ids.mapped('dayofweek'),),
                list,
            )
            public_holidays = self.env['resource.calendar.leaves'].search([
                ('date_from', '<=', end_date),
                ('date_to', '>=', start_date),
                ('resource_id', '=', False),
            ])
            user_tz = self.env.user.tz or 'UTC'
            public_holiday_days = T.pipe(
                public_holidays,
                TC.map(lambda public_holiday: rrule(
                    DAILY,
                    dtstart=public_holiday.date_from.astimezone(ZoneInfo(user_tz)).date(),
                    until=public_holiday.date_to.astimezone(ZoneInfo(user_tz)).date(),
                )),
                TC.map(list),
                TC.concat,
                TC.map(lambda date: date.date()),
                # remove weekend days
                TC.filter(lambda date: date not in T.map(lambda weekend: weekend.date(), weekend_days)),
                list,
            )
            intersected_public_holidays = T.pipe(
                duration_days,
                TC.filter(lambda date: date.date() in public_holiday_days),
                TC.count,
            )
            weekend_days_counter = len(weekend_days)
            # case 1 : remove weekend and holiday
            if line.leave_id.holiday_status_id.remove_weekend and line.leave_id.holiday_status_id.remove_public_holiday:
                leave_duration = minimum_leave_duration - weekend_days_counter - intersected_public_holidays
            # case 2 : remove weekend only
            elif line.leave_id.holiday_status_id.remove_weekend:
                leave_duration = minimum_leave_duration - weekend_days_counter
            # case 3 : remove holiday only
            elif line.leave_id.holiday_status_id.remove_public_holiday:
                leave_duration = minimum_leave_duration - intersected_public_holidays
            else:
                leave_duration = minimum_leave_duration
            line.leave_duration = leave_duration

    def generate_sick_leave_line_parts(self):
        for leave in self:
            leave_year = leave.from_date.year
            # =====================================================================================================
            sick_leave_before = leave.env['hr.leave.line'].search(
                [
                    ('employee_id', '=', leave.employee_id.id),
                    ('leave_month', '<', leave.from_date.month),
                    ('salary_rule_code', '=', 'LD5'),
                ],
                order='leave_month desc',
            ).filtered(lambda line: line.from_date.year == leave_year)
            total_sick_leave_days_before = sum(sick_leave_before.mapped('leave_duration'))
            # =====================================================================================================
            total_sick_leave_days_through = sum(leave.mapped('leave_duration'))
            # =====================================================================================================
            if not leave.employee_id.hr_leave_employee_policy_ids:
                raise ValueError(_('No sick leave policy found for the employee %s') % leave.employee_id.name)
            start_sick_leave_policy = T.pipe(
                leave.employee_id.hr_leave_employee_policy_ids,
                TC.filter(
                    lambda policy: policy.day_from <= total_sick_leave_days_before <= policy.day_to),
                TC.first,
            )
            ploicies = T.pipe(
                leave.employee_id.hr_leave_employee_policy_ids,
                TC.filter(lambda policy: policy.sequence >= start_sick_leave_policy.sequence),
                iter,
            )
            # =====================================================================================================
            while total_sick_leave_days_through > 0:
                policy = next(ploicies)
                ploicy_days = policy.remaining_days
                minimum_days = min(ploicy_days, total_sick_leave_days_through)
                total_sick_leave_days_through -= minimum_days
                wage = self.employee_id.version_id.wage if self.employee_id.version_id else 0
                leave.env['hr.leave.line.part'].sudo().create({
                    'consumed_days':
                        minimum_days,
                    'hr_leave_employee_policy_id':
                        policy.id,
                    'hr_leave_line_id':
                        leave.id,
                    'total_deduction':
                        policy.deduction_rate *
                        (wage / leave.month_working_days if leave.month_working_days else 0) * minimum_days,
                })