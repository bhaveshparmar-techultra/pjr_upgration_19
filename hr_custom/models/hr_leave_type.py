from odoo import _, api, fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    deduct_in_payslip = fields.Boolean(
        string='Deduct in Payslip',
        default=False,
    )
    salary_rule_code = fields.Char(
        string='Salary Rule Code',
    )
    leave_deduction_rate = fields.Float(
        string='Leave Deduction Rate',
        default=1.0,
    )
    remove_weekend = fields.Boolean(
        string='Remove Weekend',
        default=False,
    )
    remove_public_holiday = fields.Boolean(
        string='Remove Public Holiday',
        default=False,
    )

