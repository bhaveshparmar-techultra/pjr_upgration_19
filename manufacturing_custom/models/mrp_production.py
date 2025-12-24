from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_description = fields.Text(compute='_get_product_description', string='Product Description')

    def _get_product_description(self):
        for rec in self:
            # Odoo 19: Use sale_line_id if sale_mrp is installed
            # This field is added by sale_mrp module when MO is created from SO
            if 'sale_line_id' in rec._fields and rec.sale_line_id:
                rec.product_description = rec.sale_line_id.name
            else:
                rec.product_description = False
