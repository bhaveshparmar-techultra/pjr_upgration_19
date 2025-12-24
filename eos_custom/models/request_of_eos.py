from odoo import api, fields, models
from datetime import datetime


class EOSRequest(models.Model):
    _name = 'eos.request'
    _description = 'EOS Request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True, related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job position', readonly=True, related='employee_id.job_id')
    file_number = fields.Char(string='File Number', readonly=True, related='employee_id.file_number')
    service_type = fields.Selection([('terminate', 'Terminate'), ('resignation', 'Resignation')],
                                    required=True, string='End Of Service Type', default='resignation')
    joining_date = fields.Date(string='Joining Date', readonly=True, related='employee_id.joining_date')
    request_date = fields.Date(string='Request Date', default=fields.Date.today)

    eos_number_days = fields.Integer(string='EOS Number Days', related='employee_id.version_id.number_of_days')
    eos_due_amounts = fields.Integer(string='EOS Due Amounts', compute='_compute_final_amount', store=True)
    eos_end_date = fields.Date(string='EOS End Date', related='employee_id.version_id.eos_end_date')
    eos_net_days = fields.Float(string='EOS Net Days', related='employee_id.version_id.net_days')

    @api.depends('employee_id', 'service_type')
    def _compute_final_amount(self):
        for record in self:
            if record.employee_id.version_id:
                if record.service_type == 'terminate':
                    record.eos_due_amounts = record.employee_id.version_id.due_amount
                elif record.service_type == 'resignation':
                    due_amount = record.employee_id.version_id.due_amount
                    join_date = record.employee_id.joining_date
                    today = datetime.now().date()
                    years_employed = (today - join_date).days / 365.25 if join_date else 0
                    if years_employed < 3:
                        record.eos_due_amounts = 0.0
                    elif years_employed >= 3 and years_employed < 5:
                        record.eos_due_amounts = (due_amount * 50) / 100
                    elif years_employed >= 5 and years_employed < 10:
                        record.eos_due_amounts = due_amount * (2 / 3)
                    elif years_employed >= 10:
                        record.eos_due_amounts = due_amount
                    else:
                        record.eos_due_amounts = 0
                else:
                    record.eos_due_amounts = 0
            else:
                record.eos_due_amounts = 0