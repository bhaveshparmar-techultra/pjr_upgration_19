from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):
        """
        override globale create method to set company_id by active company
        for all models that inherit from base
        """
        model_name = self._name
        for val in vals_list:
          if 'company_id' in self.env[model_name]._fields and not val.get('company_id'):
              val['company_id'] = self.env.company.id
        record = super().create(vals_list)
        return record
