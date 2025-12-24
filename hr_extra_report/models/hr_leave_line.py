from odoo import api, fields, models


class HrLeaveLine(models.Model):
    """Leave line model for tracking individual leave day details.

    This model is used by py3o reports to display leave duration details.
    Each line represents a portion of the leave request.
    """
    _name = 'hr.leave.line'
    _description = 'Leave Line'

    leave_id = fields.Many2one(
        'hr.leave',
        string='Leave Request',
        required=True,
        ondelete='cascade',
    )
    leave_duration = fields.Float(
        string='Duration',
        help='Duration of this leave line in days',
    )
    leave_duration_amount = fields.Float(
        string='Duration Amount',
        compute='_compute_leave_duration_amount',
        store=True,
        help='Monetary amount for this leave duration (based on daily wage)',
    )
    date = fields.Date(
        string='Date',
        help='Date of this leave line',
    )
    description = fields.Char(
        string='Description',
        help='Description for this leave line',
    )

    @api.depends('leave_duration', 'leave_id.employee_id')
    def _compute_leave_duration_amount(self):
        """Compute the monetary amount for the leave duration.

        Calculates based on employee's daily wage from their hr.version (contract).
        Daily wage = monthly wage / 30
        """
        for line in self:
            amount = 0.0
            if line.leave_id and line.leave_id.employee_id:
                employee = line.leave_id.employee_id
                # Get wage from hr.version (employee's contract)
                if employee.version_id and employee.version_id.wage:
                    daily_wage = employee.version_id.wage / 30.0
                    amount = line.leave_duration * daily_wage
            line.leave_duration_amount = amount
