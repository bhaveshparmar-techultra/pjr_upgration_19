{
    "name": "HR Leaves Portal",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Employees can login and see their leaves.",
    "author": "Hassan Ghannoum",
    "company": "BCI",
    "maintainer": "Hassan Ghannoum",
    "depends": ["hr_holidays", "portal"],
    "data": [
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
        "views/leaves_template.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
