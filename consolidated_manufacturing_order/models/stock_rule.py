# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, SUPERUSER_ID, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_manufacture(self, procurements):
        """Override to create consolidated MO instead of separate MOs.

        In Odoo 19, _run_manufacture processes procurements and creates MOs.
        This override intercepts that to create a consolidated preview first.
        """
        # If called from consolidated MO action_done, create native MOs directly
        if self._context.get('called_consolidated_mo'):
            # procurements here is a list of dict values for MO creation
            productions = self.env['mrp.production']
            for productions_values in procurements:
                company_id = productions_values.get('company_id')
                # create the MO as SUPERUSER
                production = self.env['mrp.production'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(
                    productions_values)
                production.action_confirm()
                productions |= production

            for production in productions:
                origin_production = production.move_dest_ids and production.move_dest_ids[
                    0].raw_material_production_id or False
                orderpoint = production.orderpoint_id
                if orderpoint and orderpoint.create_uid.id == SUPERUSER_ID and orderpoint.trigger == 'manual':
                    production.message_post(
                        body=_('This production order has been created from Replenishment Report.'),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note')
                elif orderpoint:
                    production.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': production, 'origin': orderpoint},
                        subtype_xmlid='mail.mt_note')
                elif origin_production:
                    production.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': production, 'origin': origin_production},
                        subtype_xmlid='mail.mt_note')
            return True

        # Normal flow - intercept and create consolidated MO
        new_productions_values_by_company = defaultdict(lambda: defaultdict(list))
        procurement_ref = None

        for procurement, rule in procurements:
            procurement_ref = procurement  # Keep reference for sale_id linking
            if procurement.product_uom.compare(procurement.product_qty, 0) <= 0:
                continue
            bom = rule._get_matching_bom(procurement.product_id, procurement.company_id, procurement.values)

            mo = self.env['mrp.production']
            if procurement.origin != 'MPS':
                domain = rule._make_mo_get_domain(procurement, bom)
                mo = self.env['mrp.production'].sudo().search(domain, limit=1)

            is_batch_size = bom and bom.enable_batch_size
            if not mo or is_batch_size:
                procurement_qty = procurement.product_qty
                batch_size = bom.product_uom_id._compute_quantity(bom.batch_size, procurement.product_uom) if is_batch_size else procurement_qty
                vals = rule._prepare_mo_vals(*procurement, bom)
                while procurement.product_uom.compare(procurement_qty, 0) > 0:
                    new_productions_values_by_company[procurement.company_id.id]['values'].append({
                        **vals,
                        'product_qty': procurement.product_uom._compute_quantity(batch_size, bom.product_uom_id) if bom else procurement_qty,
                    })
                    new_productions_values_by_company[procurement.company_id.id]['procurements'].append(procurement)
                    procurement_qty -= batch_size
            else:
                # Increase qty on existing MO
                self.env['change.production.qty'].sudo().with_context(skip_activity=True).create({
                    'mo_id': mo.id,
                    'product_qty': mo.product_id.uom_id._compute_quantity((mo.product_uom_qty + procurement.product_qty), mo.product_uom_id)
                }).change_prod_qty()

        # If no new MOs to create, return
        if not new_productions_values_by_company:
            return True

        # Create consolidated MO instead of native MOs
        for company_id, data in new_productions_values_by_company.items():
            productions_values = data['values']
            if not productions_values:
                continue

            consolidated_values = {
                'name': f"Consolidated MO for {productions_values[0].get('origin', '')}",
                'state': 'confirmed',
                'company_id': company_id,
            }
            consolidated_mo = self.env['mrp.production.consolidated'].with_user(SUPERUSER_ID).sudo().with_company(
                company_id).create(consolidated_values)

            consolidated_mo_lines = self.env['mrp.production.consolidated.line']

            # Get valid fields for consolidated line model
            ConsolidatedLine = self.env['mrp.production.consolidated.line']
            valid_fields = set(ConsolidatedLine._fields.keys())

            for values_dict in productions_values:
                product_line_exist = consolidated_mo_lines.filtered(
                    lambda x: x.product_id.id == values_dict.get('product_id'))
                if product_line_exist:
                    product_line_exist.write({
                        'product_qty': product_line_exist.product_qty + values_dict.get('product_qty'),
                        'component_qty': product_line_exist.product_qty + values_dict.get('product_qty'),
                        'move_dest_ids': values_dict.get('move_dest_ids'),
                    })
                else:
                    consolidated_mo.write({'product_ids': [(4, values_dict.get('product_id'))]})
                    # Filter values_dict to only include valid fields for consolidated line
                    filtered_vals = {k: v for k, v in values_dict.items() if k in valid_fields}
                    # Map Odoo 19 field names to consolidated line field names
                    if 'date_start' in values_dict and 'date_planned_start' not in filtered_vals:
                        filtered_vals['date_planned_start'] = values_dict['date_start']
                    filtered_vals['raw_material_production_id'] = consolidated_mo.id
                    filtered_vals['component_qty'] = filtered_vals.get('product_qty')
                    consolidated_mo_line = ConsolidatedLine.create(filtered_vals)
                    consolidated_mo_lines += consolidated_mo_line

            # Expand BOM lines to show components
            for line in consolidated_mo_lines:
                bom_line_ids = line.bom_id.bom_line_ids
                if bom_line_ids:
                    original_qty = line.product_qty
                    line.component_product_id = bom_line_ids[0].product_id
                    line.component_qty = original_qty * bom_line_ids[0].product_qty
                    for bom_line in bom_line_ids[1:]:
                        newqty = original_qty * bom_line.product_qty
                        data = {}
                        for key, field in line._fields.items():
                            if key in ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', '__last_update']:
                                continue
                            value = getattr(line, key)
                            if isinstance(field, fields.Many2one):
                                data[key] = value.id
                            elif isinstance(field, fields.One2many) or isinstance(field, fields.Many2many):
                                data[key] = [(6, 0, [rec.id for rec in value])]
                            else:
                                data[key] = value
                        data.update({'component_product_id': bom_line.product_id.id, 'component_qty': newqty})
                        self.env['mrp.production.consolidated.line'].create(data)

            # Link to Sale Order if available
            if procurement_ref:
                # Odoo 19: sale_line_id is in values, use it to get sale order
                sale_line = procurement_ref.values.get('sale_line_id')
                if sale_line:
                    sale_line_obj = self.env['sale.order.line'].browse(sale_line)
                    sale_order = sale_line_obj.order_id
                    if sale_order:
                        sale_order.write({'consolidated_mrp_ids': [(4, consolidated_mo.id)]})
                        consolidated_mo.sale_id = sale_order.id

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production.consolidated',
                'view_mode': 'form',
                'res_id': consolidated_mo.id,
            }

        return True
