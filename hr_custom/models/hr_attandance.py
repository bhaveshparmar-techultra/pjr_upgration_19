import toolz as T
import toolz.curried as TC
from odoo import models, fields, api
import pytz
from datetime import datetime, date
import calendar


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        copy=False,
        store=True,
        readonly=False,
        default=lambda self: self.env.company,
    )
    over_time = fields.Float(
        string='Over Time',
        compute='_compute_employee_hours',
        store=True,
        readonly=True,
    )
    missing_hours = fields.Float(
        string='Missing Hours',
        compute='_compute_employee_hours',
        store=True,
        readonly=True,
    )
    overtime_calculation = fields.Boolean(
        related='company_id.overtime_calculation',
        string="Overtime Calculation",
        store=True,
    )
    overtime_amount = fields.Float(
        string='Overtime Amount',
        compute='_compute_overtime_amount',
    )

    delay_amount = fields.Float(
        string='Delay Amount',
        compute='_compute_delay_amount',
    )

    @api.depends('check_in', 'check_out')
    def _compute_employee_hours(self):
        for attendance in self:
            attendance.over_time = 0
            attendance.missing_hours = 0
            if attendance.overtime_calculation and attendance.check_out and attendance.check_in:
                start_date = pytz.timezone('utc').localize(
                    datetime.combine(
                        attendance.check_in,
                        datetime.min.time(),
                    ),)
                end_date = pytz.timezone('utc').localize(
                    datetime.combine(
                        attendance.check_out,
                        datetime.max.time(),
                    ),)
                working_hours_per_attendace_day = T.pipe(
                    attendance.employee_id.resource_calendar_id._work_intervals_batch(
                        start_date,
                        end_date,
                        resources=attendance.employee_id.resource_id,
                    ),
                    TC.get(attendance.employee_id.resource_id.id),
                    TC.map(lambda interval: (interval[1] - interval[0]).total_seconds() / 3600.0),
                    sum,
                )
                delta = attendance.check_out - attendance.check_in
                worked_hours = (delta.total_seconds() / 3600.0)
                # case 1 : if there is a working hours per attendance day
                # it means that it's a normal working day
                if working_hours_per_attendace_day > 0:
                    # case 1.1 : if the worked hours > working_hours_per_attendace_day
                    # it means that the employee worked overtime
                    if worked_hours > working_hours_per_attendace_day:
                        attendance.over_time = worked_hours - working_hours_per_attendace_day
                    # case 1.2 : if the worked hours < working_hours_per_attendace_day
                    # it means that the employee was late or left early
                    else:
                        attendance.missing_hours = working_hours_per_attendace_day - worked_hours
                # case 2 : if there is no working hours per attendance day
                # it means that it's a day off or a public holiday or a weekend
                # so the employee worked overtime
                elif working_hours_per_attendace_day == 0:
                    attendance.over_time = worked_hours

    def compute_month_working_days(self, day, employee):
        start_date = pytz.timezone('utc').localize(
            datetime.combine(
                date(day.year, day.month, 1),
                datetime.min.time(),
            ),)
        end_date = pytz.timezone('utc').localize(
            datetime.combine(
                date(day.year, day.month,
                     calendar.monthrange(day.year, day.month)[1]),
                datetime.max.time(),
            ),)

        month_working_days = T.pipe(
            employee.resource_calendar_id._work_intervals_batch(
                start_date,
                end_date,
                resources=employee.resource_id,
                compute_leaves=False,
            ),
            TC.keyfilter(TC.identity),  # to remove falsey keys
            lambda resouce: resouce.values(),
            TC.concat,
            TC.groupby(lambda interval: interval[0].date()),
            TC.count)
        return month_working_days

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_overtime_amount(self):
        for attendance in self:
            if attendance.over_time:
                attendace_day = attendance.check_in.date()
                month_working_days = self.compute_month_working_days(attendace_day, attendance.employee_id)
                hours_per_day = attendance.employee_id.resource_calendar_id.hours_per_day or 8
                salary_per_hours = attendance.employee_id.version_id.wage / month_working_days / hours_per_day if month_working_days and hours_per_day else 0

                # [Regular Overtime] calculate the overtime amount based on the regular overtime rate
                attendance.overtime_amount = attendance.over_time * salary_per_hours * self.env.company.regular_overtime_rate

                # [Public Holiday Overtime] check if the day is a public holiday
                public_holiday = self.env['resource.calendar.leaves'].search([
                    ('leave_date_from', '<=', attendace_day),
                    ('leave_date_to', '>=', attendace_day),
                    ('resource_id', '=', False),
                ])
                if public_holiday:
                    attendance.overtime_amount = attendance.over_time * salary_per_hours * self.env.company.public_holiday_overtime_rate
                    continue

                # [Weekend overtime ]check if the day is a weekend according to the employee's calendar
                working_days = T.pipe(
                    attendance.employee_id.resource_calendar_id.attendance_ids,
                    TC.map(TC.get('dayofweek')),
                    TC.unique,
                    TC.map(int),
                    list,
                )
                if attendace_day.weekday() not in working_days:
                    attendance.overtime_amount = attendance.over_time * salary_per_hours * self.env.company.weekend_overtime_rate
                    continue
            else:
                attendance.overtime_amount = 0

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_delay_amount(self):
        for attendance in self:
            if attendance.missing_hours:
                attendace_day = attendance.check_in.date()
                month_working_days = self.compute_month_working_days(attendace_day, attendance.employee_id)
                hours_per_day = attendance.employee_id.resource_calendar_id.hours_per_day or 8
                salary_per_hours = attendance.employee_id.version_id.wage / month_working_days / hours_per_day if month_working_days and hours_per_day else 0

                # [Delay Amount] calculate the delay amount based on the missing hours
                attendance.delay_amount = attendance.missing_hours * salary_per_hours
            else:
                attendance.delay_amount = 0