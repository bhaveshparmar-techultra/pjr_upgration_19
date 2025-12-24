# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrVersion(models.Model):
    _inherit = 'hr.version'

    overtime_calculation = fields.Boolean(
        related='company_id.overtime_calculation',
        string="Overtime Calculation",
        store=True,
    )
    started_deduction_date = fields.Date(string="Started Deduction Date")
    employee_ins_amount = fields.Float(
        string="Amount",
        copy=False,
    )
    emp_ins_start_date = fields.Date(
        string="Start Date",
        copy=False,
    )
    emp_ins_end_date = fields.Date(
        string="End Date",
        copy=False,
    )
    emp_ins_period = fields.Integer(
        string="Employee Period",
        copy=False,
    )
    family_ins_amount = fields.Float(
        string="Amount",
        copy=False,
    )
    family_ins_start_date = fields.Date(
        string="Start Date",
        copy=False,
    )
    family_ins_end_date = fields.Date(
        string="End Date",
        copy=False,
    )
    family_ins_period = fields.Integer(
        string="Family Period",
        copy=False,
    )
    yearly_ticket = fields.Float(
        string="Yearly Ticket",
        copy=False,
    )
    phone_limit = fields.Float(
        string="Phone Limit",
        copy=False,
    )
    petrol = fields.Float(
        string="Petrol",
        copy=False,
    )
    home_allowance = fields.Float(
        string="Home Allowance",
        copy=False,
    )
    medical_insurance = fields.Float(
        string="Medical Insurance",
        copy=False,
    )
    remaining_family_period = fields.Integer(
        string="Remaining Family Period",
        compute='_compute_remaining_family_period',
    )

    remaining_emp_period = fields.Integer(
        string="Remaining Employee Period",
        compute='_compute_remaining_emp_period',
    )

    active_employee_insurance = fields.Boolean(
        string="Active Employee Insurance",
        copy=False,
    )

    active_family_insurance = fields.Boolean(
        string="Active Family Insurance",
        copy=False,
    )
    # other allowances
    other_allowances = fields.Float(
        string="Other Allowances",
        copy=False,
    )
    # wps salary
    wps_salary = fields.Float(
        string="WPS Salary",
        copy=False,
    )

    def employee_insurance_payslip_domain(self):
        return [
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'done'),
            ('line_ids.code', '=', 'EMP_INSURANCE_DED'),
        ]

    def family_insurance_payslip_domain(self):
        return [
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'done'),
            ('line_ids.code', '=', 'FAMILY_INSURANCE_DED'),
        ]

    def _compute_remaining_emp_period(self):
        for record in self:
            payslip_counter = self.env['hr.payslip'].search_count(record.employee_insurance_payslip_domain())
            record.remaining_emp_period = record.emp_ins_period - payslip_counter

    def _compute_remaining_family_period(self):
        for record in self:
            payslip_counter = self.env['hr.payslip'].search_count(record.family_insurance_payslip_domain())
            record.remaining_family_period = record.family_ins_period - payslip_counter

    def open_employee_insurance_payslip(self):
        return {
            'name': _('Employee Insurance Payslip'),
            'view_mode': 'list,form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'domain': self.employee_insurance_payslip_domain(),
            'target': 'new',
        }

    def open_family_insurance_payslip(self):
        return {
            'name': _('Family Insurance Payslip'),
            'view_mode': 'list,form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'domain': self.family_insurance_payslip_domain(),
            'target': 'new',
        }