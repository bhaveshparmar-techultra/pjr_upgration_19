# -*- coding: utf-8 -*-

from odoo import models


class StockRuleInherit(models.Model):
    _inherit = 'stock.rule'

    def _should_auto_confirm_procurement_mo(self, p):
        """Override to prevent auto-confirmation of MOs created from procurements.

        In Odoo 19, this method controls whether MOs are auto-confirmed.
        Return False to keep MOs in draft state.
        """
        return False
