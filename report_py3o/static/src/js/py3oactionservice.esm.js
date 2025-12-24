/** @odoo-module **/

import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {user} from "@web/core/user";

registry
    .category("ir.actions.report handlers")
    .add("py3o_handler", async function (action, options, env) {
        if (action.report_type === "py3o") {
            let url = `/report/py3o/${action.report_name}`;
            const actionContext = action.context || {};
            // Odoo 19: Use native JavaScript instead of underscore.js
            const isDataEmpty = (
                action.data === undefined ||
                action.data === null ||
                (typeof action.data === "object" && Object.keys(action.data).length === 0)
            );
            if (isDataEmpty) {
                // Build a query string with `action.data` (it's the place where reports
                // using a wizard to customize the output traditionally put their options)
                if (actionContext.active_ids) {
                    var activeIDsPath = "/" + actionContext.active_ids.join(",");
                    url += activeIDsPath;
                }
            } else {
                var serializedOptionsPath =
                    "?options=" + encodeURIComponent(JSON.stringify(action.data));
                serializedOptionsPath +=
                    "&context=" + encodeURIComponent(JSON.stringify(actionContext));
                url += serializedOptionsPath;
            }
            env.services.ui.block();
            try {
                await download({
                    url: "/report/download",
                    data: {
                        data: JSON.stringify([url, action.report_type]),
                        context: JSON.stringify(user.context),
                    },
                });
            } finally {
                env.services.ui.unblock();
            }
            const onClose = options.onClose;
            if (action.close_on_report_download) {
                return env.services.action.doAction(
                    {type: "ir.actions.act_window_close"},
                    {onClose}
                );
            } else if (onClose) {
                onClose();
            }
            return Promise.resolve(true);
        }
        return Promise.resolve(false);
    });
