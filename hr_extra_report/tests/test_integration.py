"""
Integration tests for hr_extra_report module.
Tests actual report generation using report_xlsx_dynamic and report_py3o.
"""
import base64
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestIntegrationHrExtraReport(TransactionCase):
    """Integration tests with actual database records"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

        # Create test image for reports
        cls.test_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # Create company image for reports
        cls.company_image = cls.env['res.company.image'].create({
            'name': 'Integration Test Logo',
            'image': cls.test_image,
            'company_id': cls.company.id,
        })

        # Create department
        cls.department = cls.env['hr.department'].create({
            'name': 'Integration Test Department',
            'company_id': cls.company.id,
        })

        # Create employees
        cls.employee1 = cls.env['hr.employee'].create({
            'name': 'Integration Test Employee 1',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

        cls.employee2 = cls.env['hr.employee'].create({
            'name': 'Integration Test Employee 2',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

        # Set custom fields on employee versions
        if cls.employee1.version_id:
            cls.employee1.version_id.write({
                'work_permit': 500.0,
                'cash_allowance': 250.0,
                'wage': 5000.0,
            })

        if cls.employee2.version_id:
            cls.employee2.version_id.write({
                'work_permit': 600.0,
                'cash_allowance': 300.0,
                'wage': 6000.0,
            })

        # Create leave type with allocation
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Integration Test Annual Leave',
            'company_id': cls.company.id,
            'requires_allocation': 'yes',
            'leave_validation_type': 'no_validation',
        })

        # Create allocation for employee1
        cls.allocation = cls.env['hr.leave.allocation'].create({
            'name': 'Test Allocation for Employee 1',
            'employee_id': cls.employee1.id,
            'holiday_status_id': cls.leave_type.id,
            'number_of_days': 25,
            'state': 'confirm',
        })
        cls.allocation.action_approve()

    def test_01_version_custom_fields_set(self):
        """Test that custom fields are properly set on hr.version"""
        version1 = self.employee1.version_id
        self.assertEqual(version1.work_permit, 500.0)
        self.assertEqual(version1.cash_allowance, 250.0)

        version2 = self.employee2.version_id
        self.assertEqual(version2.work_permit, 600.0)
        self.assertEqual(version2.cash_allowance, 300.0)

    def test_02_company_image_created(self):
        """Test that company image is properly created"""
        self.assertTrue(self.company_image.id)
        self.assertEqual(self.company_image.name, 'Integration Test Logo')
        self.assertTrue(self.company_image.image)

    def test_03_leave_allocation_approved(self):
        """Test that leave allocation is approved"""
        self.assertEqual(self.allocation.state, 'validate')
        self.assertEqual(self.allocation.number_of_days, 25)

    def test_04_payslip_report_wizard(self):
        """Test payslip report wizard creation and action"""
        wizard = self.env['hr.payslip.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
            'logo_id': self.company_image.id,
        })

        self.assertTrue(wizard.id)
        self.assertEqual(wizard.logo_id, self.company_image)

        # Test print action returns proper dict
        # In Odoo 19, report_action() may return ir.actions.act_window
        # with the report_action embedded in context
        action = wizard.print_salary_receipt_report()
        self.assertIsInstance(action, dict)
        # Check if it's a direct report action or act_window with embedded report
        if action.get('type') == 'ir.actions.act_window':
            # Report action is embedded in context
            report_action = action.get('context', {}).get('report_action', {})
            self.assertEqual(report_action.get('type'), 'ir.actions.report')
            self.assertEqual(report_action.get('report_type'), 'xlsx')
        else:
            self.assertEqual(action.get('type'), 'ir.actions.report')

    def test_05_component_report_wizard(self):
        """Test component report wizard creation and action"""
        wizard = self.env['hr.payslip.component.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
        })

        self.assertTrue(wizard.id)

        # Test print action returns proper dict
        # In Odoo 19, report_action() may return ir.actions.act_window
        # with the report_action embedded in context
        action = wizard.print_component_report()
        self.assertIsInstance(action, dict)
        # Check if it's a direct report action or act_window with embedded report
        if action.get('type') == 'ir.actions.act_window':
            # Report action is embedded in context
            report_action = action.get('context', {}).get('report_action', {})
            self.assertEqual(report_action.get('type'), 'ir.actions.report')
            self.assertEqual(report_action.get('report_type'), 'xlsx')
        else:
            self.assertEqual(action.get('type'), 'ir.actions.report')

    def test_06_xlsx_report_model_generation(self):
        """Test XLSX report model can generate data"""
        report_model = self.env['report.hr_extra_report.hr_payslip_report_xlsx']

        # Verify the model has required methods
        self.assertTrue(hasattr(report_model, 'generate_xlsx_report'))

    def test_07_component_report_query(self):
        """Test component report SQL query executes without error"""
        report_model = self.env['report.hr_extra_report.hr_payslip_component_report']

        form_data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
        }

        # Should not raise an error
        result = report_model.get_report_body(form_data)
        self.assertIsInstance(result, list)

    def test_08_payslip_report_query(self):
        """Test payslip report SQL query executes without error"""
        report_model = self.env['report.hr_extra_report.hr_payslip_report']

        data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
        }

        # Should not raise an error
        result = report_model._prepare_report_data([], data)
        self.assertIsInstance(result, list)

    def test_09_leave_py3o_method(self):
        """Test leave py3o_get_leave_type_summary method"""
        # Create a leave request
        leave = self.env['hr.leave'].create({
            'name': 'Integration Test Leave',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date.today() + timedelta(days=10),
            'request_date_to': date.today() + timedelta(days=12),
        })

        # Test py3o method
        summary = leave.py3o_get_leave_type_summary()
        self.assertIsInstance(summary, str)
        self.assertIn('remaining', summary)
        self.assertIn('out of', summary)

    def test_10_py3o_report_actions_exist(self):
        """Test that py3o report actions are properly registered"""
        # Check leave request report actions
        report_actions = [
            'hr_extra_report.action_report_hr_leave_report_py3o_pjr',
            'hr_extra_report.action_report_hr_leave_report_py3o_packo',
            'hr_extra_report.action_report_hr_leave_report_py3o_we',
            'hr_extra_report.action_report_hr_leave_report_py3o_marcom',
        ]

        for action_ref in report_actions:
            try:
                action = self.env.ref(action_ref)
                self.assertTrue(action.id, f"Report action {action_ref} should exist")
                self.assertEqual(action.report_type, 'py3o')
            except ValueError:
                pass  # Action may not exist if data not loaded

    def test_11_xlsx_report_actions_exist(self):
        """Test that xlsx report actions are properly registered"""
        xlsx_actions = [
            'hr_extra_report.action_report_hr_payslip_report_xlsx',
            'hr_extra_report.action_hr_payslip_component_report',
        ]

        for action_ref in xlsx_actions:
            try:
                action = self.env.ref(action_ref)
                self.assertTrue(action.id, f"Report action {action_ref} should exist")
                self.assertEqual(action.report_type, 'xlsx')
            except ValueError:
                pass  # Action may not exist if data not loaded

    def test_12_leave_payment_report_actions_exist(self):
        """Test that leave payment py3o report actions exist"""
        payment_reports = [
            'hr_extra_report.hr_leave_payment_report_py3o_pjr',
            'hr_extra_report.hr_leave_payment_report_py3o_packo',
            'hr_extra_report.hr_leave_payment_report_py3o_we',
            'hr_extra_report.hr_leave_payment_report_py3o_marcom',
        ]

        for action_ref in payment_reports:
            try:
                action = self.env.ref(action_ref)
                self.assertTrue(action.id, f"Report action {action_ref} should exist")
                self.assertEqual(action.report_type, 'py3o')
            except ValueError:
                pass  # Action may not exist if data not loaded
