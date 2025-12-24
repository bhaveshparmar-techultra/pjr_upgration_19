# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
import calendar


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    expiry_notification_days = fields.Integer(string="Work Expiry Notification Days")
    visa_expiry_notification_days = fields.Integer(string="Visa Expiry Notification Days")
    expiry_notification_email = fields.Char(string="Expiry Notification Email")
    overtime_calculation = fields.Boolean(
        related='company_id.overtime_calculation',
        string="Overtime Calculation",
        store=True,
    )
    monthly_working_day = fields.Float(
        string="Monthly Working Days",
        compute="_compute_employee_salary_per_day_hours",
    )
    salary_per_days = fields.Float(
        string="Salary Per Days",
        compute="_compute_employee_salary_per_day_hours",
    )
    salary_per_hours = fields.Float(
        string="Salary Per Hours",
        compute="_compute_employee_salary_per_day_hours",
    )
    hr_leave_employee_policy_ids = fields.One2many(
        'hr.leave.employee.policy',
        'employee_id',
        string='Leave Policies',
    )
    has_overtime = fields.Boolean(string="Has Overtime", default=False)
    has_delay = fields.Boolean(string="Has Delay", default=False)

    def generete_sick_leave_policies(self):
        for employee in self:
            if not employee.hr_leave_employee_policy_ids:
                self.env['hr.leave.employee.policy'].create([
                    {
                        'employee_id': employee.id,
                        'day_from': 0,
                        'day_to': 15,
                        'deduction_base': 'salary_per_day',
                        'deduction_rate': 0.0,
                    },
                    {
                        'employee_id': employee.id,
                        'day_from': 16,
                        'day_to': 26,
                        'deduction_base': 'salary_per_day',
                        'deduction_rate': 0.25,
                    },
                    {
                        'employee_id': employee.id,
                        'day_from': 27,
                        'day_to': 37,
                        'deduction_base': 'salary_per_day',
                        'deduction_rate': 0.5,
                    },
                    {
                        'employee_id': employee.id,
                        'day_from': 38,
                        'day_to': 48,
                        'deduction_base': 'salary_per_day',
                        'deduction_rate': 0.75,
                    },
                    {
                        'employee_id': employee.id,
                        'day_from': 49,
                        'day_to': 10000,
                        'deduction_base': 'salary_per_day',
                        'deduction_rate': 1.0,
                    },
                ])

    def _compute_employee_salary_per_day_hours(self):
        for employee in self:
            today = datetime.today()
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
            friday_count = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() == 4:
                    friday_count += 1
                current_date += timedelta(days=1)
            employee.monthly_working_day = last_day - friday_count
            wage = employee.version_id.wage if employee.version_id else 0
            hours_per_day = employee.resource_calendar_id.hours_per_day or 8
            employee.salary_per_days = wage / employee.monthly_working_day if employee.monthly_working_day else 0
            employee.salary_per_hours = employee.salary_per_days / hours_per_day if hours_per_day else 0

    def _cron_work_permit_expiry_notification(self):
        if self.overtime_calculation:
            today_date = date.today()
            employee_ids = self.search([])
            for employee in employee_ids:
                if employee.work_permit_expiration_date and (
                    employee.work_permit_expiration_date -
                    timedelta(days=employee.expiry_notification_days)) == today_date:
                    mail_template = self.env.ref('hr_custom.mail_template_work_permit_expiry_notification')
                    email_to = str(employee.expiry_notification_email) + ', ' + str(employee.work_email)
                    email_values = {
                        'email_from': (', '.join(str(a.email) for a in self.env.user)),
                        'email_to': email_to,
                    }
                    mail_template.send_mail(self.id, force_send=True, email_values=email_values)
                if employee.visa_expire and (employee.visa_expire - timedelta(
                    days=employee.visa_expiry_notification_days)) == today_date:
                    mail_template = self.env.ref('hr_custom.mail_template_visa_expiry_notification')
                    email_to = str(employee.expiry_notification_email) + ', ' + str(employee.work_email)
                    email_values = {
                        'email_from': (', '.join(str(a.email) for a in self.env.user)),
                        'email_to': email_to,
                    }
                    mail_template.send_mail(self.id, force_send=True, email_values=email_values)

    def reset_employee_sick_leave_ploicies(self):
        employee_ids = self.search([])
        for employee in employee_ids:
            employee.hr_leave_employee_policy_ids.unlink()
            employee.generete_sick_leave_policies()