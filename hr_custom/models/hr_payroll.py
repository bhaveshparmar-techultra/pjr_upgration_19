from odoo import fields, models, _
from datetime import timedelta, date
import toolz as T
import toolz.curried as TC


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    overtime_calculation = fields.Boolean(
        related='company_id.overtime_calculation',
        string="Overtime Calculation",
        store=True,
    )
    overtime_total_amount = fields.Float(
        string='Overtime Total Amount',
        compute='_compute_overtime_total_amount',
    )

    delay_total_amount = fields.Float(
        string='Delay Total Amount',
        compute='_compute_delay_total_amount',
    )

    paid_leave_amount_deducted = fields.Float(
        string='Paid Leave Amount Deducted',
        compute='_compute_paid_leave_amount_deducted',
    )
    unpaid_leave_amount_deducted = fields.Float(
        string='Unpaid Leave Amount Deducted',
        compute='_compute_unpaid_leave_amount_deducted',
    )
    annual_leave_amount_deducted = fields.Float(
        string='Annual Leave Amount Deducted',
        compute='_compute_annual_leave_amount_deducted',
    )

    other_leave_amount_deducted = fields.Float(
        string='Other Leave Amount Deducted',
        compute='_compute_other_leave_amount_deducted',
    )

    sick_leave_amount_deducted = fields.Float(
        string='Sick Leave Amount Deducted',
        compute='_compute_sick_leave_amount_deducted',
    )

    def months_between(self, date_from, date_to):
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        year_diff = date_to.year - date_from.year
        month_diff = date_to.month - date_from.month
        total_months = year_diff * 12 + month_diff
        if date_to.day > date_from.day:
            total_months += 1
        return total_months

    def get_leave_days_within_payslip_period(self):
        self.ensure_one()
        period_start_date = self.date_from
        period_end_date = self.date_to
        leave_requests = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', period_end_date),
            ('date_to', '>=', period_start_date),
        ])
        total_leave_days = 0
        friday_count = 0
        for leave in leave_requests:
            leave_start = max(leave.date_from.date(), period_start_date)
            leave_end = min(leave.date_to.date(), period_end_date)
            current_date = leave_start
            while current_date <= leave_end:
                if current_date.weekday() == 4:
                    friday_count += 1
                current_date += timedelta(days=1)
            total_leave_days += (leave_end - leave_start).days + 1
        total_leave_days = total_leave_days - friday_count
        return total_leave_days

    def compute_sheet(self):
        res = super().compute_sheet()
        for payslip in self:
            if payslip.overtime_calculation:
                attendance_ids = self.env['hr.attendance'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('check_in', '>=', payslip.date_from),
                    ('check_out', '<=', payslip.date_to),
                ])
                over_time = missing_hours = hours_per_day = 0
                for attendance in attendance_ids:
                    hours_per_day = self.env['resource.calendar'].search(
                        [('company_id', '=', attendance.employee_id.company_id.id)], limit=1).hours_per_day
                    if attendance.over_time:
                        over_time += attendance.over_time
                    if attendance.missing_hours:
                        missing_hours += attendance.missing_hours
                leave_days_current_month = payslip.get_leave_days_within_payslip_period()
                version = payslip.employee_id.version_id
                if version and version.started_deduction_date:
                    started_deduction_date = version.started_deduction_date
                    today = date.today()
                    date_from = payslip.date_from
                    date_to = payslip.date_to
                    months_between_dates = payslip.months_between(date_from, date_to) or 0
                    overtime_amount = basic_amount = 0
                    deduction = 0
                    for line in payslip.line_ids:
                        if line.code == "BASIC":
                            basic_amount += line.amount
                        if line.code == 'OT':
                            if over_time and version.wage_type == 'monthly':
                                all_day_amount = version.wage / payslip.employee_id.monthly_working_day if payslip.employee_id.monthly_working_day else 0
                                per_hour_amount = all_day_amount / hours_per_day if hours_per_day else 0
                                line.amount = per_hour_amount
                                line.quantity = over_time
                                line.rate = 1.5
                                overtime_amount += line.total
                            else:
                                line.amount = 0.0
                                line.quantity = 0
                        if line.code == 'MH':
                            if missing_hours and version.wage_type == 'monthly':
                                missing_all_day_amount = version.wage / payslip.employee_id.monthly_working_day if payslip.employee_id.monthly_working_day else 0
                                missing_per_hour_amount = missing_all_day_amount / hours_per_day if hours_per_day else 0
                                line.amount = -missing_per_hour_amount
                                line.quantity = missing_hours
                                deduction += line.amount * line.quantity
                            else:
                                line.amount = -0.0
                                line.quantity = 0
                                line.quantity = missing_hours
                        if line.code == 'FAMILY_INSURANCE_DED':
                            if today >= started_deduction_date:
                                family_period = version.family_ins_period or 0.0
                                family_amount = version.family_ins_amount or 0.0
                                family_month_wise_amount = family_amount / family_period if family_period else 0
                                line.amount = -family_month_wise_amount
                                line.quantity = months_between_dates
                                deduction += line.amount * line.quantity
                            else:
                                line.amount = -0.0
                                line.quantity = 0
                        if line.code == 'EMP_INSURANCE_DED':
                            if today >= started_deduction_date:
                                employee_period = version.emp_ins_period or 0.0
                                employee_amount = version.employee_ins_amount or 0.0
                                employee_month_wise_amount = employee_amount / employee_period if employee_period else 0
                                line.amount = -employee_month_wise_amount
                                line.quantity = months_between_dates
                                deduction += line.amount * line.quantity
                            else:
                                line.amount = -0.0
                                line.quantity = 0
                        if line.code == 'VEC':
                            if today >= started_deduction_date:
                                all_day_amount = version.wage / payslip.employee_id.monthly_working_day if payslip.employee_id.monthly_working_day else 0
                                line.amount = -(all_day_amount * leave_days_current_month)
                                deduction += line.amount
                                line.quantity = 1
                            else:
                                line.amount = -0.0
                                line.quantity = 0
                        if line.code == 'GROSS':
                            line.amount = basic_amount + overtime_amount
                            line.quantity = 1
                        if line.code == 'NET':
                            gross = basic_amount + overtime_amount
                            line.amount = gross + deduction
                            line.quantity = 1
        return res

    def _compute_overtime_total_amount(self):
        for payslip in self:
            payslip.overtime_total_amount = 0
            if payslip.employee_id.has_overtime:
                payslip.overtime_total_amount = T.pipe(
                    payslip.employee_id.attendance_ids,
                    TC.filter(lambda x: payslip.date_from <= x.check_in.date() <= payslip.date_to),
                    TC.map(TC.get('overtime_amount')),
                    sum,
                )

    def _compute_delay_total_amount(self):
        for payslip in self:
            payslip.delay_total_amount = 0
            if payslip.employee_id.has_delay:
                payslip.delay_total_amount = T.pipe(
                    payslip.employee_id.attendance_ids,
                    TC.filter(lambda x: payslip.date_from <= x.check_in.date() <= payslip.date_to),
                    TC.map(TC.get('delay_amount')),
                    sum,
                )

    def _compute_paid_leave_amount_deducted(self):
        for payslip in self:
            payslip.paid_leave_amount_deducted = sum(self.env['hr.leave.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('leave_month', '>=', payslip.date_from.month),
                ('leave_month', '<=', payslip.date_to.month),
                ('salary_rule_code', '=', 'LD1'),
            ]).mapped('leave_duration_amount'))

    def _compute_unpaid_leave_amount_deducted(self):
        for payslip in self:
            payslip.unpaid_leave_amount_deducted = sum(self.env['hr.leave.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('leave_month', '>=', payslip.date_from.month),
                ('leave_month', '<=', payslip.date_to.month),
                ('salary_rule_code', '=', 'LD2'),
            ]).mapped('leave_duration_amount'))

    def _compute_annual_leave_amount_deducted(self):
        for payslip in self:
            payslip.annual_leave_amount_deducted = sum(self.env['hr.leave.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('leave_month', '>=', payslip.date_from.month),
                ('leave_month', '<=', payslip.date_to.month),
                ('salary_rule_code', '=', 'LD3'),
            ]).mapped('leave_duration_amount'))

    def _compute_other_leave_amount_deducted(self):
        for payslip in self:
            payslip.other_leave_amount_deducted = sum(self.env['hr.leave.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('leave_month', '>=', payslip.date_from.month),
                ('leave_month', '<=', payslip.date_to.month),
                ('salary_rule_code', '=', 'LD4'),
            ]).mapped('leave_duration_amount'))

    def _compute_sick_leave_amount_deducted(self):
        for payslip in self:
            sick_leave_lines = self.env['hr.leave.line'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('leave_month', '>=', payslip.date_from.month),
                ('leave_month', '<=', payslip.date_to.month),
                ('salary_rule_code', '=', 'LD5'),
            ])
            payslip.sick_leave_amount_deducted = sum(sick_leave_lines.hr_leave_line_part_ids.mapped('total_deduction'))