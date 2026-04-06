from odoo import models, fields, api
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        # Add stock and cost fields to POS data
        fields += ['qty_available', 'virtual_available', 'standard_price', 'weight','volume']
        return fields



