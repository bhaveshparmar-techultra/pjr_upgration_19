{
    'name': 'Sale Order Extend',
    'version': '19.0.1.0.0',
    'summary': 'Adds remaining value field to sale orders',
    'description': 'Extends sale order with remaining invoice value calculation',
    'category': 'Sales',
    'author': 'EBS - Omar Khaled',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'views/sale_order_view.xml',
        'views/template.xml',
    ],
    'installable': True,
    'auto_install': False,
}
