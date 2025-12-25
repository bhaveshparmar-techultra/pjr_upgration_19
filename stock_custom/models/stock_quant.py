from odoo import _, models, fields, api


class StockQuant(models.Model):
    _inherit = "stock.quant"

    can_edit_inventory_quantity =  fields.Boolean(compute='_compute_can_edit_inventory')

    def _compute_can_edit_inventory(self):
        for rec in self:
            if self.env.user.has_group('stock_custom.inventory_quant_user_group'):
                rec.can_edit_inventory_quantity = True
            else:
                rec.can_edit_inventory_quantity = False
