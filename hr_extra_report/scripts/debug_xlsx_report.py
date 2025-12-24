#!/usr/bin/env python3
"""
Debug script to test XLSX report action.
Usage: python3 odoo-bin shell -c <config> --no-http < debug_xlsx_report.py
"""
import json
from datetime import date, timedelta
import base64

def debug_xlsx_report(env):
    print("\n" + "="*70)
    print(" DEBUG XLSX REPORT ACTION")
    print("="*70)

    # Create test image
    test_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        b'\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00'
        b'\x00\x00\x1dIDATx\x9cc\xfc\xff\xff?\x03\x10\x00'
        b'\x00\xff\xff\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    company = env.ref('base.main_company')

    # Get or create company image
    company_image = env['res.company.image'].search([
        ('name', '=', 'Debug XLSX Logo')
    ], limit=1)
    if not company_image:
        company_image = env['res.company.image'].create({
            'name': 'Debug XLSX Logo',
            'image': test_image,
            'company_id': company.id,
        })

    print(f"\n1. Company image ID: {company_image.id}")

    # Test 1: Get the report action
    print("\n2. Getting report action...")
    report = env.ref('hr_extra_report.action_report_hr_payslip_report_xlsx')
    print(f"   Report ID: {report.id}")
    print(f"   Report name: {report.name}")
    print(f"   Report type: {report.report_type}")
    print(f"   Report model: {report.model}")

    # Test 2: Create wizard and call print method
    print("\n3. Creating wizard...")
    wizard = env['hr.payslip.report.wizard'].create({
        'date_from': date.today() - timedelta(days=30),
        'date_to': date.today(),
        'logo_id': company_image.id,
    })
    print(f"   Wizard ID: {wizard.id}")

    # Test 3: Call print method
    print("\n4. Calling print_salary_receipt_report...")
    try:
        action = wizard.print_salary_receipt_report()
        print(f"   Action type: {type(action)}")
        print(f"   Action keys: {list(action.keys()) if isinstance(action, dict) else 'N/A'}")

        if isinstance(action, dict):
            for key, value in action.items():
                if key == 'context':
                    # Context can be large, just show type
                    print(f"   {key}: <dict with {len(value) if isinstance(value, dict) else 'unknown'} keys>")
                elif key == 'data':
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")

            # Try to serialize to JSON
            print("\n5. Testing JSON serialization...")
            try:
                # Create a clean copy for JSON serialization
                clean_action = {}
                for k, v in action.items():
                    if k == 'context':
                        # Convert frozendict to regular dict
                        clean_action[k] = dict(v) if hasattr(v, 'items') else {}
                    else:
                        clean_action[k] = v

                json_str = json.dumps(clean_action, default=str)
                print(f"   JSON serialization: OK (length: {len(json_str)})")
            except Exception as e:
                print(f"   JSON serialization FAILED: {e}")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Test report action directly
    print("\n6. Testing report.report_action directly...")
    try:
        data = {
            'date_from': str(date.today() - timedelta(days=30)),
            'date_to': str(date.today()),
            'logo_id': company_image.id,
        }
        direct_action = report.with_context(discard_logo_check=True).report_action(
            docids=wizard.ids,
            data=data,
            config=False,
        )
        print(f"   Direct action type: {direct_action.get('type')}")
        print(f"   Direct action report_type: {direct_action.get('report_type')}")
        print(f"   Direct action report_name: {direct_action.get('report_name')}")
        print(f"   Direct action has context: {'context' in direct_action}")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)

# Run if in shell mode
if 'env' in dir():
    debug_xlsx_report(env)
