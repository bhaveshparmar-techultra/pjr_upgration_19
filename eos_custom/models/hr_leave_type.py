from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    absence = fields.Boolean(
        string='Absence',
        default=False,
    )