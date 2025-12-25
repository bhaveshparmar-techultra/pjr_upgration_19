from odoo import models, fields, api, _

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    backorder_restrict = fields.Boolean()

    @api.onchange('pick_ids')
    def compute_backorder_restrict(self):
        if not self.env.user.has_group('group_backorder.group_backorder'):
            self.backorder_restrict = True
        else:
            self.backorder_restrict = False