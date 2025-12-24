
from odoo import  fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    overtime_calculation = fields.Boolean(string="Overtime Calculation")
    regular_overtime_rate = fields.Float(string="Regular Overtime Rate")
    public_holiday_overtime_rate = fields.Float(string="Public Holiday Overtime Rate")
    weekend_overtime_rate = fields.Float(string="Weekend Overtime Rate")
