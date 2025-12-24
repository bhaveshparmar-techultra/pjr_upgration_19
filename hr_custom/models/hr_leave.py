from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.rrule import rrule, MONTHLY
import calendar
import toolz as T
import toolz.curried as TC
from zoneinfo import ZoneInfo


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    leave_amount = fields.Float(
        string="Leave Amount",
        readonly=True,
        compute="_compute_leave_amount",
    )

    leave_line_ids = fields.One2many(
        'hr.leave.line',
        'leave_id',
        string='Leave Lines',
    )
    leave_line_ids_count = fields.Integer(
        string='Leave Lines Count',
        compute='_compute_leave_line_ids_count',
    )

    deduct_in_payslip = fields.Boolean(
        string='Deduct in Payslip',
        default=False,
    )

    @api.depends('date_from', 'date_to')
    def _compute_leave_amount(self):
        for leave in self:
            if leave.employee_ids:
                for employee in leave.employee_ids:
                    wage = employee.version_id.wage if employee.version_id else 0
                    per_day_salary = wage / employee.monthly_working_day if employee.monthly_working_day else 0
                    leave.leave_amount = per_day_salary * leave.number_of_days
            else:
                leave.leave_amount = 0

    def _action_validate(self, check_state=True):
        for leave in self:
            wage = leave.employee_id.version_id.wage if leave.employee_id.version_id else 0
            if leave.request_date_from.month == leave.request_date_to.month:
                self.env['hr.leave.line'].create({
                    'employee_id': leave.employee_id.id,
                    'leave_id': leave.id,
                    'from_date': leave.request_date_from,
                    'to_date': leave.request_date_to,
                    'leave_month': leave.request_date_from.month,
                    'employee_salary': wage,
                    'salary_rule_code': leave.holiday_status_id.salary_rule_code,
                    'leave_deduction_rate': leave.holiday_status_id.leave_deduction_rate,
                })
            else:
                intervals = T.pipe(
                    rrule(
                        MONTHLY,
                        dtstart=leave.request_date_from.replace(day=1),
                        until=leave.request_date_to.replace(day=1),
                        bymonthday=1,
                    ),
                    TC.map(lambda date: (
                        date,
                        date.replace(day=calendar.monthrange(date.year, date.month)[1]),
                    )),
                    lambda dates: {date[0].month: date for date in dates},
                    lambda dates: {
                        **dates,
                        leave.request_date_from.month: (
                            leave.request_date_from,
                            dates[leave.request_date_from.month][1],
                        ),
                        leave.request_date_to.month: (
                            dates[leave.request_date_to.month][0],
                            leave.request_date_to,
                        ),
                    },
                )
                leave_lines = [{
                    'employee_id': leave.employee_id.id,
                    'leave_id': leave.id,
                    'leave_month': month,
                    'from_date': start_date,
                    'to_date': end_date,
                    'employee_salary': wage,
                    'salary_rule_code': leave.holiday_status_id.salary_rule_code,
                    'leave_deduction_rate': leave.holiday_status_id.leave_deduction_rate,
                } for month, (start_date, end_date) in intervals.items()]
                self.env['hr.leave.line'].create(leave_lines)
            if leave.holiday_status_id.salary_rule_code == 'LD5':
                leave.leave_line_ids.generate_sick_leave_line_parts()
        return super()._action_validate(check_state)

    def _compute_leave_line_ids_count(self):
        for leave in self:
            leave.leave_line_ids_count = len(leave.leave_line_ids)

    def open_leave_lines(self):
        return {
            'name': _('Leave Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.line',
            'view_mode': 'list,form',
            'domain': [('leave_id', '=', self.id)],
        }

    def action_refuse(self):
        result = super().action_refuse()
        self.leave_line_ids.unlink()
        return result