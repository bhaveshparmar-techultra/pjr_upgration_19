{
    "name": "Accrual Approvals",
    "summary": "Generate allocation lines for accruals need to be approved",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": ["hr_holidays", "hr", "eos_custom", "hr_custom"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/hr_leave_allocation_line_views.xml",
        "views/hr_leave_type.xml",
    ],
}
