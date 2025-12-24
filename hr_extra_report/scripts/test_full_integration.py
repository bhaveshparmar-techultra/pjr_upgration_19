#!/usr/bin/env python3
"""
Full integration test script for hr_extra_report module.
Creates actual records and tests all report functionality.

Usage:
    python3 odoo-bin shell -c <config_file> < test_full_integration.py
"""
import base64
from datetime import date, timedelta

def run_integration_tests(env):
    """Run full integration tests"""
    print("\n" + "="*70)
    print(" HR EXTRA REPORT - FULL INTEGRATION TEST")
    print("="*70)

    company = env.ref('base.main_company')
    results = {'passed': 0, 'failed': 0, 'errors': []}

    def test(name, func):
        try:
            result = func()
            if result:
                print(f"  ✓ {name}")
                results['passed'] += 1
            else:
                print(f"  ✗ {name} - FAILED")
                results['failed'] += 1
        except Exception as e:
            print(f"  ✗ {name} - ERROR: {str(e)}")
            results['failed'] += 1
            results['errors'].append((name, str(e)))

    # =========================================================================
    # 1. CREATE TEST DATA
    # =========================================================================
    print("\n[1/6] CREATING TEST DATA...")

    # Create test image
    test_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        b'\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00'
        b'\x00\x00\x1dIDATx\x9cc\xfc\xff\xff?\x03\x10\x00'
        b'\x00\xff\xff\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # Create company image
    def create_company_image():
        img = env['res.company.image'].create({
            'name': 'Test Report Logo',
            'image': test_image,
            'company_id': company.id,
        })
        return img.id > 0
    test("Create company image", create_company_image)

    company_image = env['res.company.image'].search([
        ('name', '=', 'Test Report Logo')
    ], limit=1)

    # Create department
    def create_department():
        dept = env['hr.department'].search([('name', '=', 'Test Report Dept')], limit=1)
        if not dept:
            dept = env['hr.department'].create({
                'name': 'Test Report Dept',
                'company_id': company.id,
            })
        return dept.id > 0
    test("Create department", create_department)

    department = env['hr.department'].search([('name', '=', 'Test Report Dept')], limit=1)

    # Create employees
    def create_employees():
        emp1 = env['hr.employee'].search([('name', '=', 'Test Report Employee 1')], limit=1)
        if not emp1:
            emp1 = env['hr.employee'].create({
                'name': 'Test Report Employee 1',
                'company_id': company.id,
                'department_id': department.id,
            })
        emp2 = env['hr.employee'].search([('name', '=', 'Test Report Employee 2')], limit=1)
        if not emp2:
            emp2 = env['hr.employee'].create({
                'name': 'Test Report Employee 2',
                'company_id': company.id,
                'department_id': department.id,
            })
        return emp1.id > 0 and emp2.id > 0
    test("Create test employees", create_employees)

    employee1 = env['hr.employee'].search([('name', '=', 'Test Report Employee 1')], limit=1)
    employee2 = env['hr.employee'].search([('name', '=', 'Test Report Employee 2')], limit=1)

    # =========================================================================
    # 2. TEST HR.VERSION CUSTOM FIELDS
    # =========================================================================
    print("\n[2/6] TESTING HR.VERSION CUSTOM FIELDS...")

    def test_work_permit_field():
        version = employee1.version_id
        if version:
            version.work_permit = 500.0
            return version.work_permit == 500.0
        return False
    test("Set work_permit on hr.version", test_work_permit_field)

    def test_cash_allowance_field():
        version = employee1.version_id
        if version:
            version.cash_allowance = 250.0
            return version.cash_allowance == 250.0
        return False
    test("Set cash_allowance on hr.version", test_cash_allowance_field)

    def test_version_wage():
        version = employee1.version_id
        if version:
            version.wage = 5000.0
            return version.wage == 5000.0
        return False
    test("Set wage on hr.version", test_version_wage)

    # Set values on employee2
    if employee2.version_id:
        employee2.version_id.write({
            'work_permit': 600.0,
            'cash_allowance': 300.0,
            'wage': 6000.0,
        })

    # =========================================================================
    # 3. TEST LEAVE FUNCTIONALITY
    # =========================================================================
    print("\n[3/6] TESTING LEAVE FUNCTIONALITY...")

    # Create leave type
    def create_leave_type():
        lt = env['hr.leave.type'].search([('name', '=', 'Test Report Annual Leave')], limit=1)
        if not lt:
            lt = env['hr.leave.type'].create({
                'name': 'Test Report Annual Leave',
                'company_id': company.id,
                'requires_allocation': 'yes',
                'leave_validation_type': 'no_validation',
            })
        return lt.id > 0
    test("Create leave type", create_leave_type)

    leave_type = env['hr.leave.type'].search([('name', '=', 'Test Report Annual Leave')], limit=1)

    # Create allocation
    def create_allocation():
        alloc = env['hr.leave.allocation'].search([
            ('employee_id', '=', employee1.id),
            ('holiday_status_id', '=', leave_type.id),
        ], limit=1)
        if not alloc:
            alloc = env['hr.leave.allocation'].create({
                'name': 'Test Report Allocation',
                'employee_id': employee1.id,
                'holiday_status_id': leave_type.id,
                'number_of_days': 25,
                'state': 'confirm',
            })
            alloc.action_approve()
        return alloc.state in ['validate', 'validate1']
    test("Create and approve leave allocation", create_allocation)

    # Create leave request
    def create_leave():
        leave = env['hr.leave'].search([('name', '=', 'Test Report Leave')], limit=1)
        if not leave:
            leave = env['hr.leave'].create({
                'name': 'Test Report Leave',
                'employee_id': employee1.id,
                'holiday_status_id': leave_type.id,
                'request_date_from': date.today() + timedelta(days=30),
                'request_date_to': date.today() + timedelta(days=32),
            })
        return leave.id > 0
    test("Create leave request", create_leave)

    leave = env['hr.leave'].search([('name', '=', 'Test Report Leave')], limit=1)

    # Test py3o method
    def test_py3o_method():
        if leave:
            result = leave.py3o_get_leave_type_summary()
            return 'remaining' in result and 'out of' in result
        return False
    test("Test py3o_get_leave_type_summary method", test_py3o_method)

    # =========================================================================
    # 4. TEST REPORT_XLSX_DYNAMIC REPORTS
    # =========================================================================
    print("\n[4/6] TESTING REPORT_XLSX_DYNAMIC REPORTS...")

    # Test payslip report wizard
    def test_payslip_wizard():
        wizard = env['hr.payslip.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
            'logo_id': company_image.id,
        })
        action = wizard.print_salary_receipt_report()
        # In Odoo 19, report_action() may return ir.actions.act_window
        # with the actual report_action embedded in context
        if action.get('type') == 'ir.actions.act_window':
            report_action = action.get('context', {}).get('report_action', {})
            return report_action.get('type') == 'ir.actions.report'
        return action.get('type') == 'ir.actions.report'
    test("Test payslip report wizard", test_payslip_wizard)

    # Test component report wizard
    def test_component_wizard():
        wizard = env['hr.payslip.component.report.wizard'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
        })
        action = wizard.print_component_report()
        # In Odoo 19, report_action() may return ir.actions.act_window
        # with the actual report_action embedded in context
        if action.get('type') == 'ir.actions.act_window':
            report_action = action.get('context', {}).get('report_action', {})
            return report_action.get('type') == 'ir.actions.report'
        return action.get('type') == 'ir.actions.report'
    test("Test component report wizard", test_component_wizard)

    # Test report SQL queries
    def test_payslip_report_query():
        report = env['report.hr_extra_report.hr_payslip_report']
        data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
        }
        result = report._prepare_report_data([], data)
        return isinstance(result, list)
    test("Test payslip report SQL query", test_payslip_report_query)

    def test_component_report_query():
        report = env['report.hr_extra_report.hr_payslip_component_report']
        form_data = {
            'date_from': str(date.today() - timedelta(days=365)),
            'date_to': str(date.today()),
        }
        result = report.get_report_body(form_data)
        return isinstance(result, list)
    test("Test component report SQL query", test_component_report_query)

    def test_report_header():
        report = env['report.hr_extra_report.hr_payslip_component_report']
        header = report.get_report_header()
        return len(header) == 16  # Should have 16 columns
    test("Test report header columns", test_report_header)

    # =========================================================================
    # 5. TEST REPORT_PY3O REPORTS
    # =========================================================================
    print("\n[5/6] TESTING REPORT_PY3O REPORTS...")

    # Test py3o report action references
    def test_leave_report_pjr():
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_pjr')
            return action.report_type == 'py3o'
        except:
            return False
    test("Leave report PJR action exists", test_leave_report_pjr)

    def test_leave_report_packo():
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_packo')
            return action.report_type == 'py3o'
        except:
            return False
    test("Leave report PACKO action exists", test_leave_report_packo)

    def test_leave_report_we():
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_we')
            return action.report_type == 'py3o'
        except:
            return False
    test("Leave report WE action exists", test_leave_report_we)

    def test_leave_report_marcom():
        try:
            action = env.ref('hr_extra_report.action_report_hr_leave_report_py3o_marcom')
            return action.report_type == 'py3o'
        except:
            return False
    test("Leave report MARCOM action exists", test_leave_report_marcom)

    # Test leave payment reports
    def test_leave_payment_pjr():
        try:
            action = env.ref('hr_extra_report.hr_leave_payment_report_py3o_pjr')
            return action.report_type == 'py3o'
        except:
            return False
    test("Leave payment PJR action exists", test_leave_payment_pjr)

    # =========================================================================
    # 6. TEST XLSX REPORT ACTIONS
    # =========================================================================
    print("\n[6/6] TESTING XLSX REPORT ACTIONS...")

    def test_payslip_xlsx_action():
        try:
            action = env.ref('hr_extra_report.action_report_hr_payslip_report_xlsx')
            return action.report_type == 'xlsx'
        except:
            return False
    test("Payslip XLSX report action exists", test_payslip_xlsx_action)

    def test_component_xlsx_action():
        try:
            action = env.ref('hr_extra_report.action_hr_payslip_component_report')
            return action.report_type == 'xlsx'
        except:
            return False
    test("Component XLSX report action exists", test_component_xlsx_action)

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

    print("="*70 + "\n")

    # Commit changes
    env.cr.commit()

    return results


# Run if in shell mode
if 'env' in dir():
    run_integration_tests(env)
