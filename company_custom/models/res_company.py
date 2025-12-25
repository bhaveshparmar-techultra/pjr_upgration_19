from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    company_id = fields.Many2one('res.company', 'Company', index=True)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """
        Override to add custom ref handling from client_order_ref.
        Odoo 19: Removed deprecated analytic_tag_ids handling.
        """
        result = super().create_invoices()

        # Get the active sale orders
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if sale_orders:
            # Get invoices created from these sale orders
            invoices = sale_orders.invoice_ids.filtered(
                lambda inv: inv.state == 'draft'
            )
            if invoices:
                # Collect client order refs
                refs = list(filter(bool, sale_orders.mapped('client_order_ref')))
                for invoice in invoices:
                    if refs and not invoice.ref:
                        invoice.ref = ','.join(refs)

        return result


class AccountMove(models.Model):
    _inherit = 'account.move'


class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    other_partner = fields.Many2one('res.partner', 'Other Partner')

    @api.model
    def create(self, vals):
        company = super().create(vals)
        # Add the following line to avoid user error: Incompatible companies on records.
        company.partner_id.company_id = company.id  # or you can make it = False
        return company
