from odoo.addons.portal.controllers import portal_thread
from odoo import http
from odoo.http import request


class PortalChatter(portal_thread.PortalChatter):
    """Extend portal chatter for HR Leaves"""

    @http.route()
    def portal_chatter_post(
        self,
        thread_model,
        thread_id,
        body,
        attachment_ids=None,
        attachment_tokens=None,
        **kwargs
    ):
        return super(PortalChatter, self).portal_chatter_post(
            thread_model,
            thread_id,
            body,
            attachment_ids=attachment_ids,
            attachment_tokens=attachment_tokens,
            **kwargs
        )
