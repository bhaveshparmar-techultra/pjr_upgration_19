from odoo import api, fields, models, _
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for rec in self:
            if rec.picking_type_id.code == 'internal':
                for line in rec.move_line_ids:
                    if line.location_dest_id.id != rec.location_dest_id.id:
                        raise UserError(_("Please Make To Location In Lines As Destination Location!."))
            elif rec.picking_type_id.code == 'outgoing':
                for line in rec.move_line_ids:
                    if line.location_id.id != rec.location_id.id:
                        raise UserError(_("Please Make FROM Location In Lines As SOURCE Location!."))
        return super(StockPicking, self).button_validate()
