# Copyright 2017 ForgeFlow S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    """
    Fetches all the sale order and resets the sequence of the order lines

    Note: In Odoo 17+, post_init_hook receives env directly instead of (cr, registry)
    """
    sale = env["sale.order"].search([])
    sale._reset_sequence()
