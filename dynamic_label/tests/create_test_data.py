# -*- coding: utf-8 -*-
"""
Test Data Creation Script for dynamic_label module

Run this in Odoo shell:
    python3 odoo-bin shell -d YOUR_DATABASE -c /path/to/odoo.conf

Then execute:
    exec(open('/path/to/create_test_data.py').read())
"""

def create_dynamic_label_test_data(env):
    """Create test data for dynamic_label module"""

    print("=" * 60)
    print("Creating test data for Dynamic Label module...")
    print("=" * 60)

    # 1. Create Page Label Design Template (Required)
    print("\n1. Creating Page Label Design Template...")

    design_template = env['product.page.label.design'].search([('name', '=', 'Test Label Template')], limit=1)
    if not design_template:
        design_template = env['product.page.label.design'].create({
            'name': 'Test Label Template',
            'page_template_design': '''
<t t-name="dynamic_label.dynamic_report_temp">
    <t t-call="web.html_container">
        <t t-foreach="doc_ids" t-as="doc_id">
            <div class="page">
                <table width="100%" style="margin:0px;padding:0px;table-layout:fixed !important;">
                    <span t-as="f" t-foreach="draw_table(data)">
                        <span t-as="c" t-foreach="f">
                            <tr>
                                <span t-as="product" t-foreach="f[c]">
                                    <t t-if="product != False">
                                        <t t-set="style" t-value="draw_style(data)"/>
                                        <td t-att-style="style" align="center">
                                            <div style="margin:0;padding:0;margin-left:0px;">
                                                <div style="color:black;font-size:11px;font-weight:bold;white-space:normal;">
                                                   <span t-field="product.name"/>
                                                </div>
                                                <div style="color:black;">
                                                    <span t-out="get_barcode(product, data['form']['barcode_field'], data)"/>
                                                </div>
                                                <div style="color:black;font-weight:bold; font-size:20px;">
                                                    <span style="color:black;font-weight:bold; font-size:16px;">KD </span>
                                                    <span style="color:black;font-weight:bold; font-size:16px;" t-field="product.lst_price"/>
                                                </div>
                                            </div>
                                        </td>
                                    </t>
                                    <t t-if="product == False">
                                        <t t-set="style_td" t-value="draw_style(data)"/>
                                        <td t-att-style="style_td"></td>
                                    </t>
                                </span>
                            </tr>
                        </span>
                    </span>
                </table>
            </div>
        </t>
    </t>
</t>
            ''',
            'page_width': 210,
            'page_height': 297,
            'dpi': 90,
            'margin_top': 5,
            'margin_left': 5,
            'margin_bottom': 5,
            'margin_right': 5,
            'orientation': 'Portrait',
            'format': 'A4',
            'col_no': 4,
            'col_width': 52.5,
            'col_height': 29.7,
            'from_row': 1,
            'from_col': 1,
            'with_barcode': True,
            'barcode_type': 'Code128',  # Code128 is more flexible than EAN13
            'barcode_height': 300,
            'barcode_width': 1500,
            'display_height': 40,
            'display_width': 200,
            'humanReadable': True,
            'barcode_field': 'barcode',
        })
        print(f"   Created: {design_template.name}")
    else:
        print(f"   Already exists: {design_template.name}")

    # 2. Create Test Products with Barcodes
    print("\n2. Creating test products with barcodes...")

    test_products_data = [
        {
            'name': 'Label Test Product A',
            'default_code': 'LBL-PROD-A',
            'barcode': 'LBL0001',
            'list_price': 25.50,
            'type': 'consu',
        },
        {
            'name': 'Label Test Product B',
            'default_code': 'LBL-PROD-B',
            'barcode': 'LBL0002',
            'list_price': 45.00,
            'type': 'consu',
        },
        {
            'name': 'Label Test Product C',
            'default_code': 'LBL-PROD-C',
            'barcode': 'LBL0003',
            'list_price': 15.75,
            'type': 'consu',
        },
        {
            'name': 'Label Test Product D',
            'default_code': 'LBL-PROD-D',
            'barcode': 'LBL0004',
            'list_price': 99.99,
            'type': 'consu',
        },
        {
            'name': 'Label Test Product E',
            'default_code': 'LBL-PROD-E',
            'barcode': 'LBL0005',
            'list_price': 5.25,
            'type': 'consu',
        },
    ]

    created_products = []
    for prod_data in test_products_data:
        product = env['product.product'].search([('barcode', '=', prod_data['barcode'])], limit=1)
        if not product:
            product = env['product.product'].create(prod_data)
            print(f"   Created: {product.name} (Barcode: {product.barcode})")
        else:
            print(f"   Already exists: {product.name} (Barcode: {product.barcode})")
        created_products.append(product)

    # 3. Create a test Sale Order (optional - to test from Sale Order)
    print("\n3. Creating test Sale Order...")

    partner = env['res.partner'].search([('name', '=', 'Label Test Customer')], limit=1)
    if not partner:
        partner = env['res.partner'].create({
            'name': 'Label Test Customer',
            'email': 'labeltest@example.com',
        })
        print(f"   Created partner: {partner.name}")

    sale_order = env['sale.order'].search([('name', 'like', 'Label-Test-%')], limit=1)
    if not sale_order:
        sale_order = env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': created_products[0].id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': created_products[1].id,
                    'product_uom_qty': 3,
                }),
                (0, 0, {
                    'product_id': created_products[2].id,
                    'product_uom_qty': 2,
                }),
            ],
        })
        print(f"   Created Sale Order: {sale_order.name}")
    else:
        print(f"   Already exists: {sale_order.name}")

    # Commit the transaction
    env.cr.commit()

    print("\n" + "=" * 60)
    print("TEST DATA CREATED SUCCESSFULLY!")
    print("=" * 60)
    print("\nHow to test the Dynamic Label module:")
    print("-" * 60)
    print("""
1. FROM PRODUCTS:
   - Go to Sales > Products > Products
   - Select one or more products (use the test products created)
   - Click Action > "Print Product Page Label"
   - Select the "Test Label Template"
   - Set quantities for each product
   - Click "Print" to generate PDF labels

2. FROM SALE ORDER:
   - Go to Sales > Orders > Quotations
   - Open the sale order (Label Test Customer)
   - Click Action > "Print Product Page Label"
   - Products from the order will be pre-loaded
   - Click "Print" to generate PDF labels

3. FROM PURCHASE ORDER:
   - Create a Purchase Order with products
   - Click Action > "Print Product Page Label"

4. FROM STOCK PICKING:
   - Open a Delivery or Receipt
   - Click Action > "Print Product Page Label"

5. MANAGE LABEL TEMPLATES:
   - Go to Sales > Products > Product Page Label > Page Label Design Template
   - Create/edit label templates

6. TEST BARCODE SCANNING:
   - In the label wizard, use the "Scan" field
   - Enter a barcode (e.g., LBL0001) to add product
    """)
    print("-" * 60)

    return {
        'design_template': design_template,
        'products': created_products,
        'sale_order': sale_order,
        'partner': partner,
    }


# Run if executed directly in Odoo shell
if 'env' in dir():
    result = create_dynamic_label_test_data(env)
