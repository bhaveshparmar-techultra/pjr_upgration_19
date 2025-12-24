""" inherit purchase.order """
from odoo import _, models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'dynamic.approval.mixin']
    _not_matched_action_xml_id = 'purchase_order_dynamic_approval.confirm_purchase_order_wizard_action'

    state = fields.Selection(
        selection_add=[('under_approval', 'Under Approval'), ('approved', 'Approved')])

    is_zero_amount = fields.Boolean(compute="get_zero_amount")

    @api.depends('order_line')
    def get_zero_amount(self):
        for rec in self:
            if not rec.amount_total:
                rec.is_zero_amount = True
            else:
                rec.is_zero_amount = False

    def button_draft(self):
        res = super(PurchaseOrder, self).button_draft()
        self.remove_approval_requests()
        return res

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def _button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'approved']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def button_confirm(self):
        """ override to restrict user to confirm if there is workflow """
        res = self._button_confirm()
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
        res = super(PurchaseOrder, self).action_dynamic_approval_request()
        for record in self:
            if not record.order_line:
                raise UserError(_('Please add product in order to request approval'))
        return res
