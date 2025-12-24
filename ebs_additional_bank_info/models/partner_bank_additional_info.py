from odoo import fields, models, api


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    res_partner_iban = fields.Char('Iban')
    swift_code = fields.Char('Swift Code')
