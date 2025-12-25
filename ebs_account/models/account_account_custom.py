# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountAccountCustom(models.Model):
    _inherit = 'account.account'

    group_id = fields.Many2one('account.group', string='Account Group', compute=False, readonly=False)

    @api.onchange('group_id')
    def get_type_code(self):
        for record in self:
            group_code = record.group_id.code if record.group_id else False
            if not record.code or (group_code and group_code not in record.code):
                record.code = group_code + '-' if group_code else False
            if record.group_id:
                record.currency_id = record.group_id.currency_id
    #
    # @api.constrains('code')
    # def _validate_code(self):
    #     for record in self:
    #         if record.code.find('-') == -1:
    #             raise ValidationError(_('Account Code must contain - '))
    #
    #         code = record.code.replace('-', '')
    #         if code.find('copy') == -1:
    #             if len(code) != 8:
    #                 raise ValidationError(_('Account Code format must be ####-####'))
    #
    #             account_number = record.code.split('-')[-1]
    #             if self.group_id:
    #                 if self.group_id.code_prefix_start and self.group_id.code_prefix_end:
    #                     if not (int(self.group_id.code_prefix_start) <= int(account_number) <= int(
    #                             self.group_id.code_prefix_end)):
    #                         raise ValidationError(_('Account Code is out of range of the group.'))
    #
    # @api.model
    # def _search_new_account_code(self, company, digits, prefix):
    #     for num in range(1, 10000):
    #         new_code = str(prefix.ljust(digits - len(str(num)), '0')) + str(num)
    #         rec = self.search([('code', '=', new_code), ('company_id', '=', company.id)], limit=1)
    #         if not rec:
    #             return new_code
    #     raise UserError(_('Cannot generate an unused account code.'))
