from datetime import datetime
import toolz as T
import toolz.curried as TC
from odoo import fields, models, api


class HrVersion(models.Model):
    _inherit = 'hr.version'

    number_of_days = fields.Integer(
        string='Number Of Days',
        compute='_compute_number_of_days',
    )
    due_amount = fields.Integer(
        string="Due Amount",
        compute='_compute_due_amount',
    )
    employee_joining_date = fields.Date(
        related='employee_id.joining_date',
        string='Joining Date',
        store=True,
    )
    unpaid_leaves = fields.Float(
        string='Unpaid Leaves',
        compute='_compute_unpaid_leaves',
    )
    absence_days = fields.Float(
        string='Absence Days',
        compute='_compute_absence_days',
    )
    net_days = fields.Float(
        string='Net Days',
        compute='_compute_net_days',
    )

    absenece_days_opening_balance = fields.Float(
        string='Absence Days Opening Balance',
        default=0.0,
    )

    unpaid_leaves_opening_balance = fields.Float(
        string='Unpaid Leaves Opening Balance',
        default=0.0,
    )
    debit_opening_balance = fields.Float(
        string="Debit Opening Balance",
        default=0.0,
    )
    eos_end_date = fields.Date(
        string='EOS End Date',
        default=fields.Date.today,
    )

    @api.depends('employee_joining_date', 'eos_end_date')
    def _compute_number_of_days(self):
        for record in self:
            if record.employee_joining_date:
                today = fields.Date.context_today(record)
                end_date = record.eos_end_date
                employee_joining_date = record.employee_joining_date
                delta = (end_date if end_date else today) - employee_joining_date
                record.number_of_days = delta.days
            else:
                record.number_of_days = 0

    @api.depends('employee_joining_date', 'wage', 'net_days', 'debit_opening_balance')
    def _compute_due_amount(self):
        for record in self:
            if record.employee_joining_date:
                years_employed = record.net_days / 365.25
                monthly_salary = record.wage
                daily_salary = monthly_salary / 26
                if years_employed <= 5:
                    due_amount = daily_salary * (15 * years_employed)
                else:
                    due_amount = daily_salary * (15 * 5) + daily_salary * (26 * (years_employed - 5))
                record.due_amount = due_amount
            else:
                record.due_amount = 0
            record.due_amount -= record.debit_opening_balance

    @api.depends('employee_id')
    def _compute_unpaid_leaves(self):
        for version in self:
            version.unpaid_leaves = version.unpaid_leaves_opening_balance
            if version.employee_id.system_start_date:
                start_date = datetime.combine(version.employee_id.system_start_date, datetime.min.time())
                end_date = datetime.now()
                unpaid_leaves = T.pipe(
                    version.employee_id.list_leaves(start_date, end_date),
                    TC.filter(lambda l: l[2].holiday_id.holiday_status_id.unpaid),
                    TC.map(lambda l: l[1]),
                    sum,
                    lambda hours: hours / version.employee_id.resource_id.calendar_id.hours_per_day if version.employee_id.resource_id.calendar_id.hours_per_day else 0,
                )
                version.unpaid_leaves += unpaid_leaves
            else:
                version.unpaid_leaves = 0

    @api.depends('employee_id')
    def _compute_absence_days(self):
        for version in self:
            version.absence_days = version.absenece_days_opening_balance
            if version.employee_id.system_start_date:
                start_date = datetime.combine(version.employee_id.system_start_date, datetime.min.time())
                end_date = datetime.now()
                absence_days = T.pipe(
                    version.employee_id.list_leaves(start_date, end_date),
                    TC.filter(lambda l: l[2].holiday_id.holiday_status_id.absence),
                    TC.map(lambda l: l[1]),
                    sum,
                    lambda hours: hours / version.employee_id.resource_id.calendar_id.hours_per_day if version.employee_id.resource_id.calendar_id.hours_per_day else 0,
                )
                version.absence_days += absence_days
            else:
                version.absence_days = 0

    @api.depends('number_of_days', 'absence_days', 'unpaid_leaves')
    def _compute_net_days(self):
        for version in self:
            version.net_days = version.number_of_days - version.absence_days - version.unpaid_leaves
