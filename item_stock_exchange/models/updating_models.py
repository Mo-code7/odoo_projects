from odoo import models, fields,api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    exchange_price = fields.Float(
        related='product_id.product_tmpl_id.exchange_price',
        string='سعر البيع (للطن)',
        store=True
    )

    exchange_last_price = fields.Float(
        related='product_id.product_tmpl_id.exchange_last_price',
        string='اقل سعر بيع (للطن)',
        store=True
    )

    static_model = fields.Float(
        related='product_id.product_tmpl_id.static_model',
        string='الوزن الثابت',
        store=True
    )

    min_sale_price = fields.Float(
        related='product_id.product_tmpl_id.min_sale_price',
        string='اقل سعر بيع',
        store=True
    )

    total_quantity = fields.Float(
        string='اجمالى الكمية',
        compute='_compute_total_quantity',
        store=True
    )
    
    qty_available = fields.Float(
        string="الكمية في اليد",
        compute="_compute_qty_available",
        store=False
    )

    @api.depends('product_id')
    def _compute_qty_available(self):
        for line in self:
            if line.product_id:
                line.qty_available = line.product_id.qty_available
            else:
                line.qty_available = 0.0

    @api.depends('product_uom_qty', 'static_model')
    def _compute_total_quantity(self):
        for line in self:
            # ضرب الكمية المطلوبة في الوزن الثابت للمنتج
            line.total_quantity = line.product_uom_qty * line.static_model


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cash_customer_id = fields.Many2one('res.partner', string='العميل النقدي')

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.cash_customer_id:
            invoice_vals['cash_customer_id'] = self.cash_customer_id.id
        return invoice_vals

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(SaleOrder, self).create(vals_list)
        for order in orders:
            if order.cash_customer_id:
                # تحديث أوامر التوصيل المرتبطة عند الإنشاء إذا كانت موجودة (حالة نادرة في الإنشاء المباشر)
                order.picking_ids.write({'cash_customer_id': order.cash_customer_id.id})
        return orders

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'cash_customer_id' in vals:
            # تحديث أوامر التوصيل والفواتير المرتبطة فوراً عند تعديل العميل النقدي
            for order in self:
                if order.picking_ids:
                    order.picking_ids.write({'cash_customer_id': vals.get('cash_customer_id')})
                if order.invoice_ids:
                    order.invoice_ids.write({'cash_customer_id': vals.get('cash_customer_id')})
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.cash_customer_id and order.picking_ids:
                order.picking_ids.write({'cash_customer_id': order.cash_customer_id.id})
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    cash_customer_id = fields.Many2one('res.partner', string='العميل النقدي')
    delivery_count = fields.Integer(string='عدد الشحنات', compute='_compute_delivery_count')

    def _compute_delivery_count(self):
        for move in self:
            # الحصول على أوامر التوصيل المرتبطة بأمر البيع الخاص بالفاتورة
            pickings = self.env['stock.picking'].search([('origin', '=', move.invoice_origin)]) if move.invoice_origin else self.env['stock.picking']
            move.delivery_count = len(pickings)

    def action_view_delivery(self):
        """فتح واجهة أوامر التوصيل المرتبطة بالفاتورة"""
        self.ensure_one()
        pickings = self.env['stock.picking'].search([('origin', '=', self.invoice_origin)]) if self.invoice_origin else self.env['stock.picking']
        
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = pickings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_validate_delivery(self):
        """تصديق (Validate) أوامر التوصيل المرتبطة بالفاتورة"""
        self.ensure_one()
        if not self.invoice_origin:
            raise UserError(_("لا يوجد أمر بيع مرتبط بهذه الفاتورة لتنفيذ عملية التسليم."))
            
        pickings = self.env['stock.picking'].search([
            ('origin', '=', self.invoice_origin),
            ('state', 'not in', ['done', 'cancel'])
        ])
        
        if not pickings:
            raise UserError(_("لا توجد شحنات معلقة (جاهزة) للتسليم مرتبطة بهذه الفاتورة."))

        for picking in pickings:
            # التأكد من توفر الكميات (Check Availability) إذا كانت في حالة 'confirmed'
            if picking.state == 'confirmed':
                picking.action_assign()
            
            # التحقق من اسم حقل الكمية (في الإصدارات القديمة quantity_done، وفي الجديدة quantity)
            for line in picking.move_ids:
                qty_to_set = line.product_uom_qty
                if hasattr(line, 'quantity'):
                    if line.quantity == 0:
                        line.quantity = qty_to_set
                elif hasattr(line, 'quantity_done'):
                    if line.quantity_done == 0:
                        line.quantity_done = qty_to_set
            
            picking.button_validate()
            
        return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cash_customer_id = fields.Many2one('res.partner', string='العميل النقدي')