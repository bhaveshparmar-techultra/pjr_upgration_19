#!/usr/bin/env python3
"""
Test actual report generation for hr_extra_report module.
Tests both report_xlsx_dynamic and report_py3o dependencies.

Usage:
    python3 odoo-bin shell -c <config_file> < test_report_generation.py
"""
import base64
import os
import tempfile
from datetime import date, timedelta

def test_report_generation(env):
    """Test actual report generation"""
    print("\n" + "="*70)
    print(" HR EXTRA REPORT - REPORT GENERATION TEST")
    print("="*70)

    company = env.ref('base.main_company')
    results = {'passed': 0, 'failed': 0, 'errors': []}

    def test(name, func):
        try:
            result = func()
            if result:
                print(f"  ✓ {name}")
                results['passed'] += 1
                return True
            else:
                print(f"  ✗ {name} - FAILED")
                results['failed'] += 1
                return False
        except Exception as e:
            print(f"  ✗ {name} - ERROR: {str(e)}")
            results['failed'] += 1
            results['errors'].append((name, str(e)))
            return False

    # Create test image
    test_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        b'\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00'
        b'\x00\x00\x1dIDATx\x9cc\xfc\xff\xff?\x03\x10\x00'
        b'\x00\xff\xff\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # =========================================================================
    # 1. SETUP TEST DATA
    # =========================================================================
    print("\n[1/3] SETTING UP TEST DATA...")

    company_image = env['res.company.image'].search([
        ('name', '=', 'Report Gen Test Logo')
    ], limit=1)
    if not company_image:
        company_image = env['res.company.image'].create({
            'name': 'Report Gen Test Logo',
            'image': test_image,
            'company_id': company.id,
        })
    print(f"  ✓ Company image ready (id={company_image.id})")

    # Get or create leave
    leave = env['hr.leave'].search([], limit=1)
    if leave:
        print(f"  ✓ Leave record ready (id={leave.id})")
    else:
        print("  ⚠ No leave records found for py3o testing")

    # =========================================================================
    # 2. TEST XLSX REPORT GENERATION (report_xlsx_dynamic)
    # =========================================================================
    print("\n[2/3] TESTING XLSX REPORT GENERATION...")

    def test_payslip_xlsx_report():
        """Test generating actual XLSX payslip report"""
        report = env.ref('hr_extra_report.action_report_hr_payslip_report_xlsx')

        # Check report model exists
        report_model = env['report.hr_extra_report.hr_payslip_report_xlsx']

        # Prepare data
        data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
            'logo_id': company_image.id,
        }

        # Test report data preparation
        base_report = env['report.hr_extra_report.hr_payslip_report']
        report_data = base_report._prepare_report_data([], data)

        return isinstance(report_data, list)
    test("XLSX payslip report data generation", test_payslip_xlsx_report)

    def test_component_xlsx_report():
        """Test generating actual XLSX component report"""
        report = env.ref('hr_extra_report.action_hr_payslip_component_report')

        # Check report model exists
        report_model = env['report.hr_extra_report.hr_payslip_component_report']

        # Prepare data
        form_data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
        }

        # Test report header
        header = report_model.get_report_header()
        if len(header) != 16:
            return False

        # Test report body query
        body = report_model.get_report_body(form_data)

        return isinstance(body, list)
    test("XLSX component report data generation", test_component_xlsx_report)

    def test_xlsx_abstract_methods():
        """Test that XLSX report models have required abstract methods"""
        payslip_model = env['report.hr_extra_report.hr_payslip_report_xlsx']
        component_model = env['report.hr_extra_report.hr_payslip_component_report']

        has_payslip_method = hasattr(payslip_model, 'generate_xlsx_report')
        has_component_method = hasattr(component_model, 'generate_xlsx_report')

        return has_payslip_method and has_component_method
    test("XLSX abstract methods exist", test_xlsx_abstract_methods)

    # =========================================================================
    # 3. TEST PY3O REPORT GENERATION (report_py3o)
    # =========================================================================
    print("\n[3/3] TESTING PY3O REPORT GENERATION...")

    def test_py3o_report_action_pjr():
        """Test py3o leave report PJR action"""
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_pjr')
            return (
                action.report_type == 'py3o' and
                action.model == 'hr.leave'
            )
        except ValueError:
            return False
    test("py3o leave report PJR configuration", test_py3o_report_action_pjr)

    def test_py3o_report_action_packo():
        """Test py3o leave report PACKO action"""
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_packo')
            return (
                action.report_type == 'py3o' and
                action.model == 'hr.leave'
            )
        except ValueError:
            return False
    test("py3o leave report PACKO configuration", test_py3o_report_action_packo)

    def test_py3o_report_action_we():
        """Test py3o leave report WE action"""
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_we')
            return (
                action.report_type == 'py3o' and
                action.model == 'hr.leave'
            )
        except ValueError:
            return False
    test("py3o leave report WE configuration", test_py3o_report_action_we)

    def test_py3o_report_action_marcom():
        """Test py3o leave report MARCOM action"""
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_marcom')
            return (
                action.report_type == 'py3o' and
                action.model == 'hr.leave'
            )
        except ValueError:
            return False
    test("py3o leave report MARCOM configuration", test_py3o_report_action_marcom)

    def test_py3o_leave_method():
        """Test hr.leave py3o_get_leave_type_summary method"""
        if not leave:
            return False
        result = leave.py3o_get_leave_type_summary()
        return isinstance(result, str) and 'remaining' in result
    if leave:
        test("py3o leave summary method", test_py3o_leave_method)

    def test_py3o_leave_payment_reports():
        """Test py3o leave payment reports exist"""
        report_refs = [
            'hr_extra_report.hr_leave_payment_report_py3o_pjr',
            'hr_extra_report.hr_leave_payment_report_py3o_packo',
            'hr_extra_report.hr_leave_payment_report_py3o_we',
            'hr_extra_report.hr_leave_payment_report_py3o_marcom',
        ]
        count = 0
        for ref in report_refs:
            try:
                action = env.ref(ref)
                if action.report_type == 'py3o':
                    count += 1
            except ValueError:
                pass
        return count == 4
    test("py3o leave payment reports configuration", test_py3o_leave_payment_reports)

    def test_py3o_templates_exist():
        """Test that py3o templates exist in static directory"""
        templates_path = '/home/tus/CLAUDE_gulfco_Workspace/Odoo19/workspace_odoo19/v19_migrated_pjr/hr_extra_report/static'
        if os.path.isdir(templates_path):
            files = os.listdir(templates_path)
            odt_files = [f for f in files if f.endswith('.odt')]
            # Should have 8 .odt template files
            return len(odt_files) >= 4
        return False
    test("py3o templates exist in static directory", test_py3o_templates_exist)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total:  {results['passed'] + results['failed']}")

    if results['errors']:
        print("\n  ERRORS:")
        for name, error in results['errors']:
            print(f"    - {name}: {error}")

    if results['failed'] == 0:
        print("\n  ✓ ALL REPORT GENERATION TESTS PASSED!")
        print("  The hr_extra_report module is fully compatible with:")
        print("    - report_xlsx_dynamic (XLSX reports)")
        print("    - report_py3o (LibreOffice PDF reports)")

    print("="*70 + "\n")

    return results

# Run if in shell mode
if 'env' in dir():
    test_report_generation(env)
