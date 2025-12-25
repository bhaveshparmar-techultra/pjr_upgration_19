from odoo import models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def do_unreserve(self):
        """Override to restrict unreserve action based on group permission."""
        if not self.env.user.has_group('group_unreserve.group_unreserve'):
            raise UserError(_('You do not have permission to unreserve. Please contact your administrator.'))
        return super().do_unreserve()