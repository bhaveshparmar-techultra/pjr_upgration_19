from odoo import api, fields, models


class HrLeaveLine(models.Model):
    """Leave line model extension for py3o reports.

    This extends the hr.leave.line model defined in hr_custom
    to add report-specific fields and computations.
    """
    _inherit = 'hr.leave.line'

    # Additional fields for reports (if not already defined in hr_custom)
    date = fields.Date(
        string='Date',
        help='Date of this leave line',
    )
    description = fields.Char(
        string='Description',
        help='Description for this leave line',
    )
