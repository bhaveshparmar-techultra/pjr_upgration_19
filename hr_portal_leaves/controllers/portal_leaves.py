import datetime
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.fields import Domain
import base64


class PortalEmployeeLeaves(portal.CustomerPortal):
    """Display user counters"""

    def _prepare_home_portal_values(self, counters):
        """Display counters of payslips"""
        values = super()._prepare_home_portal_values(counters)
        if "leaves_count" in counters:
            leaves_count = (
                request.env["hr.leave"]
                .sudo()
                .search_count(
                    [
                        (
                            "employee_id.user_id",
                            "=",
                            request.env.user.id,
                        )
                    ]
                )
            )

            time_off_approval_activity_type_id = request.env.ref(
                "hr_holidays.mail_act_leave_approval"
            )
            time_off_approval2_activity_type_id = request.env.ref(
                "hr_holidays.mail_act_leave_second_approval"
            )

            approvals_count = (
                request.env["mail.activity"]
                .sudo()
                .search_count(
                    [
                        ("user_id", "=", request.env.user.id),
                        ("res_model", "=", "hr.leave"),
                        (
                            "activity_type_id",
                            "in",
                            (
                                time_off_approval_activity_type_id.id,
                                time_off_approval2_activity_type_id.id,
                            ),
                        ),
                    ]
                )
            )

            values["leaves_count"] = leaves_count + approvals_count

        if "allocation_count" in counters:
            values["allocation_count"] = (
                request.env["hr.leave.allocation"]
                .sudo()
                .search_count([("employee_id.user_id", "=", request.env.user.id)])
            )

        return values

    @http.route(
        ["/my/leaves", "/my/leaves/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_leaves(self, page=1, sortby=None, search="", search_in="All"):
        """Display current user leaves"""
        searchbar_sortings = {
            "request_date_from": {"label": "Date", "order": "request_date_from desc"},
            "holiday_status_id": {"label": "Type", "order": "holiday_status_id"},
            "create_date": {"label": "Created On", "order": "create_date desc"},
        }
        searchbar_inputs = {
            "All": {
                "label": "All",
                "input": "All",
                "domain": [
                    "|",
                    "|",
                    ("name", "ilike", search),
                    ("notes", "ilike", search),
                    ("holiday_status_id", "ilike", search),
                ],
            },
            "Leave Type": {
                "label": "Leave Type",
                "input": "Leave Type",
                "domain": [("holiday_status_id", "ilike", search)],
            },
            "Current Year": {
                "label": "Current Year",
                "input": "Current Year",
                "domain": [
                    (
                        "request_date_from",
                        ">=",
                        datetime.date.today().replace(month=1, day=1),
                    ),
                    (
                        "request_date_from",
                        "<=",
                        datetime.date.today().replace(month=12, day=31),
                    ),
                ],
            },
            "Current Month": {
                "label": "Current Month",
                "input": "Current Month",
                "domain": [
                    ("request_date_from", ">=", datetime.date.today().replace(day=1)),
                    ("request_date_from", "<=", datetime.date.today().replace(day=29)),
                ],
            },
        }
        if not sortby:
            sortby = "create_date"

        order = searchbar_sortings[sortby]["order"]

        domain = [("employee_id.user_id", "=", request.env.user.id)]
        search_domain = searchbar_inputs[search_in]["domain"]
        domain = Domain.AND([domain, search_domain])

        leaves_count = request.env["hr.leave"].sudo().search_count(domain)

        pager = portal_pager(
            url="/my/leaves",
            url_args={"sortby": sortby, "search_in": search_in, "search": search},
            total=leaves_count,
            page=page,
            step=5,
        )

        leave_ids = (
            request.env["hr.leave"]
            .sudo()
            .search(
                domain,
                order=order,
                limit=5,
                offset=pager["offset"],
            )
        )

        # the best way and more efficient is to fetch the pending activity on the hr.leave.

        time_off_approval_activity_type_id = request.env.ref(
            "hr_holidays.mail_act_leave_approval"
        )
        time_off_approval2_activity_type_id = request.env.ref(
            "hr_holidays.mail_act_leave_second_approval"
        )

        to_approve_leave_activity_ids = (
            request.env["mail.activity"]
            .sudo()
            .search(
                [
                    ("user_id", "=", request.env.user.id),
                    ("res_model", "=", "hr.leave"),
                    (
                        "activity_type_id",
                        "in",
                        (
                            time_off_approval_activity_type_id.id,
                            time_off_approval2_activity_type_id.id,
                        ),
                    ),
                ]
            )
        ).mapped("res_id")

        to_approve_leave_ids = (
            request.env["hr.leave"].sudo().browse(to_approve_leave_activity_ids)
        )

        holidays = (
            request.env["hr.leave.type"]
            .with_context(employee_id=request.env.user.employee_id.id)
            .sudo()
            .get_allocation_data_request()
        )
        approved_leave_ids_domain = [
            "&",
            ("user_id", "!=", request.env.user.id),
            ("state", "=", "validate"),
            "|",
            "|",
            ("first_approver_id.user_id", "=", request.env.user.id),
            ("second_approver_id.user_id", "=", request.env.user.id),
            ("employee_id.parent_id.user_id", "=", request.env.user.id),
        ]
        approved_leave_ids_count = (
            request.env["hr.leave"].sudo().search_count(approved_leave_ids_domain)
        )
        approved_pager = portal_pager(
            url="/my/leaves",
            url_args={"sortby": sortby, "search_in": search_in, "search": search},
            total=approved_leave_ids_count,
            page=page,
            step=5,
        )
        approved_leave_ids = (
            request.env["hr.leave"]
            .sudo()
            .search(
                approved_leave_ids_domain,
                limit=10,
                offset=approved_pager["offset"],
                order=searchbar_sortings[sortby]["order"],
            )
        )
        return http.request.render(
            "hr_portal_leaves.portal_employee_leaves",
            {
                "leave_ids": leave_ids,
                "employeeId": request.env.user.employee_id.id,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
                "sortby": sortby,
                "search": search,
                "search_in": search_in,
                "page_name": "leave",
                "holidays": holidays,
                "to_approve_leave_ids": to_approve_leave_ids,
                "approved_leave_ids": approved_leave_ids,
                "pager_history": pager,
                "approved_pager": approved_pager,
            },
        )

    @http.route(
        ["/leave/details/<int:leave_id>"], type="http", auth="public", website=True
    )
    def portal_my_leave_detail(
        self,
        leave_id,
        access_token=None,
        report_type=None,
        download=False,
        **kw,
    ):

        leave_sudo = request.env["hr.leave"].sudo().browse(leave_id)

        return http.request.render(
            "hr_portal_leaves.hr_leave_content",
            {
                "leave": leave_sudo,
                "object": leave_sudo,
                "page_name": "leave_details",
                "is_manager": leave_sudo.employee_id.parent_id
                == request.env.user.sudo().employee_id,
            },
        )

    @http.route(["/new/leave"], type="http", auth="public", website=True)
    def post_new_leave(self, **kw):
        holiday_status_ids = (
            request.env["hr.leave.type"]
            .sudo()
            .search(
                [
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", request.env.company.id),
                ]
            )
            .with_context(employee_id=request.env.user.employee_id.id)
        )
        # Odoo 19: name_get() is deprecated, use display_name instead
        holiday_status_list = [(h.id, h.display_name) for h in holiday_status_ids]

        return http.request.render(
            "hr_portal_leaves.leave_request_form_view",
            {"holiday_status_ids": holiday_status_list},
        )

    @http.route(
        ["/submit/leave"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=False,
    )
    def submit_new_leave(self, **kw):

        def _prepare_leave_values():

            values = kw.copy()
            if "csrf_token" in values:
                del values["csrf_token"]

            if "Text1" in values:
                values["name"] = values["Text1"]
                del values["Text1"]

            values["employee_id"] = request.env.user.employee_id.id
            values["holiday_status_id"] = int(values["holiday_status_id"])

            return values

        attachment_ids = request.httprequest.files.getlist("attachment_ids")
        vals = _prepare_leave_values()
        vals.pop("attachment_ids")
        leave_new = (
            request.env["hr.leave"]
            .sudo()
            .with_context(employee_id=request.env.user.employee_id.id)
            .new(vals)
        )

        leave_new._compute_date_from_to()
        leave_vals = leave_new._convert_to_write(leave_new._cache)
        leave_sudo = (
            request.env["hr.leave"]
            .sudo()
            .with_context(employee_id=request.env.user.employee_id.id)
            .create(leave_vals)
        )

        for file in attachment_ids:
            request.env["ir.attachment"].sudo().create(
                {
                    "name": file.filename,
                    "type": "binary",
                    "datas": base64.encodebytes(file.read()),
                    "res_model": "hr.leave",
                    "res_id": leave_sudo.id,
                }
            )

        return request.redirect(
            "/leave/details/%s" % (leave_sudo.id),
        )

    @http.route(
        "/leave/refuse/<int:leave_id>",
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def hr_holidays_request_refuse(self, leave_id):
        leave_sudo = request.env["hr.leave"].sudo().browse(leave_id)
        leave_sudo.action_refuse()
        if leave_sudo.employee_id.parent_id == request.env.user.sudo().employee_id:
            return http.request.render(
                "hr_portal_leaves.hr_leave_content",
                {
                    "leave": leave_sudo,
                    "object": leave_sudo,
                    "page_name": "leave_details",
                    "is_manager": False,
                },
            )

        return request.redirect("/my/leaves")

    @http.route(
        "/leave/approve/<int:leave_id>",
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def hr_holidays_request_approve(self, leave_id):
        leave_sudo = request.env["hr.leave"].sudo().browse(leave_id)
        leave_sudo.action_approve()

        if leave_sudo.employee_id.parent_id == request.env.user.sudo().employee_id:
            return http.request.render(
                "hr_portal_leaves.hr_leave_content",
                {
                    "leave": leave_sudo,
                    "object": leave_sudo,
                    "page_name": "leave_details",
                    "is_manager": False,
                },
            )

        return request.redirect("/my/leaves")
