from odoo import api, fields, models


class SaleOrderApprover(models.Model):
    _inherit = 'sale.order'

    approved_user_id = fields.Many2one('res.users', readonly=True)
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank',
                                      help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number.',
                                      check_company=True)
    '''
       override confirmation method for the invoice to push the user who make the confirmation
       '''

    def action_confirm(self):
        res = super(SaleOrderApprover, self).action_confirm()
        for record in self:
            record.approved_user_id = self.env.user
        return res