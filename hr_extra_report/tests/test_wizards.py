import base64
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestHrPayslipReportWizard(TransactionCase):
    """Test cases for hr.payslip.report.wizard"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

        # Create test image
        cls.test_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        cls.company_image = cls.env['res.company.image'].create({
            'name': 'Wizard Test Logo',
            'image': cls.test_image,
            'company_id': cls.company.id,
        })

    def test_01_wizard_model_exists(self):
        """Test that hr.payslip.report.wizard model exists"""
        self.assertTrue(
            'hr.payslip.report.wizard' in self.env,
            "hr.payslip.report.wizard model should exist"
        )

    def test_02_wizard_has_required_fields(self):
        """Test that wizard has all required fields"""
        wizard_model = self.env['hr.payslip.report.wizard']
        required_fields = ['date_from', 'date_to', 'logo_id']
        for field in required_fields:
            self.assertIn(field, wizard_model._fields,
                          f"Wizard should have '{field}' field")

    def test_03_wizard_create_with_valid_data(self):
        """Test creating wizard with valid data"""
        wizard = self.env['hr.payslip.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
            'logo_id': self.company_image.id,
        })
        self.assertTrue(wizard.id)
        self.assertEqual(wizard.logo_id, self.company_image)

    def test_04_wizard_date_from_required(self):
        """Test that date_from is required"""
        with self.assertRaises(Exception):
            self.env['hr.payslip.report.wizard'].create({
                'date_to': date.today(),
                'logo_id': self.company_image.id,
            })

    def test_05_wizard_date_to_required(self):
        """Test that date_to is required"""
        with self.assertRaises(Exception):
            self.env['hr.payslip.report.wizard'].create({
                'date_from': date.today(),
                'logo_id': self.company_image.id,
            })

    def test_06_wizard_logo_required(self):
        """Test that logo_id is required"""
        with self.assertRaises(Exception):
            self.env['hr.payslip.report.wizard'].create({
                'date_from': date.today() - timedelta(days=30),
                'date_to': date.today(),
            })

    def test_07_wizard_has_print_method(self):
        """Test that wizard has print_salary_receipt_report method"""
        wizard_model = self.env['hr.payslip.report.wizard']
        self.assertTrue(
            hasattr(wizard_model, 'print_salary_receipt_report'),
            "Wizard should have print_salary_receipt_report method"
        )

    def test_08_wizard_logo_image_related_field(self):
        """Test that logo_image is related to logo_id.image"""
        wizard = self.env['hr.payslip.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
            'logo_id': self.company_image.id,
        })
        self.assertEqual(wizard.logo_image, self.company_image.image)

    def test_09_wizard_print_returns_action(self):
        """Test that print method returns a report action"""
        wizard = self.env['hr.payslip.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
            'logo_id': self.company_image.id,
        })
        action = wizard.print_salary_receipt_report()
        self.assertIsInstance(action, dict)
        self.assertIn('type', action)


@tagged('post_install', '-at_install')
class TestHrPayslipComponentReportWizard(TransactionCase):
    """Test cases for hr.payslip.component.report.wizard"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

    def test_01_component_wizard_model_exists(self):
        """Test that hr.payslip.component.report.wizard model exists"""
        self.assertTrue(
            'hr.payslip.component.report.wizard' in self.env,
            "hr.payslip.component.report.wizard model should exist"
        )

    def test_02_component_wizard_has_required_fields(self):
        """Test that component wizard has all required fields"""
        wizard_model = self.env['hr.payslip.component.report.wizard']
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            self.assertIn(field, wizard_model._fields,
                          f"Wizard should have '{field}' field")

    def test_03_component_wizard_create_with_valid_data(self):
        """Test creating component wizard with valid data"""
        wizard = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
        })
        self.assertTrue(wizard.id)

    def test_04_component_wizard_date_from_required(self):
        """Test that date_from is required"""
        with self.assertRaises(Exception):
            self.env['hr.payslip.component.report.wizard'].create({
                'date_to': date.today(),
            })

    def test_05_component_wizard_date_to_required(self):
        """Test that date_to is required"""
        with self.assertRaises(Exception):
            self.env['hr.payslip.component.report.wizard'].create({
                'date_from': date.today(),
            })

    def test_06_component_wizard_has_print_method(self):
        """Test that component wizard has print_component_report method"""
        wizard_model = self.env['hr.payslip.component.report.wizard']
        self.assertTrue(
            hasattr(wizard_model, 'print_component_report'),
            "Wizard should have print_component_report method"
        )

    def test_07_component_wizard_print_returns_action(self):
        """Test that print method returns a report action"""
        wizard = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
        })
        action = wizard.print_component_report()
        self.assertIsInstance(action, dict)
        self.assertIn('type', action)

    def test_08_component_wizard_date_range(self):
        """Test wizard with various date ranges"""
        # One month range
        wizard1 = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date(2024, 1, 1),
            'date_to': date(2024, 1, 31),
        })
        self.assertTrue(wizard1.id)

        # One year range
        wizard2 = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date(2024, 1, 1),
            'date_to': date(2024, 12, 31),
        })
        self.assertTrue(wizard2.id)

        # Single day
        wizard3 = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date(2024, 6, 15),
            'date_to': date(2024, 6, 15),
        })
        self.assertTrue(wizard3.id)
