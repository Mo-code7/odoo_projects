from odoo import models, fields, api

class ItemExchange(models.Model):
    _name = 'item.exchange'
    _description = 'بورصة الأصناف'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('product.category', string='الاسم')
    price = fields.Float(string='السعر البيع (للطن)', compute='_compute_last_values', store=True)
    last_price = fields.Float(string='اقل سعر بيع', compute='_compute_last_values', store=True)
    product_tmpl_id = fields.Many2one('product.template')

    line_ids = fields.One2many('item.exchange.lines', 'exchange_id', string='بنود البورصة')

    @api.depends('line_ids.price', 'line_ids.last_price', 'line_ids.date')
    def _compute_last_values(self):
        for rec in self:
            last_line = self.env['item.exchange.lines'].search(
                [('exchange_id', '=', rec.id)],
                order='date desc, id desc',
                limit=1
            )
            rec.price = last_line.price if last_line else 0.0
            rec.last_price = last_line.last_price if last_line else 0.0

    def write(self, vals):
        res = super(ItemExchange, self).write(vals)
        if 'price' in vals or 'last_price' in vals:
            self._update_related_products()
        return res

    def _update_related_products(self):
        """تحديث جميع المنتجات التي تنتمي للفئة المختارة"""
        for rec in self:
            if rec.name:
                products = self.env['product.template'].search([('categ_id', '=', rec.name.id)])
                if products:
                    # استدعاء دالة الحساب في المنتجات لتحديث الأسعار بناءً على القيم الجديدة في البورصة
                    products._compute_exchange_price()
        return True


class ItemExchangeLines(models.Model):
    _name = 'item.exchange.lines'
    _description = 'بنود بورصة الأصناف'

    exchange_id = fields.Many2one('item.exchange', string='البورصة')
    date = fields.Date(string='تاريخ', default=fields.Date.context_today)
    price = fields.Float(string='سعر البيع ')
    last_price = fields.Float(string='اخر سعر بيع')

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(ItemExchangeLines, self).create(vals_list)
        for line in lines:
            line.exchange_id._update_related_products()
        return lines

    def write(self, vals):
        res = super(ItemExchangeLines, self).write(vals)
        if 'price' in vals or 'last_price' in vals or 'date' in vals:
            for line in self:
                line.exchange_id._update_related_products()
        return res