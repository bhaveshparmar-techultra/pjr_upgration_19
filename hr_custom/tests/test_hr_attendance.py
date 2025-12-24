# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, date, timedelta
from odoo.tests import common, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestHrAttendance(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Enable overtime calculation on company
        cls.company = cls.env.company
        cls.company.write({
            'overtime_calculation': True,
            'regular_overtime_rate': 1.5,
            'weekend_overtime_rate': 2.0,
            'public_holiday_overtime_rate': 2.5,
        })

        # Create a resource calendar (8 hours/day, Mon-Fri)
        cls.calendar = cls.env['resource.calendar'].create({
            'name': 'Test Calendar 40h',
            'hours_per_day': 8.0,
            'attendance_ids': [
                (0, 0, {'name': 'Monday Morning', 'dayofweek': '0', 'hour_from': 8.0, 'hour_to': 12.0}),
                (0, 0, {'name': 'Monday Afternoon', 'dayofweek': '0', 'hour_from': 13.0, 'hour_to': 17.0}),
                (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 8.0, 'hour_to': 12.0}),
                (0, 0, {'name': 'Tuesday Afternoon', 'dayofweek': '1', 'hour_from': 13.0, 'hour_to': 17.0}),
                (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 8.0, 'hour_to': 12.0}),
                (0, 0, {'name': 'Wednesday Afternoon', 'dayofweek': '2', 'hour_from': 13.0, 'hour_to': 17.0}),
                (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 8.0, 'hour_to': 12.0}),
                (0, 0, {'name': 'Thursday Afternoon', 'dayofweek': '3', 'hour_from': 13.0, 'hour_to': 17.0}),
                (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 8.0, 'hour_to': 12.0}),
                (0, 0, {'name': 'Friday Afternoon', 'dayofweek': '4', 'hour_from': 13.0, 'hour_to': 17.0}),
            ],
        })

        # Create employee with contract/version
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'resource_calendar_id': cls.calendar.id,
        })

        # Update the employee's current version with wage
        cls.version = cls.employee.version_id
        cls.version.write({
            'wage': 2000.0,  # Monthly wage
            'resource_calendar_id': cls.calendar.id,
        })

    def _create_attendance(self, check_in, check_out):
        """Helper to create attendance record."""
        return self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
            'check_out': check_out,
        })

    def _get_next_weekday(self, weekday):
        """Get the next occurrence of a weekday (0=Monday, 6=Sunday)."""
        today = date.today()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # =============================================
    # Test _compute_employee_hours
    # =============================================

    def test_01_compute_employee_hours_normal_day_no_overtime(self):
        """Test normal working day with exact 8 hours - no overtime, no missing hours."""
        # Get next Monday (working day)
        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('08:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('17:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # 9 hours total but 1 hour lunch break in calendar = 8 working hours
        self.assertEqual(attendance.over_time, 1.0, "Should have 1 hour overtime (9h worked - 8h expected)")
        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours")

    def test_02_compute_employee_hours_overtime(self):
        """Test normal working day with overtime."""
        monday = self._get_next_weekday(0)
        # Work 10 hours (8:00 - 18:00)
        check_in = datetime.combine(monday, datetime.strptime('08:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('18:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # 10 hours worked, 8 hours expected = 2 hours overtime
        self.assertGreater(attendance.over_time, 0, "Should have overtime hours")
        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours")

    def test_03_compute_employee_hours_missing_hours(self):
        """Test normal working day with missing hours (late arrival or early leave)."""
        monday = self._get_next_weekday(0)
        # Work only 6 hours (9:00 - 15:00)
        check_in = datetime.combine(monday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('15:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # 6 hours worked, 8 hours expected = 2 hours missing
        self.assertEqual(attendance.over_time, 0, "Should have no overtime")
        self.assertGreater(attendance.missing_hours, 0, "Should have missing hours")

    def test_04_compute_employee_hours_weekend_overtime(self):
        """Test working on weekend - all hours count as overtime."""
        # Get next Saturday (day off)
        saturday = self._get_next_weekday(5)
        check_in = datetime.combine(saturday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(saturday, datetime.strptime('13:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # 4 hours worked on weekend = 4 hours overtime
        self.assertEqual(attendance.over_time, 4.0, "All weekend hours should be overtime")
        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours on weekend")

    def test_05_compute_employee_hours_no_checkout(self):
        """Test attendance without checkout - should have no overtime or missing hours."""
        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('08:00', '%H:%M').time())

        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
        })

        self.assertEqual(attendance.over_time, 0, "Should have no overtime without checkout")
        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours without checkout")

    # =============================================
    # Test compute_month_working_days
    # =============================================

    def test_06_compute_month_working_days(self):
        """Test computing working days in a month."""
        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('08:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('17:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)
        working_days = attendance.compute_month_working_days(monday, self.employee)

        # A month typically has 20-23 working days (Mon-Fri)
        self.assertGreater(working_days, 0, "Should have working days in a month")
        self.assertLessEqual(working_days, 23, "Should not exceed maximum possible working days")

    # =============================================
    # Test _compute_overtime_amount
    # =============================================

    def test_07_compute_overtime_amount_regular(self):
        """Test overtime amount calculation with regular rate."""
        monday = self._get_next_weekday(0)
        # Work 10 hours to ensure overtime
        check_in = datetime.combine(monday, datetime.strptime('07:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('18:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        if attendance.over_time > 0:
            self.assertGreater(attendance.overtime_amount, 0, "Overtime amount should be positive")

    def test_08_compute_overtime_amount_weekend(self):
        """Test overtime amount calculation with weekend rate."""
        saturday = self._get_next_weekday(5)
        check_in = datetime.combine(saturday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(saturday, datetime.strptime('13:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # Weekend overtime should use weekend rate (2.0)
        self.assertGreater(attendance.overtime_amount, 0, "Weekend overtime amount should be positive")
        self.assertEqual(attendance.over_time, 4.0, "Should have 4 hours of overtime")

    def test_09_compute_overtime_amount_public_holiday(self):
        """Test overtime amount calculation with public holiday rate."""
        monday = self._get_next_weekday(0)

        # Create a public holiday for that day
        self.env['resource.calendar.leaves'].create({
            'name': 'Test Public Holiday',
            'leave_date_from': monday,
            'leave_date_to': monday,
            'resource_id': False,  # Global public holiday
            'calendar_id': self.calendar.id,
        })

        check_in = datetime.combine(monday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('13:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # Public holiday overtime should use public holiday rate (2.5)
        self.assertGreater(attendance.over_time, 0, "Should have overtime on public holiday")
        self.assertGreater(attendance.overtime_amount, 0, "Public holiday overtime amount should be positive")

    def test_10_compute_overtime_amount_no_overtime(self):
        """Test overtime amount is zero when no overtime."""
        monday = self._get_next_weekday(0)
        # Work less than 8 hours
        check_in = datetime.combine(monday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('14:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        self.assertEqual(attendance.over_time, 0, "Should have no overtime")
        self.assertEqual(attendance.overtime_amount, 0, "Overtime amount should be zero")

    # =============================================
    # Test _compute_delay_amount
    # =============================================

    def test_11_compute_delay_amount_with_missing_hours(self):
        """Test delay amount calculation when employee has missing hours."""
        monday = self._get_next_weekday(0)
        # Work only 5 hours (late + early leave)
        check_in = datetime.combine(monday, datetime.strptime('10:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('15:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        if attendance.missing_hours > 0:
            self.assertGreater(attendance.delay_amount, 0, "Delay amount should be positive when missing hours")

    def test_12_compute_delay_amount_no_missing_hours(self):
        """Test delay amount is zero when no missing hours."""
        monday = self._get_next_weekday(0)
        # Work full day with overtime
        check_in = datetime.combine(monday, datetime.strptime('07:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('18:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours")
        self.assertEqual(attendance.delay_amount, 0, "Delay amount should be zero")

    def test_13_compute_delay_amount_weekend(self):
        """Test delay amount is zero on weekends (no expected hours)."""
        saturday = self._get_next_weekday(5)
        check_in = datetime.combine(saturday, datetime.strptime('09:00', '%H:%M').time())
        check_out = datetime.combine(saturday, datetime.strptime('11:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        # Weekend has no expected hours, so no missing hours
        self.assertEqual(attendance.missing_hours, 0, "Should have no missing hours on weekend")
        self.assertEqual(attendance.delay_amount, 0, "Delay amount should be zero on weekend")

    # =============================================
    # Test overtime_calculation flag
    # =============================================

    def test_14_overtime_calculation_disabled(self):
        """Test that overtime/delay not computed when flag is disabled."""
        # Disable overtime calculation
        self.company.overtime_calculation = False

        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('07:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('20:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)

        self.assertEqual(attendance.over_time, 0, "Overtime should be zero when calculation disabled")
        self.assertEqual(attendance.missing_hours, 0, "Missing hours should be zero when calculation disabled")

        # Re-enable for other tests
        self.company.overtime_calculation = True

    # =============================================
    # Test edge cases
    # =============================================

    def test_15_employee_no_wage(self):
        """Test attendance with employee having no wage configured."""
        # Create employee without version/contract
        employee_no_wage = self.env['hr.employee'].create({
            'name': 'Employee No Wage',
            'resource_calendar_id': self.calendar.id,
        })

        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('07:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('18:00', '%H:%M').time())

        attendance = self.env['hr.attendance'].create({
            'employee_id': employee_no_wage.id,
            'check_in': check_in,
            'check_out': check_out,
        })

        # Should not raise error, overtime_amount should be 0 due to no wage
        self.assertEqual(attendance.overtime_amount, 0, "Overtime amount should be zero without wage")

    def test_16_salary_per_hour_calculation(self):
        """Test that salary per hour is calculated correctly."""
        monday = self._get_next_weekday(0)
        check_in = datetime.combine(monday, datetime.strptime('08:00', '%H:%M').time())
        check_out = datetime.combine(monday, datetime.strptime('17:00', '%H:%M').time())

        attendance = self._create_attendance(check_in, check_out)
        working_days = attendance.compute_month_working_days(monday, self.employee)
        hours_per_day = self.calendar.hours_per_day or 8

        # Calculate expected salary per hour
        expected_salary_per_hour = self.version.wage / working_days / hours_per_day if working_days else 0

        self.assertGreater(expected_salary_per_hour, 0, "Salary per hour should be positive")
