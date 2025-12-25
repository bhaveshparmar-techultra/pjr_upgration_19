from odoo import _, api, fields, models
import uuid


class HrLeavePortal(models.Model):
    _name = 'hr.leave'
    _inherit = ['portal.mixin', 'hr.leave']
    _description = 'HR Leave Portal Extension'

    access_token = fields.Char(
        string="Access Token",
        default=lambda self: str(uuid.uuid4()),
        required=True,
        readonly=True,
        copy=False
    )

    portal_state = fields.Selection(
        compute='_compute_portal_state',
        selection=[
            ('draft', 'To Submit'),
            ('confirm', 'Manager Approval'),
            ('refuse', 'Refused'),
            ('validate1', 'HR Approval'),
            ('validate', 'Approved')
        ]
    )

    def _compute_portal_state(self):
        for rec in self:
            rec.portal_state = rec.state
