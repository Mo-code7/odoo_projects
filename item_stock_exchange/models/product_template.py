from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    exchange_price = fields.Float(
        string='سعر البيع (للطن)',
        compute='_compute_exchange_price',
        store=True
    )

    exchange_last_price = fields.Float(
        string='اقل سعر بيع (للطن)',
        compute='_compute_exchange_price',
        store=True
    )

    static_model = fields.Float(string='الوزن الثابت', default=1.0)

    min_sale_price = fields.Float(
        string='اقل سعر بيع',
        compute='_compute_exchange_price',
        store=True
    )

    @api.depends('categ_id', 'static_model')
    def _compute_exchange_price(self):
        # البحث عن جميع سجلات البورصة وربطها بمعرف الفئة
        exchanges = {
            ex.name.id: ex
            for ex in self.env['item.exchange'].search([])
        }

        for product in self:
            # الحصول على سجل البورصة المرتبط بفئة المنتج
            ex = exchanges.get(product.categ_id.id)

            price_ton = ex.price if ex else 0.0
            last_price_ton = ex.last_price if ex else 0.0

            product.exchange_price = price_ton
            product.exchange_last_price = last_price_ton

            # التحويل من طن لكيلو (بافتراض أن السعر للطن والوزن الثابت بالكيلو)
            price_per_kg = price_ton / 1000.0
            last_price_per_kg = last_price_ton / 1000.0

            # الضرب في الوزن الثابت للحصول على سعر الوحدة
            final_price = price_per_kg * product.static_model
            final_last_price = last_price_per_kg * product.static_model

            # تحديث سعر البيع الرسمي وأقل سعر بيع
            product.list_price = final_price
            product.min_sale_price = final_last_price