import base64
from datetime import date
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPayslipReports(TransactionCase):
    """Test cases for payslip report abstract models"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

        # Create department
        cls.department = cls.env['hr.department'].create({
            'name': 'Report Test Department',
            'company_id': cls.company.id,
        })

        # Create employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Report Test Employee',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
        })

        # Test image for company logo
        cls.test_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        cls.company_image = cls.env['res.company.image'].create({
            'name': 'Test Report Logo',
            'image': cls.test_image,
            'company_id': cls.company.id,
        })


@tagged('post_install', '-at_install')
class TestHrPayslipReport(TransactionCase):
    """Test cases for report.hr_extra_report.hr_payslip_report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['report.hr_extra_report.hr_payslip_report']

    def test_01_report_model_exists(self):
        """Test that the hr_payslip_report abstract model exists"""
        self.assertTrue(
            'report.hr_extra_report.hr_payslip_report' in self.env,
            "hr_payslip_report model should exist"
        )

    def test_02_report_has_prepare_method(self):
        """Test that report has _prepare_report_data method"""
        self.assertTrue(
            hasattr(self.report_model, '_prepare_report_data'),
            "Report should have _prepare_report_data method"
        )

    def test_03_prepare_report_data_with_empty_range(self):
        """Test _prepare_report_data with date range that has no payslips"""
        data = {
            'date_from': '2020-01-01',
            'date_to': '2020-01-31',
        }
        result = self.report_model._prepare_report_data([], data)
        self.assertIsInstance(result, list)


@tagged('post_install', '-at_install')
class TestHrPayslipReportXlsx(TransactionCase):
    """Test cases for report.hr_extra_report.hr_payslip_report_xlsx"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.test_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        cls.company_image = cls.env['res.company.image'].create({
            'name': 'XLSX Test Logo',
            'image': cls.test_image,
            'company_id': cls.company.id,
        })

    def test_01_xlsx_report_model_exists(self):
        """Test that the hr_payslip_report_xlsx model exists"""
        self.assertTrue(
            'report.hr_extra_report.hr_payslip_report_xlsx' in self.env,
            "hr_payslip_report_xlsx model should exist"
        )

    def test_02_xlsx_report_inherits_abstract(self):
        """Test that xlsx report inherits from report.report_xlsx_dynamic.abstract"""
        model = self.env['report.hr_extra_report.hr_payslip_report_xlsx']
        self.assertIn(
            'report.report_xlsx_dynamic.abstract',
            model._inherit if isinstance(model._inherit, list) else [model._inherit],
            "Should inherit from xlsx abstract report"
        )

    def test_03_xlsx_report_has_generate_method(self):
        """Test that xlsx report has generate_xlsx_report method"""
        model = self.env['report.hr_extra_report.hr_payslip_report_xlsx']
        self.assertTrue(
            hasattr(model, 'generate_xlsx_report'),
            "Report should have generate_xlsx_report method"
        )


@tagged('post_install', '-at_install')
class TestHrPayslipComponentReport(TransactionCase):
    """Test cases for report.hr_extra_report.hr_payslip_component_report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['report.hr_extra_report.hr_payslip_component_report']

    def test_01_component_report_model_exists(self):
        """Test that the hr_payslip_component_report model exists"""
        self.assertTrue(
            'report.hr_extra_report.hr_payslip_component_report' in self.env,
            "hr_payslip_component_report model should exist"
        )

    def test_02_component_report_has_get_report_body(self):
        """Test that component report has get_report_body method"""
        self.assertTrue(
            hasattr(self.report_model, 'get_report_body'),
            "Report should have get_report_body method"
        )

    def test_03_component_report_has_get_report_header(self):
        """Test that component report has get_report_header method"""
        self.assertTrue(
            hasattr(self.report_model, 'get_report_header'),
            "Report should have get_report_header method"
        )

    def test_04_get_report_header_returns_list(self):
        """Test that get_report_header returns a list of column names"""
        header = self.report_model.get_report_header()
        self.assertIsInstance(header, list)
        self.assertTrue(len(header) > 0, "Header should have columns")

    def test_05_get_report_header_contains_expected_columns(self):
        """Test that header contains expected column names"""
        header = self.report_model.get_report_header()
        expected_columns = [
            'Date', 'Employee', 'Basic Wage', 'Work Permit',
            'Cash Allowance', 'Bank Transfer'
        ]
        for col in expected_columns:
            self.assertIn(col, header, f"Header should contain '{col}' column")

    def test_06_get_report_body_with_date_range(self):
        """Test get_report_body with a date range"""
        form_data = {
            'date_from': '2020-01-01',
            'date_to': '2020-12-31',
        }
        result = self.report_model.get_report_body(form_data)
        self.assertIsInstance(result, list)

    def test_07_component_report_inherits_abstract(self):
        """Test that component report inherits from xlsx abstract"""
        model = self.env['report.hr_extra_report.hr_payslip_component_report']
        self.assertIn(
            'report.report_xlsx_dynamic.abstract',
            model._inherit if isinstance(model._inherit, list) else [model._inherit],
            "Should inherit from xlsx abstract report"
        )
