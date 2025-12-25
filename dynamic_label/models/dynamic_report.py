# -*- coding: utf-8 -*-
from odoo import models, api, _
from reportlab.graphics.barcode import createBarcodeDrawing
from base64 import b64encode
import math
from reportlab.graphics import barcode
from odoo.exceptions import ValidationError
from binascii import hexlify
from markupsafe import Markup



class dynamic_report_temp(models.AbstractModel):
    _name = 'report.dynamic_label.dynamic_report_temp'
    _description = 'Dynamic Report Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('dynamic_label.dynamic_report_temp').with_context(
            {'lang': self.env.user.lang})
        docargs = {
            'doc_ids': self.env["wizard.product.page.report"].browse(data["ids"]).with_context(
                {'lang': self.env.user.lang}),
            # 'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'draw_table': self._draw_table,
            'get_barcode': self._get_barcode,
            'draw_style': self._draw_style,
            'data': data
        }
        if data['form']['with_barcode'] and data['form']['barcode_field']:
            for product in self.env['product.page.label.qty'].browse(data['form']['product_ids']):
                width = int(data['form']['barcode_height'])
                height = int(data['form']['barcode_width'])
                barcode_field = product.product_id.read([str(data['form']['barcode_field'])])
                if barcode_field:
                    barcode_field = barcode_field[0].get(str(data['form']['barcode_field']))
                    if not barcode_field:
                        raise ValidationError(
                            'Select valid barcode type according barcode field value or check barcode value !')
                try:
                     createBarcodeDrawing(
                        data['form']['barcode_type'], value=barcode_field, format='png', width=width, height=height,
                        humanReadable=data['form']['humanReadable'])
                except:
                    raise ValidationError('Select valid barcode type according barcode field value !')
        return docargs
        # return report_obj.render('dynamic_label.dynamic_report_temp', docargs)

    def _draw_style(self, data):
        return 'width:' + str(data['form']['col_width']) + 'mm !important;height:' + str(data['form'][
                                                                                             'col_height']) + 'mm !important; margin: 0px 0px 0px 0px; padding: 0px; overflow: hidden !important; text-overflow: ellipsis !important;'

    def get_cell_number(self, from_row, from_col, col_no):
        return ((from_row - 1) * col_no + from_col - 1)

    def _draw_table(self, data):
        design = self.env['product.page.label.design'].browse(data['form']['design_id'][0])
        product_list = []
        if data['form']['product_ids']:
            cell_no = self.get_cell_number(data['form']['from_row'], data['form']['from_col'],
                                           int(data['form']['col_no']))
            box_needed = int(cell_no) or 0
            for product_data in self.env['product.page.label.qty'].browse(data['form']['product_ids']):
                if product_data.product_id:
                    box_needed += int(product_data.qty)
                    product_list.append(product_data)
            cell_record = self.create_list(product_list, int(cell_no))
            _table = self.create_table(box_needed, cell_record, data)
            return _table

    def _get_barcode(self, product, barcode, data):
        barcode_str = ''
        if data['form']['with_barcode']:
            barcode_value = product.read([barcode])
            if barcode_value:
                barcode_value = barcode_value[0].get(barcode)
            barcode_drawing = createBarcodeDrawing(
                data['form']['barcode_type'], value=barcode_value, format='png',
                width=int(data['form']['barcode_height']),
                height=int(data['form']['barcode_width']), humanReadable=data['form']['humanReadable'])
            barcode_png = barcode_drawing.asString('png')
            # Use Markup to mark HTML as safe for t-out rendering in Odoo 19
            barcode_str = Markup("<img style='width:{width}px;height:{height}px;' src='data:image/png;base64,{b64}'/>".format(
                width=data['form']['display_width'],
                height=data['form']['display_height'],
                b64=b64encode(barcode_png).decode('utf-8')
            ))
        return barcode_str

    def create_list(self, products, cell_no):
        product_data = {}
        for prod in products:
            if prod.product_id:
                for qty in range(0, int(prod.qty)):
                    product_data.update({cell_no: {'product_id': prod.product_id}})
                    cell_no += 1
        return product_data

    def create_table(self, box_needed, cell_record, data):
        no_of_col = int(data['form']['col_no'])
        product_table = []
        for tr_no in range(1, int(math.ceil(float(box_needed) / no_of_col + 1))):
            product_dict = {}
            for td_no in range(1, no_of_col + 1):
                cellno = self.get_cell_number(tr_no, td_no, no_of_col)
                if cell_record.get(cellno):
                    product_id = cell_record.get(cellno).get('product_id')
                    if product_dict.get(tr_no):
                        product_dict[tr_no].append(product_id)
                    else:
                        product_dict[tr_no] = [product_id]
                else:
                    if product_dict.get(tr_no):
                        product_dict[tr_no].append(False)
                    else:
                        product_dict[tr_no] = [False]
            product_table.append(product_dict)
        return product_table
