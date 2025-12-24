from odoo import _, api, fields, models


class ResCompanyImage(models.Model):
    _name = 'res.company.image'
    _rec_name = 'name'
    _description = 'Company Image'

    name = fields.Char(string='Name', required=True)
    image = fields.Binary(string='Image', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
    )
