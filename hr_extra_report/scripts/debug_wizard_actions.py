#!/usr/bin/env python3
"""
Debug script to check wizard action return types.

Usage:
    python3 odoo-bin shell -c <config_file> < debug_wizard_actions.py
"""
import base64
from datetime import date, timedelta

def debug_actions(env):
    """Debug wizard action return types"""
    print("\n" + "="*70)
    print(" DEBUG WIZARD ACTIONS")
    print("="*70)

    company = env.ref('base.main_company')

    # Create test image
    test_image = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        b'\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00'
        b'\x00\x00\x1dIDATx\x9cc\xfc\xff\xff?\x03\x10\x00'
        b'\x00\xff\xff\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # Create or find company image
    company_image = env['res.company.image'].search([
        ('name', '=', 'Debug Test Logo')
    ], limit=1)
    if not company_image:
        company_image = env['res.company.image'].create({
            'name': 'Debug Test Logo',
            'image': test_image,
            'company_id': company.id,
        })

    print("\n1. Testing hr.payslip.report.wizard...")
    wizard1 = env['hr.payslip.report.wizard'].create({
        'date_from': date.today() - timedelta(days=30),
        'date_to': date.today(),
        'logo_id': company_image.id,
    })

    action1 = wizard1.print_salary_receipt_report()
    print(f"   Action type: {type(action1)}")
    print(f"   Action dict: {action1}")
    print(f"   action.get('type'): {action1.get('type') if isinstance(action1, dict) else 'N/A'}")

    print("\n2. Testing hr.payslip.component.report.wizard...")
    wizard2 = env['hr.payslip.component.report.wizard'].create({
        'date_from': date.today() - timedelta(days=30),
        'date_to': date.today(),
    })

    action2 = wizard2.print_component_report()
    print(f"   Action type: {type(action2)}")
    print(f"   Action dict: {action2}")
    print(f"   action.get('type'): {action2.get('type') if isinstance(action2, dict) else 'N/A'}")

    print("\n" + "="*70 + "\n")

    return action1, action2

# Run if in shell mode
if 'env' in dir():
    debug_actions(env)
