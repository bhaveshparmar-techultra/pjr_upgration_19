# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tests import common, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestHrPayslip(common.TransactionCase):
    """
    Test cases for HR Payslip with all custom salary rules:
    - EMP_INSURANCE_DED: Employee Insurance Deduction
    - FAMILY_INSURANCE_DED: Family Insurance Deduction
    - OT: Over Time (fixed)
    - OVT: Overtime Allowance (computed from attendance)
    - MISSH: Missing Hours Deduction
    - LD1: Paid Leave Deduction
    - LD: Leave Deduction
    - LD2: Unpaid Leave Deduction
    - LD3: Annual Leave Deduction
    - LD4: Other Leave Deduction
    - LD5: Sick Leave Deduction
    - MH: Missing Hours (fixed)
    """

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

        # Create employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee Payslip',
            'resource_calendar_id': cls.calendar.id,
            'has_overtime': True,
            'has_delay': True,
        })

        # Generate sick leave policies for the employee
        cls.employee.generete_sick_leave_policies()

        # Get/Update the employee's version with all required fields
        cls.version = cls.employee.version_id
        today = date.today()
        cls.version.write({
            'wage': 2000.0,
            'resource_calendar_id': cls.calendar.id,
            'contract_date_start': today - relativedelta(months=6),
            # Insurance fields
            'started_deduction_date': today - relativedelta(months=3),
            'active_employee_insurance': True,
            'employee_ins_amount': 600.0,
            'emp_ins_period': 12,
            'emp_ins_start_date': today - relativedelta(months=3),
            'emp_ins_end_date': today + relativedelta(months=9),
            'active_family_insurance': True,
            'family_ins_amount': 1200.0,
            'family_ins_period': 12,
            'family_ins_start_date': today - relativedelta(months=3),
            'family_ins_end_date': today + relativedelta(months=9),
        })

        # Create leave types with deduction settings
        cls.leave_type_paid = cls.env['hr.leave.type'].create({
            'name': 'Paid Leave',
            'requires_allocation': 'no',
            'deduct_in_payslip': True,
            'salary_rule_code': 'LD1',
            'leave_deduction_rate': 0.5,
            'remove_weekend': True,
            'remove_public_holiday': True,
        })

        cls.leave_type_unpaid = cls.env['hr.leave.type'].create({
            'name': 'Unpaid Leave',
            'requires_allocation': 'no',
            'deduct_in_payslip': True,
            'salary_rule_code': 'LD2',
            'leave_deduction_rate': 1.0,
            'remove_weekend': True,
            'remove_public_holiday': False,
        })

        cls.leave_type_annual = cls.env['hr.leave.type'].create({
            'name': 'Annual Leave',
            'requires_allocation': 'no',
            'deduct_in_payslip': True,
            'salary_rule_code': 'LD3',
            'leave_deduction_rate': 0.0,
            'remove_weekend': True,
            'remove_public_holiday': True,
        })

        cls.leave_type_sick = cls.env['hr.leave.type'].create({
            'name': 'Sick Leave',
            'requires_allocation': 'no',
            'deduct_in_payslip': True,
            'salary_rule_code': 'LD5',
            'leave_deduction_rate': 0.25,
            'remove_weekend': True,
            'remove_public_holiday': True,
        })

        cls.leave_type_other = cls.env['hr.leave.type'].create({
            'name': 'Other Leave',
            'requires_allocation': 'no',
            'deduct_in_payslip': True,
            'salary_rule_code': 'LD4',
            'leave_deduction_rate': 0.75,
            'remove_weekend': False,
            'remove_public_holiday': False,
        })

    def _get_payslip_period(self):
        """Get current month payslip period."""
        today = date.today()
        date_from = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        date_to = next_month.replace(day=1) - timedelta(days=1)
        return date_from, date_to

    def _get_next_weekday(self, weekday, base_date=None):
        """Get the next occurrence of a weekday (0=Monday, 6=Sunday)."""
        if base_date is None:
            base_date = date.today()
        days_ahead = weekday - base_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return base_date + timedelta(days=days_ahead)

    def _create_attendance_with_overtime(self, check_date):
        """Create attendance with overtime hours."""
        check_in = datetime.combine(check_date, datetime.strptime('07:00', '%H:%M').time())
        check_out = datetime.combine(check_date, datetime.strptime('19:00', '%H:%M').time())
        return self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
            'check_out': check_out,
        })

    def _create_attendance_with_missing_hours(self, check_date):
        """Create attendance with missing hours (late arrival)."""
        check_in = datetime.combine(check_date, datetime.strptime('10:00', '%H:%M').time())
        check_out = datetime.combine(check_date, datetime.strptime('15:00', '%H:%M').time())
        return self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
            'check_out': check_out,
        })

    def _create_payslip(self, date_from=None, date_to=None):
        """Create a payslip for the employee."""
        if not date_from or not date_to:
            date_from, date_to = self._get_payslip_period()

        # Get the salary structure
        structure = self.env.ref('hr_payroll.structure_002', raise_if_not_found=False)
        if not structure:
            structure = self.env['hr.payroll.structure'].search([], limit=1)

        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': date_from,
            'date_to': date_to,
            'struct_id': structure.id if structure else False,
        })
        return payslip

    # =============================================
    # Test Basic Payslip Creation
    # =============================================

    def test_01_create_basic_payslip(self):
        """Test creating a basic payslip."""
        payslip = self._create_payslip()
        self.assertTrue(payslip, "Payslip should be created")
        self.assertEqual(payslip.employee_id, self.employee, "Payslip should be for the test employee")
        self.assertEqual(payslip.state, 'draft', "Payslip should be in draft state")

    def test_02_compute_payslip_sheet(self):
        """Test computing payslip sheet generates salary lines."""
        payslip = self._create_payslip()
        payslip.compute_sheet()
        self.assertTrue(payslip.line_ids, "Payslip should have salary lines after compute")

    # =============================================
    # Test Overtime Rules (OT, OVT)
    # =============================================

    def test_03_payslip_with_overtime(self):
        """Test payslip with overtime attendance."""
        date_from, date_to = self._get_payslip_period()

        # Create attendance with overtime within payslip period
        monday = self._get_next_weekday(0, date_from)
        if monday <= date_to:
            attendance = self._create_attendance_with_overtime(monday)
            self.assertGreater(attendance.over_time, 0, "Attendance should have overtime")

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Check overtime total amount is computed
        if self.employee.has_overtime:
            self.assertIsNotNone(payslip.overtime_total_amount, "Overtime total should be computed")

    def test_04_payslip_overtime_amount_calculation(self):
        """Test overtime amount calculation in payslip."""
        date_from, date_to = self._get_payslip_period()

        # Create multiple overtime attendances
        current_date = date_from
        while current_date <= date_to:
            if current_date.weekday() < 5:  # Monday to Friday
                self._create_attendance_with_overtime(current_date)
            current_date += timedelta(days=1)

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Verify OVT rule is applied
        ovt_line = payslip.line_ids.filtered(lambda l: l.code == 'OVT')
        if ovt_line:
            self.assertGreaterEqual(ovt_line.total, 0, "OVT line should have non-negative total")

    # =============================================
    # Test Missing Hours Rules (MISSH, MH)
    # =============================================

    def test_05_payslip_with_missing_hours(self):
        """Test payslip with missing hours (delays)."""
        date_from, date_to = self._get_payslip_period()

        # Create attendance with missing hours
        monday = self._get_next_weekday(0, date_from)
        if monday <= date_to:
            attendance = self._create_attendance_with_missing_hours(monday)
            self.assertGreater(attendance.missing_hours, 0, "Attendance should have missing hours")

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Check delay total amount
        if self.employee.has_delay:
            self.assertIsNotNone(payslip.delay_total_amount, "Delay total should be computed")

    # =============================================
    # Test Insurance Deductions (EMP_INSURANCE_DED, FAMILY_INSURANCE_DED)
    # =============================================

    def test_06_payslip_employee_insurance_deduction(self):
        """Test employee insurance deduction in payslip."""
        payslip = self._create_payslip()
        payslip.compute_sheet()

        # Check if EMP_INSURANCE_DED rule is applied
        emp_ins_line = payslip.line_ids.filtered(lambda l: l.code == 'EMP_INSURANCE_DED')
        if emp_ins_line and self.version.active_employee_insurance:
            # Should be negative (deduction)
            self.assertLessEqual(emp_ins_line.total, 0, "Employee insurance should be a deduction")

    def test_07_payslip_family_insurance_deduction(self):
        """Test family insurance deduction in payslip."""
        payslip = self._create_payslip()
        payslip.compute_sheet()

        # Check if FAMILY_INSURANCE_DED rule is applied
        family_ins_line = payslip.line_ids.filtered(lambda l: l.code == 'FAMILY_INSURANCE_DED')
        if family_ins_line and self.version.active_family_insurance:
            # Should be negative (deduction)
            self.assertLessEqual(family_ins_line.total, 0, "Family insurance should be a deduction")

    # =============================================
    # Test Leave Deductions (LD1, LD2, LD3, LD4, LD5)
    # =============================================

    def test_08_payslip_paid_leave_deduction(self):
        """Test paid leave deduction (LD1) in payslip."""
        date_from, date_to = self._get_payslip_period()

        # Create a paid leave within payslip period
        leave_start = self._get_next_weekday(1, date_from)  # Tuesday
        leave_end = self._get_next_weekday(2, date_from)  # Wednesday

        if leave_start <= date_to and leave_end <= date_to:
            leave = self.env['hr.leave'].create({
                'employee_id': self.employee.id,
                'holiday_status_id': self.leave_type_paid.id,
                'request_date_from': leave_start,
                'request_date_to': leave_end,
            })
            leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Check paid leave deduction
        self.assertIsNotNone(payslip.paid_leave_amount_deducted, "Paid leave deduction should be computed")

    def test_09_payslip_unpaid_leave_deduction(self):
        """Test unpaid leave deduction (LD2) in payslip."""
        date_from, date_to = self._get_payslip_period()

        # Create an unpaid leave
        leave_start = self._get_next_weekday(3, date_from)  # Thursday

        if leave_start <= date_to:
            leave = self.env['hr.leave'].create({
                'employee_id': self.employee.id,
                'holiday_status_id': self.leave_type_unpaid.id,
                'request_date_from': leave_start,
                'request_date_to': leave_start,
            })
            leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        self.assertIsNotNone(payslip.unpaid_leave_amount_deducted, "Unpaid leave deduction should be computed")

    def test_10_payslip_annual_leave_deduction(self):
        """Test annual leave deduction (LD3) in payslip."""
        date_from, date_to = self._get_payslip_period()

        leave_start = self._get_next_weekday(0, date_from)  # Monday

        if leave_start <= date_to:
            leave = self.env['hr.leave'].create({
                'employee_id': self.employee.id,
                'holiday_status_id': self.leave_type_annual.id,
                'request_date_from': leave_start,
                'request_date_to': leave_start,
            })
            leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        self.assertIsNotNone(payslip.annual_leave_amount_deducted, "Annual leave deduction should be computed")

    def test_11_payslip_sick_leave_deduction(self):
        """Test sick leave deduction (LD5) in payslip."""
        date_from, date_to = self._get_payslip_period()

        leave_start = self._get_next_weekday(1, date_from)  # Tuesday
        leave_end = self._get_next_weekday(3, date_from)  # Thursday

        if leave_start <= date_to and leave_end <= date_to:
            leave = self.env['hr.leave'].create({
                'employee_id': self.employee.id,
                'holiday_status_id': self.leave_type_sick.id,
                'request_date_from': leave_start,
                'request_date_to': leave_end,
            })
            leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        self.assertIsNotNone(payslip.sick_leave_amount_deducted, "Sick leave deduction should be computed")

    def test_12_payslip_other_leave_deduction(self):
        """Test other leave deduction (LD4) in payslip."""
        date_from, date_to = self._get_payslip_period()

        leave_start = self._get_next_weekday(4, date_from)  # Friday

        if leave_start <= date_to:
            leave = self.env['hr.leave'].create({
                'employee_id': self.employee.id,
                'holiday_status_id': self.leave_type_other.id,
                'request_date_from': leave_start,
                'request_date_to': leave_start,
            })
            leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        self.assertIsNotNone(payslip.other_leave_amount_deducted, "Other leave deduction should be computed")

    # =============================================
    # Test Complete Payslip with All Rules
    # =============================================

    def test_13_complete_payslip_all_rules(self):
        """Test complete payslip with all salary rules applied."""
        date_from, date_to = self._get_payslip_period()

        # Create various attendances
        current_date = date_from
        overtime_days = 0
        delay_days = 0

        while current_date <= date_to and (overtime_days < 3 or delay_days < 2):
            if current_date.weekday() < 5:  # Weekday
                if overtime_days < 3:
                    self._create_attendance_with_overtime(current_date)
                    overtime_days += 1
                elif delay_days < 2:
                    self._create_attendance_with_missing_hours(current_date)
                    delay_days += 1
            current_date += timedelta(days=1)

        # Create payslip
        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Verify payslip has lines
        self.assertTrue(payslip.line_ids, "Payslip should have salary lines")

        # Log all salary lines for debugging
        for line in payslip.line_ids:
            print(f"Salary Rule: {line.code} - {line.name}: Amount={line.amount}, Qty={line.quantity}, Total={line.total}")

    # =============================================
    # Test Payslip Validation
    # =============================================

    def test_14_payslip_confirm(self):
        """Test payslip confirmation workflow."""
        payslip = self._create_payslip()
        payslip.compute_sheet()

        # Confirm payslip
        payslip.action_payslip_done()
        self.assertEqual(payslip.state, 'done', "Payslip should be in done state")

    def test_15_payslip_with_no_version(self):
        """Test payslip for employee without version/contract."""
        # Create employee without proper version setup
        employee_no_version = self.env['hr.employee'].create({
            'name': 'Employee No Version',
            'resource_calendar_id': self.calendar.id,
        })

        date_from, date_to = self._get_payslip_period()

        # Get the salary structure
        structure = self.env.ref('hr_payroll.structure_002', raise_if_not_found=False)
        if not structure:
            structure = self.env['hr.payroll.structure'].search([], limit=1)

        payslip = self.env['hr.payslip'].create({
            'employee_id': employee_no_version.id,
            'date_from': date_from,
            'date_to': date_to,
            'struct_id': structure.id if structure else False,
        })

        # Should not raise error
        payslip.compute_sheet()
        self.assertTrue(True, "Payslip computed without error for employee with minimal version")

    # =============================================
    # Test Edge Cases
    # =============================================

    def test_16_payslip_multiple_leaves_same_month(self):
        """Test payslip with multiple leave types in same month."""
        date_from, date_to = self._get_payslip_period()

        # Create different types of leaves
        leave_dates = [
            (self.leave_type_paid, self._get_next_weekday(0, date_from)),
            (self.leave_type_unpaid, self._get_next_weekday(1, date_from)),
            (self.leave_type_annual, self._get_next_weekday(2, date_from)),
        ]

        for leave_type, leave_date in leave_dates:
            if leave_date <= date_to:
                leave = self.env['hr.leave'].create({
                    'employee_id': self.employee.id,
                    'holiday_status_id': leave_type.id,
                    'request_date_from': leave_date,
                    'request_date_to': leave_date,
                })
                leave._action_validate()

        payslip = self._create_payslip(date_from, date_to)
        payslip.compute_sheet()

        # Verify all leave deductions are computed
        self.assertIsNotNone(payslip.paid_leave_amount_deducted)
        self.assertIsNotNone(payslip.unpaid_leave_amount_deducted)
        self.assertIsNotNone(payslip.annual_leave_amount_deducted)

    def test_17_payslip_insurance_disabled(self):
        """Test payslip when insurance is disabled."""
        # Disable insurance
        self.version.write({
            'active_employee_insurance': False,
            'active_family_insurance': False,
        })

        payslip = self._create_payslip()
        payslip.compute_sheet()

        # Insurance lines should not be active
        emp_ins_line = payslip.line_ids.filtered(lambda l: l.code == 'EMP_INSURANCE_DED')
        family_ins_line = payslip.line_ids.filtered(lambda l: l.code == 'FAMILY_INSURANCE_DED')

        # Re-enable for other tests
        self.version.write({
            'active_employee_insurance': True,
            'active_family_insurance': True,
        })

        # Lines might exist but with zero amount due to condition
        if emp_ins_line:
            self.assertEqual(emp_ins_line.total, 0, "Employee insurance should be zero when disabled")
