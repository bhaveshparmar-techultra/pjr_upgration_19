# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class MrpProductionConsolidated(models.Model):
    """ Manufacturing Orders Consolidated """
    _name = 'mrp.production.consolidated'
    _description = 'Production Order Consolidated'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name")
    origin = fields.Char(
        'Source', copy=False,
        help="Reference of the document that generated this production order request.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='State', default='draft', copy=False, index=True, readonly=True, tracking=True)
    component_line_ids = fields.One2many(
        'mrp.production.consolidated.line', 'raw_material_production_id', 'Components',
        readonly=False, copy=False)

    product_ids = fields.Many2many('product.product', string='Products')
    bom_ids = fields.Many2many(
        'mrp.bom', string='Bill of Materials', readonly=False,
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")

    move_dest_ids = fields.Many2many('stock.move', string="Stock Movements of Produced Goods")
    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('mrp.group_mrp_user').id)])
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        index=True)

    rule_id = fields.Many2one('stock.rule')
    sale_id = fields.Many2one('sale.order')
    mrp_production_ids = fields.Many2many(related='sale_id.mrp_production_ids')
    mrp_production_count = fields.Integer(related='sale_id.mrp_production_count')

    def action_done(self):
        """Create native odoo separate MO records for each products from this consolidated MO"""
        # Fields to exclude when copying to MO
        EXCLUDE_FIELDS = {
            'id', 'create_uid', 'create_date', 'write_uid', 'write_date', '__last_update',
            'raw_material_production_id', 'state', 'component_product_id', 'price_unit',
            'component_qty', 'production_group_id', 'use_create_components_lots'
        }
        # Field mappings from consolidated line to mrp.production (Odoo 19 compatibility)
        FIELD_MAPPINGS = {
            'date_planned_start': 'date_start',
            'date_planned_finished': 'date_finished',
        }

        MrpProduction = self.env['mrp.production']
        mo_valid_fields = set(MrpProduction._fields.keys())

        for rec in self:
            seen_products = set()
            mo_values = []
            for line in rec.component_line_ids:
                if line.product_id.id not in seen_products:
                    seen_products.add(line.product_id.id)

                    # Prepare values list to create odoo native mrp records separate for each product
                    data = {}

                    for key, field in line._fields.items():
                        if key in EXCLUDE_FIELDS:
                            continue  # Exclude some fields

                        value = getattr(line, key)

                        # Map field name if needed
                        target_key = FIELD_MAPPINGS.get(key, key)

                        # Only include fields that exist on mrp.production
                        if target_key not in mo_valid_fields:
                            continue

                        if isinstance(field, fields.Many2one):
                            data[target_key] = value.id
                        elif isinstance(field, fields.One2many) or isinstance(field, fields.Many2many):
                            data[target_key] = [(6, 0, [r.id for r in value])]
                        else:
                            data[target_key] = value
                    mo_values.append(data)
            if mo_values:
                self.env['stock.rule'].with_context(called_consolidated_mo=True)._run_manufacture(mo_values)
                rec.state = 'done'

    def action_view_mrp_production(self):
        self.ensure_one()
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(self.mrp_production_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.mrp_production_ids.id,
            })
        else:
            action.update({
                'name': _("Manufacturing Orders Generated by %s", self.name),
                'domain': [('id', 'in', self.mrp_production_ids.ids)],
                'view_mode': 'list,form',  # Odoo 19: tree -> list
            })
        return action


class MrpProductionConsolidatedLine(models.Model):
    """ Manufacturing Orders Consolidated """
    _name = 'mrp.production.consolidated.line'
    _description = 'Production Order Consolidated Line'

    name = fields.Char("Name")
    origin = fields.Char(
        'Source', copy=False,
        help="Reference of the document that generated this production order request.")
    raw_material_production_id = fields.Many2one('mrp.production.consolidated')
    state = fields.Selection(related='raw_material_production_id.state')
    # Odoo 19: type='product' is now type='consu' with is_storable=True
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '=', 'consu'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        copy=True,
        required=True, check_company=True)

    component_product_id = fields.Many2one(
        'product.product', 'Component',
        domain="[('type', '=', 'consu'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        copy=True,
        check_company=True)

    # Odoo 19: procurement.group model removed, using production_group_id from mrp.production
    production_group_id = fields.Many2one(
        'mrp.production.group', 'Production Group',
        copy=False)
    move_dest_ids = fields.Many2many('stock.move', string="Stock Movements of Produced Goods")
    # Odoo 19: reference_ids links MO to sale order through stock.reference
    reference_ids = fields.Many2many('stock.reference', string="References")
    product_description_variants = fields.Char('Custom Description')
    component_qty = fields.Float(string='Component Quantity')
    product_qty = fields.Float(string='Product Quantity')
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint', 'Orderpoint', copy=False, index='btree_not_null')
    product_uom_qty = fields.Float(string='Quantity', compute='_compute_product_uom_qty', store=True)
    propagate_cancel = fields.Boolean(
        'Propagate cancel and split')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', copy=True, readonly=False,
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        required=True, check_company=True, index=True)
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material', readonly=False,
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")
    # Odoo 19: use_create_components_lots is on picking type, use_auto_consume_components_lots removed
    use_create_components_lots = fields.Boolean(related='picking_type_id.use_create_components_lots')
    location_src_id = fields.Many2one(
        'stock.location', 'Components Location',
        check_company=True,
        readonly=False, required=True,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Location where the system will look for components.")
    # this field was added to be passed a default in view for manual raw moves
    warehouse_id = fields.Many2one(related='location_src_id.warehouse_id')
    location_dest_id = fields.Many2one(
        'stock.location', 'Finished Products Location', check_company=True,
        readonly=False, required=True,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Location where the system will stock the finished products.")
    date_planned_start = fields.Datetime(
        'Scheduled Date', copy=False,
        help="Date at which you plan to start the production.",
        index=True, required=True)
    date_planned_finished = fields.Datetime(
        'Scheduled End Date', store=True,
        help="Date at which you plan to finish the production.",
        copy=False)
    date_deadline = fields.Datetime(
        'Deadline', copy=False, readonly=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        readonly=False, required=True, copy=True)
    price_unit = fields.Float('Unit Price', copy=False)

    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        index=True, required=True)
    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('mrp.group_mrp_user').id)])

    @api.depends('product_uom_id', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for production in self:
            if production.product_id.uom_id != production.product_uom_id:
                production.product_uom_qty = production.product_uom_id._compute_quantity(production.product_qty,
                                                                                         production.product_id.uom_id)
            else:
                production.product_uom_qty = production.product_qty
