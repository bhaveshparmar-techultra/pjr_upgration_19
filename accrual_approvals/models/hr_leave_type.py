from odoo import _, api, fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'


    is_annual = fields.Boolean(
        string='Is Annual Leave',
    )