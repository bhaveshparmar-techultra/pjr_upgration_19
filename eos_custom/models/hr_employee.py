from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    joining_date = fields.Date(string='Joining Date', required=True)
    system_start_date = fields.Date(
        string='System Start Date',
        required=True,
        default=fields.Date.context_today,
    )
    file_number = fields.Char(string='File Number', required=True)