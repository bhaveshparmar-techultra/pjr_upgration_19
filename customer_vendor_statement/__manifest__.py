# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Customer Vendor Statement',
    'version': '19.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Statement for customer and Vendor by currency',
    'description': 'open any customer or vendor form and click on action--> Customer / Vendor Statement',
    "author": "Abdallah Mohamed",
    'website': 'abdalla_mohammed@outlook.com',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/statement.xml',
        'wizard/customer_vendor_statement_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
