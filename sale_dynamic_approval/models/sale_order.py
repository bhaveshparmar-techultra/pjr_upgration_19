""" inherit sale.order """
from odoo import _, models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'dynamic.approval.mixin']
    _not_matched_action_xml_id = 'sale_dynamic_approval.confirm_sale_order_wizard_action'

    state = fields.Selection(
        selection_add=[('under_approval', 'Under Approval'), ('approved', 'Approved'), ('sale',)])
    is_zero_amount = fields.Boolean(compute="get_zero_amount")

    @api.depends('order_line')
    def get_zero_amount(self):
        for rec in self:
            if not rec.amount_total:
                rec.is_zero_amount = True
            else:
                rec.is_zero_amount = False

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        self.remove_approval_requests()
        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def action_confirm(self):
        """ override to restrict user to confirm if there is workflow """
        res = super(SaleOrder, self).action_confirm()
        if self.mapped('dynamic_approve_request_ids') and \
                self.mapped('dynamic_approve_request_ids').filtered(lambda request: request.status != 'approved'):
            raise UserError(
                _('You can not confirm order, There are pending approval.'))
        for record in self:
            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback()
        return res

    def action_dynamic_approval_request(self):
        """" override to restrict request approval """
        res = super(SaleOrder, self).action_dynamic_approval_request()
        for record in self:
            if not record.order_line:
                raise UserError(_('Please add product in order to request approval'))
        return res

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        if self.state not in {'draft', 'sent','approved'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
            not line.display_type
            and not line.is_downpayment
            and not line.product_id
            for line in self.order_line
        ):
            return _("Some order lines are missing a product, you need to correct them before going further.")

        return False
