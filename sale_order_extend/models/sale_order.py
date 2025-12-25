from odoo import fields, models, api


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    sale_order_remaining_value = fields.Float(
        string='Remaining Value',
        compute='_compute_sale_order_remaining_value',
        search='_search_remaining_invoice_value',
    )
    partner_id = fields.Many2one(
        domain="['&', ('parent_id', '=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total', 'amount_total')
    def _compute_sale_order_remaining_value(self):
        for record in self:
            total_invoiced = sum(
                record.invoice_ids.filtered(lambda i: i.state == 'posted').mapped('amount_total')
            )
            record.sale_order_remaining_value = record.amount_total - total_invoiced

    @api.model
    def _search_remaining_invoice_value(self, operator, value):
        sale_order_ids = self.env['sale.order'].search([])
        target_orders = []
        for order in sale_order_ids:
            total_invoiced = sum(
                order.invoice_ids.filtered(lambda i: i.state == 'posted').mapped('amount_total')
            )
            remaining = order.amount_total - total_invoiced

            if operator == '>' and remaining > value:
                target_orders.append(order.id)
            elif operator == '<' and remaining < value:
                target_orders.append(order.id)
            elif operator == '=' and remaining == value:
                target_orders.append(order.id)
            elif operator == '>=' and remaining >= value:
                target_orders.append(order.id)
            elif operator == '<=' and remaining <= value:
                target_orders.append(order.id)
            elif operator == '!=' and remaining != value:
                target_orders.append(order.id)

        return [('id', 'in', target_orders)]
