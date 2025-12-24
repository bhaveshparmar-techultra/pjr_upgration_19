from odoo import _, api, fields, models


class HrVersion(models.Model):
    _inherit = 'hr.version'

    work_permit = fields.Float(
        string='Work Permit Allowance',
        help='Allowance or cost related to work permit processing/fees for the employee',
    )
    cash_allowance = fields.Float(
        string='Cash Allowance',
        help='Cash allowance given to the employee (meal, transport, etc.)',
    )
