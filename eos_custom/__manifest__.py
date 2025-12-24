{
    'name': "Employee's End Of Service",
    'summary': "Employee's End Of Service",
    'description': """ """,
    'version': '19.0.0.1',
    'author': 'Techultra Solutions Private Limited',
    'website': "",
    'license': 'LGPL-3',
    'depends': ['hr_payroll', 'hr', 'hr_holidays'],
    'external_dependencies': {
        'python': ['toolz'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/eos_security_groups.xml',
        'views/hr_employee.xml',
        'views/request_of_eos.xml',
        'views/hr_version.xml',
        'views/hr_leave_type.xml',
    ],
}
