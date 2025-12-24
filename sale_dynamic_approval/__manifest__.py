# -*- coding: utf-8 -*-
{
    'name': 'Sales Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Ever Business Solutions',
    'maintainer': 'Abdalla Mohamed',
    'website': 'https://www.everbsgroup.com/',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_sale_order_wizard.xml',
        'views/sale_order.xml',
        'data/mail_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
