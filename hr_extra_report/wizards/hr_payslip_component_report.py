from odoo import _, api, fields, models


class HrPayslipComponentReportWizard(models.TransientModel):
    _name = 'hr.payslip.component.report.wizard'
    _description = 'HR Payslip Report Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
    )

    def print_component_report(self):
        data = {
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
        }
        # Use standard report_action method from ir.actions.report
        # This ensures proper Odoo 19 compatibility
        report = self.env.ref('hr_extra_report.action_hr_payslip_component_report')
        return report.with_context(discard_logo_check=True).report_action(
            docids=self.ids,
            data=data,
            config=False,  # Skip document layout configurator
        )
