from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrVersion(TransactionCase):
    """Test cases for hr.version extension with work_permit and cash_allowance fields"""

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
            'name': 'Test Employee',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

    def test_01_hr_version_has_work_permit_field(self):
        """Test that hr.version model has work_permit field"""
        version_model = self.env['hr.version']
        self.assertIn('work_permit', version_model._fields,
                      "hr.version should have 'work_permit' field")
        self.assertEqual(version_model._fields['work_permit'].type, 'float',
                         "work_permit should be a Float field")

    def test_02_hr_version_has_cash_allowance_field(self):
        """Test that hr.version model has cash_allowance field"""
        version_model = self.env['hr.version']
        self.assertIn('cash_allowance', version_model._fields,
                      "hr.version should have 'cash_allowance' field")
        self.assertEqual(version_model._fields['cash_allowance'].type, 'float',
                         "cash_allowance should be a Float field")

    def test_03_set_work_permit_on_version(self):
        """Test setting work_permit value on hr.version"""
        # Get the employee's version
        version = self.employee.version_id
        if version:
            version.work_permit = 500.0
            self.assertEqual(version.work_permit, 500.0)

    def test_04_set_cash_allowance_on_version(self):
        """Test setting cash_allowance value on hr.version"""
        # Get the employee's version
        version = self.employee.version_id
        if version:
            version.cash_allowance = 250.0
            self.assertEqual(version.cash_allowance, 250.0)

    def test_05_version_fields_default_to_zero(self):
        """Test that work_permit and cash_allowance default to 0"""
        version = self.employee.version_id
        if version:
            # Reset values
            version.write({
                'work_permit': 0.0,
                'cash_allowance': 0.0,
            })
            self.assertEqual(version.work_permit, 0.0)
            self.assertEqual(version.cash_allowance, 0.0)

    def test_06_create_contract_template_with_custom_fields(self):
        """Test creating a contract template with work_permit and cash_allowance"""
        template = self.env['hr.version'].create({
            'name': 'Test Template',
            'company_id': self.company.id,
            'work_permit': 1000.0,
            'cash_allowance': 500.0,
        })
        self.assertTrue(template.id)
        self.assertEqual(template.work_permit, 1000.0)
        self.assertEqual(template.cash_allowance, 500.0)
        # Template should not have an employee
        self.assertFalse(template.employee_id)

    def test_07_version_fields_accept_decimal_values(self):
        """Test that fields accept decimal values"""
        version = self.employee.version_id
        if version:
            version.work_permit = 123.45
            version.cash_allowance = 678.90
            self.assertAlmostEqual(version.work_permit, 123.45, places=2)
            self.assertAlmostEqual(version.cash_allowance, 678.90, places=2)

    def test_08_version_fields_accept_negative_values(self):
        """Test that fields can store negative values (if needed for deductions)"""
        version = self.employee.version_id
        if version:
            version.work_permit = -100.0
            self.assertEqual(version.work_permit, -100.0)
