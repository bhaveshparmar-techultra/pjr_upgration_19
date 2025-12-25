# Copyright 2017-20 kbizsoft
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float(
        string="Discount (Fixed)",
        digits="Product Price",
        help="Fixed amount discount.",
    )

    @api.onchange("discount_amount")
    def _onchange_discount_amount(self):
        total = self.quantity * self.price_unit
        self.discount = (self.discount_amount / total) * 100   if total else 0.0


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_fixed = fields.Float(
        string="Discount (Fixed)",
        digits="Product Price",
        help="Fixed amount discount.",
    ) 

    @api.onchange("discount_fixed")
    def _onchange_discount_fixed(self):
          total = self.product_uom_qty * self.price_unit
          self.discount = (self.discount_fixed / total) * 100 if total else 0.0


    def _prepare_invoice_line(self, **optional_values):
        """Inherit function for update ton quantity and unit quantity when create invoice"""
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res["discount_amount"] = self.discount_fixed
        return res
