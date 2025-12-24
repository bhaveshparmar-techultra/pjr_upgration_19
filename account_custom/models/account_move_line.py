# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLineCustom(models.Model):
    _inherit = 'account.move.line'

    # Keep original field definitions for data migration compatibility
    product_category = fields.Many2one(
        related='product_id.categ_id',
        store=True,
        string='Product Category',
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="account_move_line_id_analytic_account_id_rel",
        column1="account_move_line_id",
        column2="analytic_account_id",
        string="Analytic Account",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            dict_analytic = {}
            list_analytic = []
            if rec.analytic_account_ids:
                for line in rec.analytic_account_ids:
                    dict_analytic[str(line.id)] = 100
                rec.analytic_distribution = dict_analytic
            elif rec.analytic_distribution:
                for account, value in rec.analytic_distribution.items():
                    list_analytic.append(int(account))
                rec.analytic_account_ids = [(6, 0, list_analytic)]
        return res

    def write(self, vals):
        flag = False
        for rec in self:
            if 'analytic_account_ids' in vals and not flag:
                analytic_account_ids_list = False
                if type(vals['analytic_account_ids'][0]) is tuple or type(vals['analytic_account_ids'][0]) is list:
                    analytic_account_ids_list = vals['analytic_account_ids'][0][2]
                elif type(vals['analytic_account_ids'][0]) is int:
                    analytic_account_ids_list = vals['analytic_account_ids']
                if analytic_account_ids_list:
                    analytic_accounts = {}
                    for account in analytic_account_ids_list:
                        if rec.analytic_distribution:
                            for account_id, distribution in rec.analytic_distribution.items():
                                if account == int(account_id):
                                    analytic_accounts[str(account)] = distribution
                                    break
                                else:
                                    analytic_accounts[str(account)] = 100
                        else:
                            analytic_accounts[str(account)] = 100
                    vals['analytic_distribution'] = analytic_accounts
            elif 'analytic_distribution' in vals:
                flag = True
                analytic_accounts_list = []
                if vals['analytic_distribution']:
                    for account_id, distribution in vals['analytic_distribution'].items():
                        analytic_accounts_list.append(int(account_id))
                    vals['analytic_account_ids'] = [(6, 0, analytic_accounts_list)]

        return super().write(vals)