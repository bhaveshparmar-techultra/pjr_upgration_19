#!/usr/bin/env python3
"""
Create sample payroll data for testing hr_extra_report.
This script creates employees, contracts, salary structures, and payslips.

Usage:
    python3 odoo-bin shell -c <config> --no-http < create_sample_payroll_data.py
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import base64

def create_sample_payroll_data(env):
    print("\n" + "="*70)
    print(" CREATING SAMPLE PAYROLL DATA")
    print("="*70)

    company = env.ref('base.main_company')

    # Create test image for company logo
    test_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        b'\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00'
        b'\x00\x00\x1dIDATx\x9cc\xfc\xff\xff?\x03\x10\x00'
        b'\x00\xff\xff\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # =========================================================================
    # 1. CREATE COMPANY IMAGE FOR REPORTS
    # =========================================================================
    print("\n[1/6] Creating company image...")
    company_image = env['res.company.image'].search([
        ('name', '=', 'Sample Report Logo')
    ], limit=1)
    if not company_image:
        company_image = env['res.company.image'].create({
            'name': 'Sample Report Logo',
            'image': test_image,
            'company_id': company.id,
        })
    print(f"  ✓ Company image: {company_image.name} (ID: {company_image.id})")

    # =========================================================================
    # 2. CREATE DEPARTMENT
    # =========================================================================
    print("\n[2/6] Creating department...")
    department = env['hr.department'].search([
        ('name', '=', 'Sample HR Department')
    ], limit=1)
    if not department:
        department = env['hr.department'].create({
            'name': 'Sample HR Department',
            'company_id': company.id,
        })
    print(f"  ✓ Department: {department.name} (ID: {department.id})")

    # =========================================================================
    # 3. CREATE EMPLOYEES
    # =========================================================================
    print("\n[3/6] Creating employees...")
    employees = []
    employee_data = [
        {'name': 'John Smith', 'work_email': 'john.smith@example.com'},
        {'name': 'Jane Doe', 'work_email': 'jane.doe@example.com'},
        {'name': 'Bob Johnson', 'work_email': 'bob.johnson@example.com'},
    ]

    for emp_data in employee_data:
        employee = env['hr.employee'].search([
            ('name', '=', emp_data['name'])
        ], limit=1)
        if not employee:
            employee = env['hr.employee'].create({
                'name': emp_data['name'],
                'work_email': emp_data['work_email'],
                'company_id': company.id,
                'department_id': department.id,
            })
        employees.append(employee)
        print(f"  ✓ Employee: {employee.name} (ID: {employee.id})")

    # =========================================================================
    # 4. CREATE/UPDATE HR.VERSION (CONTRACTS) WITH CUSTOM FIELDS
    # =========================================================================
    print("\n[4/6] Setting up employee versions (contracts)...")
    wages = [5000.0, 6500.0, 4500.0]
    work_permits = [500.0, 600.0, 400.0]
    cash_allowances = [250.0, 300.0, 200.0]

    for i, employee in enumerate(employees):
        if employee.version_id:
            employee.version_id.write({
                'wage': wages[i],
                'work_permit': work_permits[i],
                'cash_allowance': cash_allowances[i],
            })
            print(f"  ✓ Updated version for {employee.name}: wage={wages[i]}, work_permit={work_permits[i]}")
        else:
            print(f"  ⚠ No version found for {employee.name}")

    # =========================================================================
    # 5. GET OR CREATE SALARY STRUCTURE
    # =========================================================================
    print("\n[5/6] Setting up salary structure...")

    # Find existing salary structure
    salary_structure = env['hr.payroll.structure'].search([], limit=1)
    if salary_structure:
        print(f"  ✓ Using existing structure: {salary_structure.name} (ID: {salary_structure.id})")
    else:
        # Try to create a basic structure
        struct_type = env['hr.payroll.structure.type'].search([], limit=1)
        if not struct_type:
            struct_type = env['hr.payroll.structure.type'].create({
                'name': 'Sample Structure Type',
                'wage_type': 'monthly',
            })
        salary_structure = env['hr.payroll.structure'].create({
            'name': 'Sample Salary Structure',
            'type_id': struct_type.id,
        })
        print(f"  ✓ Created structure: {salary_structure.name} (ID: {salary_structure.id})")

    # =========================================================================
    # 6. CREATE PAYSLIPS
    # =========================================================================
    print("\n[6/6] Creating payslips...")

    # Create payslips for last 3 months
    today = date.today()
    months = [
        (today - relativedelta(months=2)).replace(day=1),
        (today - relativedelta(months=1)).replace(day=1),
        today.replace(day=1),
    ]

    payslips_created = 0
    for employee in employees:
        for month_start in months:
            # Calculate month end
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            # Check if payslip already exists
            existing = env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_from', '=', month_start),
                ('date_to', '=', month_end),
            ], limit=1)

            if existing:
                print(f"  - Payslip exists for {employee.name} ({month_start})")
                continue

            try:
                # Create payslip
                payslip_vals = {
                    'name': f"Salary Slip - {employee.name} - {month_start.strftime('%B %Y')}",
                    'employee_id': employee.id,
                    'date_from': month_start,
                    'date_to': month_end,
                    'company_id': company.id,
                }

                # Try to set structure if employee has contract
                if employee.version_id:
                    payslip_vals['struct_id'] = salary_structure.id

                payslip = env['hr.payslip'].create(payslip_vals)

                # Try to compute the payslip
                try:
                    payslip.compute_sheet()
                except Exception as e:
                    print(f"    ⚠ Could not compute sheet: {e}")

                payslips_created += 1
                print(f"  ✓ Created payslip: {payslip.name} (ID: {payslip.id})")

            except Exception as e:
                print(f"  ✗ Failed to create payslip for {employee.name} ({month_start}): {e}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    print(f"  Company Image ID: {company_image.id}")
    print(f"  Department: {department.name}")
    print(f"  Employees created/found: {len(employees)}")
    print(f"  Payslips created: {payslips_created}")
    print("\n  To test the report:")
    print(f"    1. Go to Payroll > Reports > Salary Receipt Report")
    print(f"    2. Select date range covering the last 3 months")
    print(f"    3. Select logo: 'Sample Report Logo' (ID: {company_image.id})")
    print(f"    4. Click 'Print Report'")
    print("="*70 + "\n")

    # Commit changes
    env.cr.commit()

    return {
        'company_image_id': company_image.id,
        'employees': len(employees),
        'payslips': payslips_created,
    }

# Run if in shell mode
if 'env' in dir():
    create_sample_payroll_data(env)
