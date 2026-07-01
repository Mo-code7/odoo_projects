# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class RestaurantSaleReport(models.Model):
    _name = 'restaurant.sale.report'
    _description = 'تقرير مبيعات المطعم'
    _auto = False
    _order = 'order_date desc'

    order_date      = fields.Date(string='التاريخ', readonly=True)
    partner_id      = fields.Many2one('res.partner', string='العميل', readonly=True)
    order_type      = fields.Selection([
        ('dine_in',  'داخل المطعم'),
        ('takeaway', 'تيك أواي'),
        ('delivery', 'توصيل'),
    ], string='نوع الطلب', readonly=True)
    product_id      = fields.Many2one('product.product', string='الصنف', readonly=True)
    product_qty     = fields.Float(string='الكمية', readonly=True)
    price_subtotal  = fields.Float(string='الإجمالي', readonly=True)
    payment_status  = fields.Selection([
        ('pending',  'في الانتظار'),
        ('success',  'ناجح'),
        ('failed',   'فاشل'),
        ('refunded', 'مسترجع'),
    ], string='حالة الدفع', readonly=True)
    order_count     = fields.Integer(string='عدد الطلبات', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER ()            AS id,
                    ro.create_date::DATE            AS order_date,
                    ro.partner_id,
                    ro.order_type,
                    ro.payment_status,
                    rol.product_id,
                    SUM(rol.product_qty)            AS product_qty,
                    SUM(rol.price_subtotal)         AS price_subtotal,
                    COUNT(DISTINCT ro.id)           AS order_count
                FROM restaurant_order ro
                JOIN restaurant_order_line rol ON rol.order_id = ro.id
                WHERE ro.state NOT IN ('cancel', 'draft')
                GROUP BY
                    ro.create_date::DATE,
                    ro.partner_id,
                    ro.order_type,
                    ro.payment_status,
                    rol.product_id
            )
        """ % self._table)
