from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from stdnum import ean

paper_format_dict = {'A0': [841, 1189], 'A1': [594, 841], 'A2': [420, 594], 'A3': [297, 420], 'A4': [210, 297],
                     'A5': [148, 210], 'A6': [105, 148], 'A7': [74, 105], 'A8': [52, 74], 'A9': [37, 52],
                     'B0': [1000, 1414], 'B1': [707, 1000], 'B2': [500, 707], 'B3': [353, 500], 'B4': [250, 353],
                     'B5': [176, 250], 'B6': [125, 176], 'B7': [88, 125], 'B8': [62, 88], 'B9': [33, 62],
                     'B10': [31, 44],
                     'C5E': [163, 229], 'Comm10E': [105, 241], 'DLE': [110, 220], 'Executive': [190.5, 254],
                     'Folio': [210, 330], 'Ledger': [431.8, 279.4], 'Legal': [215.9, 355.6], 'Letter': [215.9, 279.4],
                     'Tabloid': [279.4, 431.8]
                     }


class product_page_label_design(models.Model):
    _name = 'product.page.label.design'
    _description = 'Product Page Label Design'

    @api.model
    def default_get(self, fields_list):
        res = super(product_page_label_design, self).default_get(fields_list)
        if self._context.get('wiz_id') and self._context.get('from_wizard'):
            for wiz in self.env['wizard.product.page.report'].browse(self._context.get('wiz_id')):
                res.update({'page_template_design': wiz.column_report_design,
                            'page_width': wiz.page_width, 'page_height': wiz.page_height,
                            'dpi': wiz.dpi, 'margin_top': wiz.margin_top,
                            'margin_left': wiz.margin_left, 'margin_bottom': wiz.margin_bottom,
                            'margin_right': wiz.margin_right, 'orientation': wiz.orientation,
                            'barcode_type': wiz.barcode_type, 'humanReadable': wiz.humanReadable,
                            'barcode_height': wiz.barcode_height, 'barcode_width': wiz.barcode_width,
                            'display_height': wiz.display_height, 'display_width': wiz.display_width,
                            'with_barcode': wiz.with_barcode, 'format': wiz.format,
                            'col_no': wiz.col_no, 'col_width': wiz.col_width,
                            'col_height': wiz.col_height, 'barcode_field': wiz.barcode_field,
                            })
        return res

    @api.model
    def _get_barcode_field(self):
        field_list = []
        ir_model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
        if ir_model_id:
            for field in self.env['ir.model.fields'].search(
                    [('field_description', '!=', 'unknown'), ('model_id', '=', ir_model_id.id),
                     ('ttype', '=', 'char')]):
                field_list.append((field.name, field.field_description))
        return field_list

    name = fields.Char(string="Design Name")
    page_template_design = fields.Text(string="Report Design")
    # page
    page_width = fields.Integer(string='Page Width (mm)', default=210)
    page_height = fields.Integer(string='Page Height (mm)', default=297)
    dpi = fields.Integer(string='DPI', default=80, help="The number of individual dots\
                                that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=1)
    margin_left = fields.Integer(string='Margin Left (mm)', default=1)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=1)
    margin_right = fields.Integer(string='Margin Right (mm)', default=1)
    orientation = fields.Selection([('Landscape', 'Landscape'),
                                    ('Portrait', 'Portrait')],
                                   string='Orientation', default='Portrait', required=True)
    # barcode
    barcode_type = fields.Selection([('Codabar', 'Codabar'), ('Code11', 'Code11'),
                                     ('Code128', 'Code128'), ('EAN13', 'EAN13'),
                                     ('Extended39', 'Extended39'), ('EAN8', 'EAN8'),
                                     ('Extended93', 'Extended93'), ('USPS_4State', 'USPS_4State'),
                                     ('I2of5', 'I2of5'), ('UPCA', 'UPCA'),
                                     ('QR', 'QR')],
                                    string='Type', default='EAN13', required=True)
    humanReadable = fields.Boolean(string="HumanReadable", help="User wants to print barcode number\
                                    with barcode page label.")
    barcode_height = fields.Integer(string="Height", default=300, required=True, help="This height will\
                                    required for the clearity of the barcode.")
    barcode_width = fields.Integer(string="Width", default=1500, required=True, help="This width will \
                                    required for the clearity of the barcode.")
    display_height = fields.Integer(string="Display Height (px)", required=True, default=40,
                                    help="This height will required for display barcode in page label.")
    display_width = fields.Integer(string="Display Width (px)", required=True, default=200,
                                   help="This width will required for display barcode in page label.")
    with_barcode = fields.Boolean(string='Barcode', help="Click this check box if user want to print\
                                    barcode for Product Page Label.", default=True)
    # new columns and rows fields
    format = fields.Selection([('A0', 'A0  5   841 x 1189 mm'),
                               ('A1', 'A1  6   594 x 841 mm'),
                               ('A2', 'A2  7   420 x 594 mm'),
                               ('A3', 'A3  8   297 x 420 mm'),
                               ('A4', 'A4  0   210 x 297 mm, 8.26 x 11.69 inches'),
                               ('A5', 'A5  9   148 x 210 mm'),
                               ('A6', 'A6  10  105 x 148 mm'),
                               ('A7', 'A7  11  74 x 105 mm'),
                               ('A8', 'A8  12  52 x 74 mm'),
                               ('A9', 'A9  13  37 x 52 mm'),
                               ('B0', 'B0  14  1000 x 1414 mm'),
                               ('B1', 'B1  15  707 x 1000 mm'),
                               ('B2', 'B2  17  500 x 707 mm'),
                               ('B3', 'B3  18  353 x 500 mm'),
                               ('B4', 'B4  19  250 x 353 mm'),
                               ('B5', 'B5  1   176 x 250 mm, 6.93 x 9.84 inches'),
                               ('B6', 'B6  20  125 x 176 mm'),
                               ('B7', 'B7  21  88 x 125 mm'),
                               ('B8', 'B8  22  62 x 88 mm'),
                               ('B9', 'B9  23  33 x 62 mm'),
                               ('B10', ':B10    16  31 x 44 mm'),
                               ('C5E', 'C5E 24  163 x 229 mm'),
                               ('Comm10E', 'Comm10E 25  105 x 241 mm, U.S. '
                                           'Common 10 Envelope'),
                               ('DLE', 'DLE 26 110 x 220 mm'),
                               ('Executive', 'Executive 4   7.5 x 10 inches, '
                                             '190.5 x 254 mm'),
                               ('Folio', 'Folio 27  210 x 330 mm'),
                               ('Ledger', 'Ledger  28  431.8 x 279.4 mm'),
                               ('Legal', 'Legal    3   8.5 x 14 inches, '
                                         '215.9 x 355.6 mm'),
                               ('Letter', 'Letter 2 8.5 x 11 inches, '
                                          '215.9 x 279.4 mm'),
                               ('Tabloid', 'Tabloid 29 279.4 x 431.8 mm'),
                               ('custom', 'Custom')],
                              string='Paper Type', default="custom",
                              help="Select Proper Paper size")
    col_no = fields.Integer('No. of Column', default=1)
    col_width = fields.Float('Column Width (mm)', default=52.5)
    col_height = fields.Float('Column Height (mm)', default=29.7)
    from_col = fields.Integer(string="Start Column", default=1)
    from_row = fields.Integer(string="Start Row", default=1)
    active = fields.Boolean(string="Active", default=True)
    barcode_field = fields.Selection('_get_barcode_field', string="Barcode Field")

    def close_wizard(self):
        self.write({'active': False})
        return {
            'name': _('Print Product Page Label'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.product.page.report',
            'target': 'new',
            'res_id': self._context.get('wiz_id'),
            'context': self.env.context
        }

    def go_to_label_wizard(self):
        if not self.name:
            raise UserError(_('Page Label Design Name is required.'))
        return {
            'name': _('Product Page Label'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.product.page.report',
            'target': 'new',
            'res_id': self._context.get('wiz_id'),
            'context': {}
        }


class productPageLabelQty(models.TransientModel):
    _name = 'product.page.label.qty'
    _description = 'Product Page Label Quantity'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Integer(string='Quantity', default=1)
    prod_small_wiz_id = fields.Many2one('wizard.product.page.report', string='Product Wizard')


class wizard_report(models.TransientModel):
    _name = "wizard.product.page.report"
    _description = 'Wizard Product Page Report'

    @api.model
    def default_get(self, fields_list):
        prod_list = []
        product_dict = {}
        res = super(wizard_report, self).default_get(fields_list)
        if self._context.get('active_ids') and self._context.get('active_model') == 'purchase.order':
            for line in self.env['purchase.order.line'].search([('order_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and product_dict.get(line.product_id.id):
                    product_dict.update(
                        {line.product_id.id: int(product_dict.get(line.product_id.id)) + int(line.product_qty)})
                else:
                    product_dict.update({line.product_id.id: line.product_qty})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'sale.order':
            for line in self.env['sale.order.line'].search([('order_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and product_dict.get(line.product_id.id):
                    product_dict.update(
                        {line.product_id.id: int(product_dict.get(line.product_id.id)) + int(line.product_uom_qty)})
                else:
                    product_dict.update({line.product_id.id: line.product_uom_qty})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'stock.picking':
            for line in self.env['stock.move.line'].search(
                    [('picking_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and product_dict.get(line.product_id.id):
                    product_dict.update(
                        {line.product_id.id: int(product_dict.get(line.product_id.id)) + int(line.qty_done)})
                else:
                    product_dict.update({line.product_id.id: line.qty_done})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'product.product':
            for line in self.env['product.product'].browse(self._context.get('active_ids')):
                if line and product_dict.get(line.id):
                    product_dict.update({line.id: int(product_dict.get(line.id))})
                else:
                    product_dict.update({line.id: line.qty_available})
        for product_id in product_dict:
            prod_list.append((0, 0, {'product_id': product_id, 'qty': product_dict[product_id]}))
        res['product_ids'] = prod_list
        all_design = self.env['product.page.label.design'].search([])
        if all_design:
            res['design_id'] = all_design[0].id
        else:
            raise ValidationError(_('Please create Page Label Design Template'))
        self.on_change_design_id()
        return res

    @api.model
    def _get_page_report_design(self):
        view_id = self.env['ir.ui.view'].search([('name', '=', 'dynamic_report_temp')])
        if view_id.arch:
            return view_id.arch

    @api.model
    def _get_page_report_id(self):
        view_id = self.env['ir.ui.view'].search([('name', '=', 'dynamic_report_temp')])
        if not view_id:
            raise UserError('Someone has deleted the reference view of report.\
                Please Update the module!')
        return view_id

    @api.model
    def _get_report_paperformat_id(self):
        xml_id = self.env['ir.actions.report'].search([('report_name', '=', 'dynamic_label.dynamic_report_temp')])
        if not xml_id or not xml_id.paperformat_id:
            raise UserError('Someone has deleted the reference paper format of report.\
                Please Update the module!')
        return xml_id.paperformat_id.id

    @api.onchange('paper_format_id')
    def onchange_report_paperformat_id(self):
        if self.paper_format_id:
            self.format = self.paper_format_id.format
            self.page_width = self.paper_format_id.page_width
            self.page_height = self.paper_format_id.page_height
            self.orientation = self.paper_format_id.orientation
            self.margin_top = self.paper_format_id.margin_top
            self.margin_left = self.paper_format_id.margin_left
            self.margin_bottom = self.paper_format_id.margin_bottom
            self.margin_right = self.paper_format_id.margin_right
            self.dpi = self.paper_format_id.dpi

    @api.onchange('design_id')
    def on_change_design_id(self):
        if self.design_id:
            self.column_report_design = self.design_id.page_template_design
            # paper format args
            self.format = self.design_id.format
            self.page_width = self.design_id.page_width
            self.page_height = self.design_id.page_height
            self.orientation = self.design_id.orientation
            self.dpi = self.design_id.dpi
            self.margin_top = self.design_id.margin_top
            self.margin_left = self.design_id.margin_left
            self.margin_bottom = self.design_id.margin_bottom
            self.margin_right = self.design_id.margin_right
            # barcode args
            self.with_barcode = self.design_id.with_barcode
            self.barcode_type = self.design_id.barcode_type
            self.barcode_height = self.design_id.barcode_height
            self.barcode_width = self.design_id.barcode_width
            self.humanReadable = self.design_id.humanReadable
            self.display_height = self.design_id.display_height
            self.display_width = self.design_id.display_width
            # display row col args
            self.col_no = self.design_id.col_no
            self.col_width = self.design_id.col_width
            self.col_height = self.design_id.col_height
            self.barcode_field = self.design_id.barcode_field

    @api.onchange('dpi')
    def onchange_dpi(self):
        if self.dpi < 80:
            self.dpi = 80

    @api.onchange('col_width', 'col_height')
    def onchange_col_size(self):
        if self.col_height and self.col_width:
            if self.format != 'custom':
                format_size = paper_format_dict.get(self.format)
                if format_size:
                    total_col = format_size[0] / self.col_width
                    self.col_no = int(total_col)
                    # self.col_no_float = total_col
            else:
                total_col = self.page_width / self.col_width
                self.col_no = int(total_col)
                # self.col_no_float = total_col

    @api.model
    def _get_barcode_field(self):
        field_list = []
        ir_model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
        if ir_model_id:
            for field in self.env['ir.model.fields'].search(
                    [('field_description', '!=', 'unknown'), ('model_id', '=', ir_model_id.id),
                     ('ttype', '=', 'char')]):
                field_list.append((field.name, field.field_description))
        return field_list

    def valid_barcode(self, barcode):
        if len(barcode) == 13:
            return ean.is_valid(barcode)
        elif len(barcode) == 12:
            hashlist = list(barcode)
            hashlist.insert(0, '0')
            number = ''.join(hashlist)
            return ean.is_valid(number)

    @api.onchange('scan')
    def add_product_via_scan(self):
        if self.scan:
            domain = [('barcode', '=', self.scan)]
            product_obj = self.env['product.product'].search(domain, limit=1)

            line_list = []
            flag = 0
            if product_obj:
                for record in self.product_ids:
                    if record.product_id.id == product_obj.id:
                        record.qty += 1
                        flag = 1
                    line_list.append((4, record.id))

                if not flag:
                    vals = {'product_id': product_obj.id,
                            'qty': 1,
                            }

                    line_list.append((0, 0, vals))
                self.product_ids = line_list
                self.scan = ''
            else:
                self.scan = ''
                raise UserError(_('Unknown Barcode OR Product can not be purchase!!'))

    scan = fields.Char('Scan')

    design_id = fields.Many2one('product.page.label.design', string="Template")
    product_ids = fields.One2many('product.page.label.qty', 'prod_small_wiz_id', string='Product List')
    page_width = fields.Integer(string='Page Width (mm)', default=60)
    page_height = fields.Integer(string='Page Height (mm)', default=30)
    dpi = fields.Integer(string='DPI', default=90, help="The number of individual dots \
                        that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=0)
    margin_left = fields.Integer(string='Margin Left (mm)', default=0)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=0)
    margin_right = fields.Integer(string='Margin Right (mm)', default=0)
    orientation = fields.Selection([('Landscape', 'Landscape'),
                                    ('Portrait', 'Portrait')],
                                   string='Orientation', default='Portrait', required=True)
    # barcode input
    barcode_type = fields.Selection([('Codabar', 'Codabar'), ('Code11', 'Code11'),
                                     ('Code128', 'Code128'), ('EAN13', 'EAN13'),
                                     ('Extended39', 'Extended39'), ('EAN8', 'EAN8'),
                                     ('Extended93', 'Extended93'), ('USPS_4State', 'USPS_4State'),
                                     ('I2of5', 'I2of5'), ('UPCA', 'UPCA'),
                                     ('QR', 'QR')],
                                    string='Type', default='EAN13', required=True)
    humanReadable = fields.Boolean(string="HumanReadable", help="User wants to print barcode number \
                                    with barcode label.")
    barcode_height = fields.Integer(string="Height", default=300, required=True,
                                    help="This height will required for the clearity of the barcode.")
    barcode_width = fields.Integer(string="Width", default=1500, required=True,
                                   help="This width will required for the clearity of the barcode.")
    display_height = fields.Integer(string="Display Height (px)", required=True, default=40,
                                    help="This height will required for display barcode in page label.")
    display_width = fields.Integer(string="Display Width (px)", required=True, default=200,
                                   help="This width will required for display barcode in page label.")
    # report design
    view_id = fields.Many2one('ir.ui.view', string='Report View', default=_get_page_report_id)
    paper_format_id = fields.Many2one('report.paperformat', string="Paper Format", default=_get_report_paperformat_id)
    with_barcode = fields.Boolean(string='Barcode', help="Click this check box if user want to\
                        print barcode for Product Page Label.", default=True)
    # new columns and rows fields
    format = fields.Selection([('A0', 'A0  5   841 x 1189 mm'),
                               ('A1', 'A1  6   594 x 841 mm'),
                               ('A2', 'A2  7   420 x 594 mm'),
                               ('A3', 'A3  8   297 x 420 mm'),
                               ('A4', 'A4  0   210 x 297 mm, 8.26 x 11.69 inches'),
                               ('A5', 'A5  9   148 x 210 mm'),
                               ('A6', 'A6  10  105 x 148 mm'),
                               ('A7', 'A7  11  74 x 105 mm'),
                               ('A8', 'A8  12  52 x 74 mm'),
                               ('A9', 'A9  13  37 x 52 mm'),
                               ('B0', 'B0  14  1000 x 1414 mm'),
                               ('B1', 'B1  15  707 x 1000 mm'),
                               ('B2', 'B2  17  500 x 707 mm'),
                               ('B3', 'B3  18  353 x 500 mm'),
                               ('B4', 'B4  19  250 x 353 mm'),
                               ('B5', 'B5  1   176 x 250 mm, 6.93 x 9.84 inches'),
                               ('B6', 'B6  20  125 x 176 mm'),
                               ('B7', 'B7  21  88 x 125 mm'),
                               ('B8', 'B8  22  62 x 88 mm'),
                               ('B9', 'B9  23  33 x 62 mm'),
                               ('B10', ':B10    16  31 x 44 mm'),
                               ('C5E', 'C5E 24  163 x 229 mm'),
                               ('Comm10E', 'Comm10E 25  105 x 241 mm, U.S. '
                                           'Common 10 Envelope'),
                               ('DLE', 'DLE 26 110 x 220 mm'),
                               ('Executive', 'Executive 4   7.5 x 10 inches, '
                                             '190.5 x 254 mm'),
                               ('Folio', 'Folio 27  210 x 330 mm'),
                               ('Ledger', 'Ledger  28  431.8 x 279.4 mm'),
                               ('Legal', 'Legal    3   8.5 x 14 inches, '
                                         '215.9 x 355.6 mm'),
                               ('Letter', 'Letter 2 8.5 x 11 inches, '
                                          '215.9 x 279.4 mm'),
                               ('Tabloid', 'Tabloid 29 279.4 x 431.8 mm'),
                               ('custom', 'Custom')],
                              string='Paper Type', default="custom",
                              help="Select Proper Paper size")
    col_no = fields.Integer('No. of Column',default=1)
    # col_no_float = fields.Float('No. of Column (float)', readonly=True, help="Column Size without Rounding.")
    col_width = fields.Float('Column Width (mm)', default=50.0)
    col_height = fields.Float('Column Height (mm)', default=25.0)
    from_col = fields.Integer(string="Start Column", default=1)
    from_row = fields.Integer(string="Start Row", default=1)
    page_report_id = fields.Many2one('ir.ui.view', string='Page Report View', default=_get_page_report_id)
    column_report_design = fields.Text(string="Report Design", default=_get_page_report_design)
    barcode_field = fields.Selection(related='design_id.barcode_field', string="Barcode Field")

    def action_print(self):
        if not self.product_ids:
            raise UserError('Please, select product(s) to print.')
        for product in self.product_ids:
            if product.qty <= 0:
                raise UserError('%s product page label qty should be greater then 0.!'
                              % (product.product_id.name))
            if self.with_barcode and not self.barcode_field:
                raise UserError('Please select barcode field to print barcode.')
            if not product.product_id.read([self.barcode_field]) and self.with_barcode:
                raise UserError(_('%s Product does not contain value that you trying to print!'
                                % (product.product_id.name)))
        if (self.format == 'custom') and ((self.page_height <= 0) or (self.page_width <= 0)):
            raise UserError(_('You can not give page width and page height to zero(0).'))
        if (self.margin_top < 0) or (self.margin_left < 0) or \
                (self.margin_bottom < 0) or (self.margin_right < 0):
            raise UserError('Margin Value(s) for report can not be negative!')
        if (self.col_no <= 0):
            raise UserError(_('Minimun 1 column Required to print page labels in page.'))
        # for page
        if (self.col_height <= 0) or (self.col_width <= 0):
            raise UserError(_('Give proper hight and width for page column.'))
        if (self.from_col <= 0) or (self.from_row <= 0):
            raise UserError(_('Start row and column position should be 1 or greater.'))
        if self.from_col > self.col_no:
            raise UserError(_('Start column position can not be greater than no. of column.'))
        if self.with_barcode and (self.barcode_height <= 0 or self.barcode_width <= 0 or
                                  self.display_height <= 0 or self.display_width <= 0):
            raise UserError(_('Give proper barcode height and width values for display.'))
        data = self.read()[0]
        datas = {
            'ids': self._ids,
            'model': 'wizard.product.page.report',
            'form': data
        }
        ctx = {
            'dynamic_size': True,
            'data': data
        }
        if self.page_report_id and self.column_report_design:
            self.page_report_id.write({'arch': self.column_report_design})
        if self.paper_format_id:
            if self.format == 'custom':
                self.paper_format_id.write({
                    'format': self.format,
                    'page_width': self.page_width,
                    'page_height': self.page_height,
                    'orientation': self.orientation,
                    'margin_top': self.margin_top,
                    'margin_left': self.margin_left,
                    'margin_bottom': self.margin_bottom,
                    'margin_right': self.margin_right,
                    'dpi': self.dpi
                })
            else:
                self.paper_format_id.write({
                    'format': self.format,
                    'page_width': 0,
                    'page_height': 0,
                    'orientation': self.orientation,
                    'margin_top': self.margin_top,
                    'margin_left': self.margin_left,
                    'margin_bottom': self.margin_bottom,
                    'margin_right': self.margin_right,
                    'dpi': self.dpi
                })
        return self.env.ref('dynamic_label.action_report_dynamic_report').report_action(self, data=datas)

    def save_design(self):
        # Odoo 19: Use self.env.ref() instead of get_object_reference
        view = self.env.ref('dynamic_label.wizard_page_label_design_form_view')
        return {
            'name': _('Product Page Label Design'),
            'view_mode': 'form',
            'res_model': 'product.page.label.design',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': view.id,
            'context': {'wiz_id': self.id},
        }
