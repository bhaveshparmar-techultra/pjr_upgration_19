from odoo import _, models, fields, api



class StockMove(models.Model):
    _inherit = "stock.move"

    product_description = fields.Text(string="Description",related='sale_line_id.name')

    @api.constrains('partner_id')
    def _onchange_move_partner_id(self):
        for rec in self:
            move_lines = self.env['stock.move.line'].search([('move_id', '=', rec.id)])
            for line in move_lines:
                line.partner_id = rec.partner_id.id if rec.partner_id else False

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        vals = dict(
            vals,
            product_description=self.product_description,
        )
        return vals
