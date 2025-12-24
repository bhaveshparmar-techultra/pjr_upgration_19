from odoo import models, fields, api


class AccountMoveInvoicePrint(models.Model):
    _inherit = 'account.move'

    sale_order_id = fields.Many2one('sale.order')
    approved_user_id = fields.Many2one('res.users', readonly=True)

    def _invoice_sale_order_ref(self):
        for record in self:
            if record.invoice_line_ids:
                return record.mapped('invoice_line_ids').sale_line_ids.order_id.name or ''
            else:
                return ''

    '''
    override confirmation method for the invoice to push the user who make the confirmation
    '''

    def action_post(self):
        res = super(AccountMoveInvoicePrint, self).action_post()
        for record in self:
            record.approved_user_id = self.env.user
        return res

    @api.depends("invoice_line_ids")
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = max(sale.mapped("invoice_line_ids.sequence") or [0]) + 1

    max_line_sequence = fields.Integer(
        string="Max sequence in lines", compute="_compute_max_line_sequence", store=True
    )

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in sorted(rec.invoice_line_ids, key=lambda x: (x.sequence, x.id)):
                if line.sequence != current_sequence:
                    line.sequence = current_sequence
                current_sequence += 1

    def write(self, line_values):
        res = super(AccountMoveInvoicePrint, self).write(line_values)
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(AccountMoveInvoicePrint, self.with_context(keep_line_sequence=True)).copy(
            default
        )


class SaleOrderLine(models.Model):
    _inherit = "account.move.line"

    # re-defines the field to change the default
    sequence = fields.Integer(
        help="Gives the sequence of this line when displaying the sale order.",
        default=9999,
    )

    # displays sequence on the order line
    sequence2 = fields.Integer(
        help="Shows the sequence of this line in the sale order.",
        related="sequence",
        string="Line Number",
        readonly=True,
        store=True,
    )

    # @api.model
    # def create(self, values):
    def write(self, values):
        line = super(SaleOrderLine, self).write(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get("keep_line_sequence"):
            self.move_id._reset_sequence()
        return line


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def get_paperformat(self):
        # force the right format (instaed of /A4) when print invoice, only if we are using the 'PJR Commercial Publications Editing L.L.C' company
        res = super(IrActionsReport, self).get_paperformat()
        if self and self.name in ('Invoices without Payment','Invoices') and self.env.company.name == 'PJR Commercial Publications Editing L.L.C':
            paperformat_id = self.env.ref('ebs_custom_prints.paperformat_invoice_order', False)
            return paperformat_id
        else:
            return res