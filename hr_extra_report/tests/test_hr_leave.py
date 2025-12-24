from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrLeave(TransactionCase):
    """Test cases for hr.leave extension with py3o_get_leave_type_summary method"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

        # Create a department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department',
            'company_id': cls.company.id,
        })

        # Create an employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee Leave',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

        # Create a leave type
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Test Annual Leave',
            'company_id': cls.company.id,
            'requires_allocation': 'yes',
            'leave_validation_type': 'no_validation',
        })

        # Create an allocation for the employee
        cls.allocation = cls.env['hr.leave.allocation'].create({
            'name': 'Test Allocation',
            'employee_id': cls.employee.id,
            'holiday_status_id': cls.leave_type.id,
            'number_of_days': 20,
            'state': 'confirm',
        })
        # Approve allocation using action_approve (Odoo 19)
        cls.allocation.action_approve()

    def test_01_hr_leave_has_py3o_method(self):
        """Test that hr.leave has py3o_get_leave_type_summary method"""
        leave_model = self.env['hr.leave']
        self.assertTrue(
            hasattr(leave_model, 'py3o_get_leave_type_summary'),
            "hr.leave should have 'py3o_get_leave_type_summary' method"
        )

    def test_02_py3o_method_returns_string(self):
        """Test that py3o_get_leave_type_summary returns a string"""
        # Create a leave request
        leave = self.env['hr.leave'].create({
            'name': 'Test Leave',
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date.today(),
            'request_date_to': date.today() + timedelta(days=2),
        })

        result = leave.py3o_get_leave_type_summary()
        self.assertIsInstance(result, str, "Method should return a string")

    def test_03_py3o_method_contains_remaining_info(self):
        """Test that py3o_get_leave_type_summary contains remaining days info"""
        leave = self.env['hr.leave'].create({
            'name': 'Test Leave 2',
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date.today() + timedelta(days=10),
            'request_date_to': date.today() + timedelta(days=12),
        })

        result = leave.py3o_get_leave_type_summary()
        self.assertIn('remaining', result.lower(),
                      "Result should contain 'remaining' keyword")
        self.assertIn('out of', result.lower(),
                      "Result should contain 'out of' keyword")

    def test_04_py3o_method_format(self):
        """Test that py3o_get_leave_type_summary returns proper format"""
        leave = self.env['hr.leave'].create({
            'name': 'Test Leave 3',
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date.today() + timedelta(days=20),
            'request_date_to': date.today() + timedelta(days=21),
        })

        result = leave.py3o_get_leave_type_summary()
        # Should be in format "X remaining out of Y"
        parts = result.split()
        self.assertTrue(len(parts) >= 4, "Result should have at least 4 parts")

    def test_05_py3o_method_returns_correct_format(self):
        """Test py3o_get_leave_type_summary returns correctly formatted string"""
        leave = self.env['hr.leave'].create({
            'name': 'Format Test Leave',
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date.today() + timedelta(days=40),
            'request_date_to': date.today() + timedelta(days=41),
        })

        result = leave.py3o_get_leave_type_summary()
        # Verify the format contains numeric values
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0, "Result should not be empty")
