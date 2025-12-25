# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_product_accounts(self):
        accounts = super()._get_product_accounts()
        if self.landed_cost_ok:
            accounts['stock_input'] = accounts['expense']
        return accounts
