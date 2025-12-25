# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'MRP Production Consolidated',
    'version': '19.0.1.0.0',
    'website': 'https://www.plennix.com/',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Consolidated Manufacturing Order from Sale Order',
    'depends': ['mrp', 'sale', 'sale_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_consolidated.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
}
