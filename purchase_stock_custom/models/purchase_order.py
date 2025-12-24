from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Odoo 19: Removed 'states' parameter as READONLY_STATES was removed
    # The field is already defined in purchase_stock, we're just overriding default
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Deliver To',
        required=True,
        default=False,
        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment",
    )

    company_check = fields.Boolean(
        string="Company Check",
        compute="_compute_company_check",
    )

    @api.depends('company_id')
    def _compute_company_check(self):
        for rec in self:
            rec.company_check = self.env.company.id == 1

    @api.onchange('company_id')
    def _onchange_company_id(self):
        return False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    length = fields.Float(string="Length")
    width = fields.Float(string="Width")

    @api.onchange('width', 'length')
    def onchange_product_qty(self):
        for rec in self:
            rec.product_qty = rec.width * rec.length
