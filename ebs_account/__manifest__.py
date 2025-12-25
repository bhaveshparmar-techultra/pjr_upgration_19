# -*- coding: utf-8 -*-
{
    'name': "EBS Accounting",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ever Business Solutions",
    'website': "https://www.everbsgroup.com/",

    'category': 'Accounting',
    'version': '19.0.1.0.0',
    'license': 'OPL-1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'data/decimal_accuracy.xml',
        'views/account_group_view.xml',
        'views/account_account_view.xml'
    ]
}
