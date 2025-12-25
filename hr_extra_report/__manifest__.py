{
    'name': "HR Extra Report",
    'summary': """ HR Extra Report """,
    'author': "Plennix",
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'report_xlsx_dynamic',
        'hr_payroll',
        'hr_holidays',
        'report_py3o',
        'hr_custom',  # Required: hr.leave.line model is defined here
    ],
    'external_dependencies': {
        'python': ['toolz']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'views/hr_employee_view.xml',
        'views/hr_version_view.xml',
        'wizards/hr_payslip_report_wizard.xml',
        'reports/hr_leave_report.xml',
        'reports/hr_leave_payment_report.xml',
        'reports/hr_payslip_report_xlsx.xml',
        'wizards/hr_payslip_component_report.xml',
    ],
}
