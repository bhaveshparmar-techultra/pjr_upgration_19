from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    partner_id = fields.Many2one(
        'res.partner', 'Destination Address ',
        help="Optional address where goods are to be delivered, specifically used for allotment")
    product_description = fields.Text(string="Description")


    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            # In Odoo 19, product_uom is already a record, assign it as product_uom_id for report compatibility
            aggregated_move_lines[aggregated_move_line]['product_uom_id'] = aggregated_move_lines[aggregated_move_line]['product_uom']
            product_desc = False
            for rec in self:
                if rec.product_id == aggregated_move_lines[aggregated_move_line]['product']:
                    product_desc = rec.product_description
                    break
            aggregated_move_lines[aggregated_move_line]['product_description'] = product_desc
        return aggregated_move_lines
