from odoo import _, api, fields, models


class HrPayslipReportWizard(models.TransientModel):
    _name = 'hr.payslip.report.wizard'
    _description = 'HR Payslip Report Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
    )
    logo_id = fields.Many2one(
        'res.company.image',
        string='Company Logo',
        required=True,
    )
    logo_image = fields.Binary(
        string='Logo Image',
        related='logo_id.image',
    )

    def print_salary_receipt_report(self):
        data = {
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
            'logo_id': self.logo_id.id,
        }
        # Use standard report_action method from ir.actions.report
        # This ensures proper Odoo 19 compatibility
        report = self.env.ref('hr_extra_report.action_report_hr_payslip_report_xlsx')
        return report.with_context(discard_logo_check=True).report_action(
            docids=self.ids,
            data=data,
            config=False,  # Skip document layout configurator
        )
