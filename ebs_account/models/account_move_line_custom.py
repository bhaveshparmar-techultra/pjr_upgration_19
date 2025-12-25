# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLineCustom(models.Model):
    _inherit = 'account.move.line'

    account_group_id = fields.Many2one('account.group', related='account_id.group_id', store=True)
    price_subtotal = fields.Monetary(digits = 'Product Price',)
    price_unit = fields.Float(digits = 'Product Price',)