from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    file_number = fields.Char(
        string='File Number',
        help='Employee file number or ID used for internal tracking',
    )
    joining_date = fields.Date(
        string='Joining Date',
        help='Date when the employee joined the company',
    )
