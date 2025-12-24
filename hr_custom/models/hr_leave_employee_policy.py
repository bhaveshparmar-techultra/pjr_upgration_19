from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrLeaveEmployeePolicy(models.Model):
    _name = 'hr.leave.employee.policy'
    _description = 'Sick Leave Deduction Policy'
    _rec_name = 'display_name'

    sequence = fields.Integer(string='Sequence',)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
    )
    day_from = fields.Integer(
        string='From Days',
        required=True,
    )
    day_to = fields.Integer(
        string='To Days',
        required=True,
    )
    remaining_days = fields.Float(
        string='Remaining Days',
        compute='_compute_remaining_days',
    )

    consumed_days = fields.Float(
        string='Consumed Days',
        compute='_compute_consumed_days',
    )

    total_days = fields.Float(
        string='Total Days',
        compute='_compute_total_days',
    )

    deduction_base = fields.Selection(
        [
            ('salary_per_day', 'Salary Per Day'),
            ('other_base', 'Other Base'),
        ],
        string='Deduction Base',
        required=True,
        default='salary_per_day',
    )
    deduction_rate = fields.Float(
        string='Deduction Rate',
        required=True,
        default=1.0,
    )
    hr_leave_line_part_ids = fields.One2many(
        'hr.leave.line.part',
        'hr_leave_employee_policy_id',
        string='Leave Line Parts',
    )

    def _compute_consumed_days(self):
        for record in self:
            record.consumed_days = sum(record.hr_leave_line_part_ids.mapped('consumed_days'))

    def _compute_remaining_days(self):
        for record in self:
            record.remaining_days = record.total_days - record.consumed_days

    def _compute_total_days(self):
        for record in self:
            record.total_days = record.day_to - record.day_from

    @api.depends('day_from', 'day_to')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f'From {record.day_from} - To {record.day_to}'

    @api.constrains('day_from', 'day_to')
    def _check_overlap(self):
        for record in self:
            if record.day_from >= record.day_to:
                raise ValidationError('The "From" day must be less than the "To" day.')

            # Search for existing policies that overlap with the current record
            overlapping_policies = self.env['hr.leave.employee.policy'].search([
                ('id', '!=', record.id),
                ('day_from', '<=', record.day_to),
                ('day_to', '>=', record.day_from),
                ('employee_id', '=', record.employee_id.id),
            ])

            if overlapping_policies:
                raise ValidationError('The period overlaps with an existing sick leave deduction policy.')