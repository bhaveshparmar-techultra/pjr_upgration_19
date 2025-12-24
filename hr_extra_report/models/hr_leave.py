from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_line_ids = fields.One2many(
        'hr.leave.line',
        'leave_id',
        string='Leave Lines',
        help='Detailed lines for this leave request (used in py3o reports)',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create leave lines when leave is created."""
        records = super().create(vals_list)
        records._ensure_leave_lines()
        return records

    def write(self, vals):
        """Update leave lines when number_of_days changes."""
        result = super().write(vals)
        if 'number_of_days' in vals or 'date_from' in vals:
            self._ensure_leave_lines()
        return result

    def read(self, fields=None, load='_classic_read'):
        """Ensure leave lines exist when reading records (for reports)."""
        # Ensure leave lines exist before reading leave_line_ids
        if fields is None or 'leave_line_ids' in fields:
            self._ensure_leave_lines()
        return super().read(fields=fields, load=load)

    def _ensure_leave_lines(self):
        """Ensure leave lines exist for this leave record.

        Creates a single leave line with the total duration if none exist.
        This is used by py3o reports that reference leave_line_ids.
        """
        for record in self:
            if not record.leave_line_ids:
                self.env['hr.leave.line'].create({
                    'leave_id': record.id,
                    'leave_duration': record.number_of_days,
                    'date': record.date_from.date() if record.date_from else False,
                    'description': record.holiday_status_id.name if record.holiday_status_id else '',
                })
            else:
                # Update existing line if duration changed
                line = record.leave_line_ids[0]
                if line.leave_duration != record.number_of_days:
                    line.write({
                        'leave_duration': record.number_of_days,
                        'date': record.date_from.date() if record.date_from else False,
                    })

    def py3o_get_leave_type_summary(self):
        """Returns a summary of leave type usage for py3o reports.

        In Odoo 19, virtual_remaining_leaves is a computed field on hr.leave.
        """
        self.ensure_one()
        virtual_remaining = self.virtual_remaining_leaves or 0
        max_leaves = self.holiday_status_id.max_leaves or 0
        return f"{round(virtual_remaining, 2)} remaining out of {round(max_leaves, 2)}"
