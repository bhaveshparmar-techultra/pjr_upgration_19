# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class AccountGroupCustom(models.Model):
    _inherit = 'account.group'
    _order = 'code'

    code = fields.Char(string='Code', required=True)
    parent_id = fields.Many2one('account.group', string='Parent', index=True, ondelete='cascade', readonly=False)
    user_type_id = fields.Selection([('header', 'Header'), ('posting', 'Posting')], required=True, string='Type')
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.onchange('user_type_id')
    def _onchange_user_type_id(self):
        if self.user_type_id == 'header':
            self.code_prefix_start = ''
            self.code_prefix_end = ''

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for group in self:
            prefix = group.code or ""
            group.display_name = prefix + ' - ' + group.name if prefix else group.name

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if operator == 'ilike' and not (name or '').strip():
            search_domain = []
        else:
            criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
            search_domain = criteria_operator + [('code', '=ilike', name + '%'), ('name', operator, name)]
        return self._search(expression.AND([search_domain, domain]), limit=limit, order=order)

    @api.constrains('code_prefix_start', 'code_prefix_end')
    def _constraint_prefix_overlap(self):
        for record in self:
            if record.user_type_id == 'posting':
                if not (record.code_prefix_start and record.code_prefix_end):
                    raise ValidationError(_('Account Group with posting type must contain start and end code prefix'))
                if len(record.code_prefix_start) != 4 or not record.code_prefix_start.isnumeric():
                    raise ValidationError(_('Start code prefix must be number'))
                if len(record.code_prefix_end) != 4 or not record.code_prefix_end.isnumeric():
                    raise ValidationError(_('End code prefix must be number'))

    def _adapt_accounts_for_account_groups(self, account_ids=None):
        return

    def _adapt_parent_account_group(self):
        return
