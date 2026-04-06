from odoo import models, fields, api, _       
from datetime import date as dt_date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
# class HrPayslipLine(models.Model):
#     _inherit = 'hr.payslip.line'

#     # تعديل حقل code ليبقى مش مطلوب
#     code = fields.Char(string="Code", required=False)  
from datetime import date, timedelta  
import logging
_logger = logging.getLogger(__name__)

class AnimalBreeding(models.Model):
    _name = 'typesss' 
    _description = 'سلالات'
    des = fields.Char(string='الوصف')
    
    name = fields.Char(string='اسم السلالة')
    
    
class AnimalBreeding(models.Model):
    _name = 'animal.breeding'
    _description = 'عملية تكاثر'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    name = fields.Char(string='رقم العملية')
    counterpart_account_id = fields.Many2one(
        'account.account',
        string="الحساب المقابل",
        required=True
    )
    journal_id = fields.Many2one( 'account.journal',string="دفتر اليومية", required=True, domain="[('type','=','general')]")
    total_artificial = fields.Float(
        string="إجمالي مصروفات تلقيح صناعي",
        # compute="_compute_totals",
        store=True
    )
    total_mandatory = fields.Float(
        string="إجمالي مصروفات تلقيح إجباري",
        # compute="_compute_totals",
        store=True
    )
    line_ids = fields.One2many('animal.breeding.line', 'breeding_id', string="بنود المصروفات")  
    move_count = fields.Integer(string='عدد القيود', compute='_compute_move_count')

    def _compute_move_count(self):
        for rec in self:
            rec.move_count = sum(1 for line in rec.line_ids if line.move_id)
    def action_view_moves(self):
        self.ensure_one()  # تأكد إن العملية تتم على سجل واحد فقط
        move_ids = self.line_ids.mapped('move_id').ids  # جمع كل القيود المحاسبية المرتبطة
        return {
        'name': 'القيود المحاسبية',
        'type': 'ir.actions.act_window',
        'res_model': 'account.move',
        'view_mode': 'list,form',
        'domain': [('id', 'in', move_ids)],
        'target': 'current',
    }
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec._create_move_if_needed()
        return rec

    # عند تعديل سجل
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._create_move_if_needed()
        return res

    # إنشاء القيود المحاسبية لكل سطر
    def _create_move_if_needed(self):
        for rec in self:
            if not rec.line_ids or not rec.journal_id or not rec.counterpart_account_id:
                continue

            for line in rec.line_ids:
                if line.amount > 0 and not line.move_id:
                    move_vals = {
                        'journal_id': rec.journal_id.id,
                        'date': line.date or rec.date or fields.Date.context_today(self),
                        'ref': f"مصروفات تلقيح - {line.id}",
                        'line_ids': [
                            (0, 0, {
                                'account_id': line.account_id.id,
                                'name': "بند مصروف",
                                'debit': line.amount,
                                'credit': 0.0,
                                'x_studio_many2one_field_6m7_1ikhq2lqg': line.analytic_account_id.id if line.analytic_account_id else False,
                            }),
                            (0, 0, {
                                'account_id': rec.counterpart_account_id.id,
                                'name': "مقابل مصروف تلقيح",
                                'debit': 0.0,
                                'credit': line.amount,
                                'x_studio_many2one_field_6m7_1ikhq2lqg': line.analytic_account_id.id if line.analytic_account_id else False,
                            }),
                        ]
                    }
                    move = self.env['account.move'].create(move_vals)
                    move.action_post()
                    line.move_id = move.id
     
    female_id = fields.Many2one('livestock.animal', string='الأنثى', required=True, domain="[('gender','=','female')]", tracking=True)  
    male_id = fields.Many2one('livestock.animal', string='الذكر', domain="[('gender','=','male')]", tracking=True)
    
    date = fields.Date(string='تاريخ العملية', required=True, tracking=True)
    
    type = fields.Selection([('natural', 'تلقيح طبيعي'),('artificial', 'تلقيح اصطناعي')], string='نوع التلقيح', required=True,tracking=True)
                            
    state = fields.Selection([('pending', 'بانتظار'),('done', 'ناجح'),('failed', 'فشل')], string='النتيجة', default='pending', tracking=True)
    
    notes = fields.Text(string='ملاحظات')
    time_per = fields.Integer(string='فترة الحمل',compute='_compute_time_per')
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
    @api.depends('date')
    def _compute_time_per(self):
        today = dt_date.today()
        for rec in self:
            if rec.date:
                rec.time_per = (today - rec.date).days
            else:
                rec.time_per = 0
    @api.onchange('type')
    def _onchange_type(self):
            if self.type == 'artificial':
                self.male_id = False  # إفراغ الحقل
    def action_done(self):
        for rec in self:
          rec.state = 'done'
    def action_failed(self):
        for rec in self:
         rec.state = 'failed'  
class AnimalBreedingLine(models.Model):
    _name = "animal.breeding.line"
    _description = "Animal Breeding Line"

    breeding_id = fields.Many2one("animal.breeding", string="Breeding", ondelete="cascade")
    analytic_account_id = fields.Many2one(
    'account.analytic.account',
    string="الحساب التحليلي",
    required=True
)
    date= fields.Date(string='التاريخ',default=fields.Date.context_today)
    move_id = fields.Many2one('account.move', string="القيد المحاسبي")
    amount = fields.Float(string="المبلغ")

    account_id = fields.Many2one("account.account", string="Account", required=True)
class AnimalBirth(models.Model):
    _name = 'animal.birth'
    _description = 'ولادة'
    _rec_name = 'name'
    _order = 'birth_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(   string='اسم الولادة',compute='_compute_name',store=True )
    
    breeding_id = fields.Many2one('animal.breeding', string='عملية التكاثر',tracking=True )
    
    mother_id = fields.Many2one( related='breeding_id.female_id', string='الأم',required=True, tracking=True )
    
    father_id = fields.Many2one( related='breeding_id.male_id', string='الاب',tracking=True)

    birth_date = fields.Date(   string='تاريخ الولادة',   required=True,   default=fields.Date.today,   tracking=True)

    
    birth_time = fields.Datetime(    string='وقت الولادة',   tracking=True )
    
    birth_type = fields.Selection([   ('natural', 'طبيعية'),   ('assisted', 'بمساعدة'),   ('cesarean', 'قيصرية'),   ('difficult', 'متعسرة') ]
    , string='نوع الولادة', required=True, default='natural', tracking=True)
    
    number_born = fields.Integer(   string='عدد المواليد',compute='_compute_numbers',  default=1,  tracking=True )
    
    veterinarian = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    complications = fields.Text(string='المضاعفات',tracking=True )
    
    treatment_given = fields.Text(string='العلاج المقدم',tracking=True)
    
    cost = fields.Float(string='التكلفة',tracking=True)
    
    notes = fields.Text(string='ملاحظات',tracking=True)
  
    status = fields.Selection([('heat', 'شبق'),('insemination', 'تلقيح'),('pregnancy_check', 'فحص حمل'),('pregnancy_failed', 'فشل الحمل'),('pregnancy_success', 'نجح الحمل'),
    ('dry', 'تجفيف'),('calving', 'ولادة'),('postpartum', 'نفاس'),('done', 'انتهاء العملية'),], string='الحالة', default='heat', tracking=True)
    # import_value = fields.Float(string="قيمة الولادة")
    total_birth_value = fields.Float(string='إجمالي قيمة الولادات', compute='_compute_total_birth_value', store=True)

  
    lines = fields.Many2many('livestock.animal', string='الولادات')
    manufacturing_count = fields.Integer(
    string="عدد أوامر التصنيع",
    compute="_compute_manufacturing_count")
    stock_moves_count = fields.Integer(string="عدد إعادة التقييم", compute="_compute_stock_moves_count")

    @api.depends('lines.import_value')
    def _compute_total_birth_value(self):
        for rec in self:
            total = 0.0
            # تأكد من وجود سجلات في lines
            if rec.lines:
                for line in rec.lines:
                    # اجمع قيمة import_value من كل سجل في lines
                    total += line.import_value
            rec.total_birth_value = total

    def action_preview_stock_moves(self):
        StockValuation = self.env['stock.valuation.layer']
        for rec in self:
            # ✅ الحصول على تكلفة المنتج القديمة
            old_cost = rec.product.standard_price
            difference = rec.new_cost - old_cost

            if difference != 0:
                # ✅ إنشاء طبقة تقييم جديدة
                StockValuation.create({
                    'product_id': rec.product_id.id,
                    'quantity': rec.product_id.qty_available,
                    'unit_cost': rec.new_cost,
                    'value': difference * rec.product_id.qty_available,
                    'date': rec.date,
                    'description': f'إعادة تقييم {rec.product_id.display_name} - {rec.reason or ""}',
                    'company_id': rec.company_id.id,
                })

                # ✅ تحديث تكلفة المنتج
                rec.product.sudo().standard_price = rec.new_cost
    # ✅ حساب عدد قيود إعادة التقييم فقط
    def _compute_stock_moves_count(self):
        for rec in self:
            product_ids = rec.lines.mapped('product.id')
            if product_ids:
                count = self.env['stock.valuation.layer'].search_count([
                    ('product_id', 'in', product_ids),
                    ('description', 'ilike', 'إعادة تقييم'),  # فلترة بس على القيود اللي اتعملها revaluation
                ])
                rec.stock_moves_count = count
            else:
                rec.stock_moves_count = 0

    # ✅ فتح نافذة قيود إعادة التقييم
    def action_open_stock_moves(self):
        self.ensure_one()
        product_ids = self.lines.mapped('product.id')
        return {
            'name': "إعادة التقييم للمخزون",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.valuation.layer',
            'view_mode': 'list,form',
            'domain': [
                ('product_id', 'in', product_ids),
                ('description', 'ilike', 'إعادة تقييم'),  # نفس الفلترة زي الكاونت
            ],
            'target': 'current',
        }
    def _compute_manufacturing_count(self):
        for rec in self:
            product_names = self.lines.mapped('product.name')
            rec.manufacturing_count = self.env['mrp.production'].search_count([
                ('product_id.name', 'in', product_names)
            ])
    def action_view_manufacturing_orders(self):
        self.ensure_one()
        product_names = self.lines.mapped('product.name')
        return {
            'type': 'ir.actions.act_window',
            'name': 'أوامر التصنيع',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
           # 'domain': [('product_id.name', 'in', product_names)] ,
        'context': dict(self._context),
    }

    def action_create_mo_for_animals(self):
        mo_model = self.env['mrp.production']

        picking_type = self.env['stock.picking.type'].search([('code', '=', 'mrp_operation')], limit=1)
        if not picking_type:
            raise UserError("لا يوجد نوع عملية تصنيع معرف في النظام.")

        location_src = self.env.ref('stock.stock_location_stock')
        location_dest = self.env.ref('stock.stock_location_stock')

        for rec in self:
            for animal in rec.lines:
                if not animal.product:
                    raise UserError(f"الحيوان {animal.name} لا يحتوي على منتج مرتبط!")

                product_variant = animal.product.product_variant_id

                # التحقق إذا كان الـ MO موجود مسبقًا
                existing_mo = mo_model.search([
                    ('origin', '=', f"MO for {animal.name}"),
                    ('product_id', '=', product_variant.id)
                ], limit=1)

                if existing_mo:
                    # ممكن بدل ما نعمل Error نعمل تجاهل أو تنبيه
                    raise UserError(f"تم إنشاء أمر تصنيع لهذا الحيوان مسبقًا: {animal.name}")

                mo_model.create({
                    'product_id': product_variant.id,
                    'product_qty': 1,
                    'product_uom_id': product_variant.uom_id.id,
                    'location_src_id': location_src.id,
                    'location_dest_id': location_dest.id,
                    'picking_type_id': picking_type.id,
                    'origin': f"MO for {animal.name}"
                })

        return True
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
    def action_set_pending(self):
        self.status = 'pending'

    def action_set_monitoring(self):
        self.status = 'monitoring'

    def action_set_done(self):
        self.status = 'done'
    @api.depends('mother_id', 'birth_date')
    def _compute_name(self):
        for record in self:
            if record.mother_id and record.birth_date:
                record.name = f'ولادة {record.mother_id.name} - {record.birth_date}'
            else:
                record.name = 'ولادة جديدة'
    @api.depends('lines')
    def _compute_numbers(self):
        for record in self:
            record.number_born=len(record.lines)

class AnimalPedigree(models.Model):
    _name = 'animal.pedigree'
    _description = 'نسب الحيوان'
    _rec_name = 'animal_id'

    animal_id = fields.Many2one('livestock.animal',string='الحيوان',required=True)
    
    father_id = fields.Many2one('livestock.animal',string='الأب',domain=[('gender', '=', 'male')])
    
    mother_id = fields.Many2one('livestock.animal',string='الأم',domain=[('gender', '=', 'female')])
    
    paternal_grandfather_id = fields.Many2one('livestock.animal',string='جد الأب',domain=[('gender', '=', 'male')])
    
    paternal_grandmother_id = fields.Many2one('livestock.animal',string='جدة الأب',domain=[('gender', '=', 'female')])
    
    maternal_grandfather_id = fields.Many2one('livestock.animal',string='جد الأم',domain=[('gender', '=', 'male')])
    
    maternal_grandmother_id = fields.Many2one('livestock.animal',string='جدة الأم',domain=[('gender', '=', 'female')])
    
    generation = fields.Integer(string='الجيل',default=1)
    
    inbreeding_coefficient = fields.Float(string='معامل زواج الأقارب',help='نسبة زواج الأقارب في النسب')
    
class LivestockFarm(models.Model):
    _name = 'livestock.farm'
    _description = 'مزرعة/حظيرة'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='اسم الحظيرة', required=True, tracking=True)
    location = fields.Char(string='الموقع', tracking=True)
    capacity = fields.Integer(string='السعة القصوى', tracking=True, help='عدد الحيوانات الأقصى')
    manager_id = fields.Many2one('res.users', string='المسؤول', tracking=True)
    warehse_id = fields.Many2one(
    'stock.warehouse',
    string="المستودع",
    related='locaon_id.warehouse_id',
    readonly=True
)

    locaon_id = fields.Many2one(
    'stock.location',
    string="الموقع",
    default=lambda self: self.env['stock.location'].search([("usage", "=", "internal")], limit=1)
)

    @api.onchange('locaon_id')
    def _onchange_locaon_id(self):
        if self.locaon_id:
            self.name = self.locaon_id.name

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)

    category_line_ids = fields.One2many('livestock.farm.category.line', 'farm_id', string="أصناف المنتجات")
    warehouse_line_ids = fields.One2many('livestock.farm.warehouse.line', 'farm_id', string="المستودعات")

    # _sql_constraints = [
    #     ('name_company_uniq', 'unique(name, company_id)', 'اسم المزرعة/الحظيرة يجب أن يكون فريد في نفس الشركة!'),
    # ]4
    


class LivestockFarmCategoryLine(models.Model):
    _name = 'livestock.farm.category.line'
    _description = 'خط صنف المنتج في المزرعة'

    farm_id = fields.Many2one('livestock.farm', string="المزرعة")
    category_id = fields.Many2one('product.category', string="فئة المنتج", required=True)
    qty_available = fields.Float(string="الكمية المتاحة", compute="_compute_qty_available", store=False)

    @api.depends('category_id', 'farm_id.locaon_id')
    def _compute_qty_available(self):
        for line in self:
            qty = 0.0
            if line.category_id and line.farm_id.locaon_id:
                # البحث عن كل المنتجات داخل الفئة
                products = self.env['product.product'].search([('categ_id', '=', line.category_id.id)])
                if products:
                    # جمع الكميات من المخزون في الموقع المحدد
                    quants = self.env['stock.quant'].read_group(
                        [('product_id', 'in', products.ids), ('location_id', '=', line.farm_id.locaon_id.id)],
                        ['quantity'],
                        []
                    )
                    qty = sum(q['quantity'] for q in quants)
            line.qty_available = qty

class LivestockFarmWarehouseLine(models.Model):
    _name = 'livestock.farm.warehouse.line'
    _description = 'خط المستودع في المزرعة'

    farm_id = fields.Many2one('livestock.farm', string="المزرعة")
    category_id = fields.Many2one('product.category', string="فئة المنتج", required=True)
    qty_available = fields.Float(string="إجمالي الكمية المتاحة", compute="_compute_qty_available", store=False)

    @api.depends('category_id', 'farm_id.warehse_id')
    def _compute_qty_available(self):
        for line in self:
            qty = 0.0
            if line.farm_id.warehse_id and line.category_id:
                # تحديد كل المواقع الداخلية الخاصة بالمستودع
                products = self.env['product.product'].search([('categ_id', '=', line.category_id.id)]) 
                if products:
                    # تجميع الكميات من المخزون في المواقع دي
                    quants = self.env['stock.quant'].read_group(
                        [('product_id', 'in', products.ids), ('warehouse_id', '=', line.farm_id.warehse_id.id)],
                        ['quantity'],
                        []
                    )
                    qty = quants and quants[0].get('quantity', 0.0) or 0.0
            line.qty_available = qty

class FeedingRecord(models.Model):
    _name = 'feeding.record'
    _description = 'سجل تغذية'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name=fields.Char(string='الاسم' ,default=lambda self: self.env['ir.sequence'].next_by_code('feeding.record'))
    animal_id = fields.Many2one('livestock.animal', string='الحيوان')
    account2_id = fields.Many2one(
        'account.account',
        string="الحساب وسيط",
        required=True
    )
    account1_id = fields.Many2one(
        'account.account',
        string="الحساب ",
        required=True
    )
    mothers_count = fields.Integer(string='عدد الأمهات', compute='_compute_mothers_move_count')

    @api.depends('line_ids_feeds.type_as')
    def _compute_mothers_move_count(self):
        for rec in self:
            mother_lines = rec.line_ids_feeds.filtered(lambda l: l.type_as == 'month')
            if mother_lines:
                count = self.env['account.move'].search_count([('ref', '=', f"أمهات - {self.name}")])
                rec.mothers_count = count if count > 0 else 0
            else:
                rec.mothers_count = 0

    def action_open_mothers_lines(self):
        self.ensure_one()
        return {
        'type': 'ir.actions.act_window',
        'name': 'أسطر الأمهات',
         'res_model': 'account.move',  # غيّرها لو اسم الموديل مختلف
        'view_mode': 'list,form',
        'domain': [
            ('ref', '=', f"أمهات - {self.name}")   # 👈 عرض فقط القيود اللي مرجعها أمهات
        ],
        # 'context':{
        #     'default_type_as': 'month',
        #     'default_prod_animal': self.id,  # حط هنا المنتج اللي تبي تفترضه
        #     'default_quantity': 10,
        #     'default_total_cost': 0.0,
        # },
    }

    group = fields.Many2many('livestock.farm',string='المجموعة/الحظيرة')
    date_from = fields.Date(string='من',default=fields.Date.context_today)
    date_to = fields.Date(string='الي',default=fields.Date.context_today)
    feed_type = fields.Many2one('product.product', string='نوع العلف/الوجبة', required=True) # Changed to product.product or similar
    quantity = fields.Float(string='اجمالي الكمية', compute='_compute_total_quatity',digits=(10,2), required=True)
    actual_quantity = fields.Float(string='الكمية الفعلية', compute='_compute_actual_quantity', store=True)    
    source = fields.Selection([('stock', 'مخزون'),('self_produced', 'إنتاج ذاتي')], string='مصدر العلف', default='stock')
    cost = fields.Float(related='feed_type.standard_price', string='التكلفة')
    employee_id = fields.Many2one('res.users', string='الموظف المسؤول' ,default=lambda self: self.env.user.id)
    notes = fields.Text(string='ملاحظات')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
    line_ids_feeds = fields.One2many('feeding.record.line', 'record_id', string='بنود التغذية')
    quantity_days = fields.Float(string='اجمالي التكلفه للمدة', compute='_compute_total_tity',digits=(10,2), required=True)
    quantity_daly = fields.Float(string='اجمالي التكلفة اليومية', compute='_compute_t_quantity',digits=(10,2), required=True)
    duration_days = fields.Integer(string='عدد الأيام', compute='_compute_duration', store=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
    # Stock Picking
    picking_id = fields.Many2one('stock.picking', string='اذن الصرف')
    picking_count = fields.Integer(string='عدد أذونات الصرف', compute='_compute_picking_count')
    picking_type_id = fields.Many2one(
    'stock.picking.type', 
    string='أنواع الصرف',  required=True,
    domain=[('code', '=', 'outgoing')],

)

    revaluation_count = fields.Integer(
        string="عدد قيود التقييم",
        compute="_compute_revaluation_count"
    )

    # الحقول كما عندك...
    picking_id = fields.Many2one('stock.picking', string='اذن الصرف')
    journal_id = fields.Many2one('account.journal', string='يومية المخزون', required=True)
    # move_id = fields.Many2one('account.move', string="القيد حسابي", readonly=True)

    # def action_confirm_feeding(self):
    #     """صرف المخزون، إعادة تقييم المخزون وإنشاء قيد محاسبي"""
    #     StockValuation = self.env['stock.valuation.layer']
    #     AccountMove = self.env['account.move']
    #     AccountMoveLine = self.env['account.move.line']

    #     for record in self:
    #         if not record.line_ids_feeds:
    #             raise UserError("لا توجد بنود تغذية لإتمام العملية.")

    #         total_feed_value = 0.0

    #         # 1- إنشاء إذن الصرف إذا المصدر stock
    #         if record.source == 'stock':
    #             picking_vals = {
    #                 'picking_type_id': record.picking_type_id.id,
    #                 'partner_id': False,
    #                 'date': fields.Date.context_today(self),
    #                 'origin': record.name,
    #                 'move_ids_without_package': [],
    #             }

    #             for line in record.line_ids_feeds:
    #                 move_vals = (0, 0, {
    #                     'product_id': line.feed_type.id,
    #                     'product_uom_qty': line.quantity,
    #                     'product_uom': line.feed_type.uom_id.id,
    #                     'name': f"Feed for {line.feed_type.name}",
    #                     'location_id': record.picking_type_id.default_location_src_id.id,
    #                     'location_dest_id': record.picking_type_id.default_location_dest_id.id,
    #                 })
    #                 picking_vals['move_ids_without_package'].append(move_vals)
    #                 total_feed_value += line.quantity * line.feed_type.standard_price

    #             picking = self.env['stock.picking'].create(picking_vals)
    #             picking.action_confirm()
    #             picking.action_assign()
    #             # picking.action_done()
    #             record.picking_id = picking.id

    #         # 2- إعادة تقييم المخزون لكل حيوان
    #         for animal in record.animal_id:
    #             StockValuation.create({
    #                 'product_id': animal.product_id.id,
    #                 'quantity': 1,
    #                 'unit_cost': animal.cost + total_feed_value,
    #                 'value': animal.cost + total_feed_value,
    #                 'description': f"Revaluation for {record.name} after feeding",
    #             })
    #             animal.cost += total_feed_value

    #         # 3- إنشاء القيد المحاسبي (متوازن)
    #         if not record.move_id:
    #             move_vals = {
    #             'journal_id': record.journal_id.id,
    #             'date': fields.Date.context_today(self),
    #             'ref': f"Feeding {record.name}",
    #             'line_ids': [
    #                 # مدين: زيادة قيمة الحيوان (revaluation)
    #                 (0, 0, {
    #                     'account_id': 2461,
    #                     'debit': total_feed_value,
    #                     'credit': 0.0,
    #                     'name': f"Increase value of {record.name}",
    #                 }),
    #                 # دائن: صرف المخزون
    #                 (0, 0, {
    #                     'account_id': 2461,
    #                     'debit': 0.0,
    #                     'credit': total_feed_value,
    #                     'name': f"Consume feed {record.feed_type.name}",
    #                 }),
    #             ]
    #         }
    #         move = AccountMove.create(move_vals)
    #         move.action_post()
    #         record.move_id = move.id

    #     return True

    @api.depends('line_ids_feeds.total_cost', 'line_ids_feeds.percentage')
    def _compute_actual_quantity(self):
        for rec in self:
            total = 0.0
            for line in rec.line_ids_feeds:
                # total_cost * (النسبة / 100) لأن النسبة محسوبة كـ 100 بيس
                total += line.total_cost * (line.percentage)
            rec.actual_quantity = total

    # @api.depends('line_ids_feeds.total_cost', 'line_ids_feeds.percentage')
    # def _compute_actual_quantity(self):
    #     for rec in self:
    #         total_cost = sum(rec.line_ids_feeds.mapped('total_cost'))
    #         total_percentage = sum(rec.line_ids_feeds.mapped('percentage'))

    #         if total_percentage == 0:
    #             rec.actual_quantity = 0.0
    #         else:
    #             rec.actual_quantity = total_cost * total_percentage 

    def action_open_revaluations(self): 
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.valuation.layer',
            'view_mode': 'list,form',
            'domain': [
                ('description', '=', self.name),
            ]
        }
    def _compute_revaluation_count(self):
        for rec in self:
            rec.revaluation_count = self.env['stock.valuation.layer'].search_count([
             ('description', '=', rec.name),
            ('company_id', '=', rec.company_id.id),
        ])

    def action_create_revaluation(self):
        journal = self.env['account.journal'].search([('code', '=', 'INV')], limit=1)
        if not journal:
            raise UserError("لم يتم العثور على دفتر اليومية بكود 'INV'.")
    
        for rec in self:
            # ❌ حذف القيود القديمة
            old_moves = self.env['account.move'].search([('ref', '=', rec.name)])
            for move in old_moves:
                if move.state == 'posted':
                    move.button_draft()
                move.unlink()
    
            # ✅ حذف تقييمات المخزون القديمة المرتبطة بنفس الاسم
            old_layers = self.env['stock.valuation.layer'].search([
                ('description', '=', rec.name),
                ('company_id', '=', rec.company_id.id)
            ])
            old_layers.unlink()
    
            mother_move_lines = []
    
            for line in rec.line_ids_feeds:
                product = line.prod_animal.product_variant_id
    
                if not line.total_cost or line.total_cost == 0 or not line.quantity or line.quantity == 0:
                    continue
    
                debit_account = rec.account1_id
                credit_account = rec.account2_id
    
                if not debit_account or not credit_account:
                    raise UserError("يرجى التأكد من إعداد الحسابات المحاسبية في السجل.")
    
                if line.type_as == 'month':
                    mother_move_lines.append((0, 0, {
                        'account_id': debit_account.id,
                        'name': product.display_name,
                        'debit': line.total_cost,
                        'product_id': product.id, 
                        'credit': 0.0,
                    }))
                    mother_move_lines.append((0, 0, {
                        'account_id': credit_account.id,
                        'name': product.display_name,
                        'debit': 0.0,
                         'product_id': product.id,
                        'credit': line.total_cost,
                    }))
                    continue
    
                # ✅ إنشاء قيد لكل سطر (غير أمهات)
                move_vals = {
                    'journal_id': journal.id,
                    'date': fields.Date.today(),
                    'ref': rec.name,
                    'line_ids': [
                        (0, 0, {
                            'account_id': debit_account.id,
                             'product_id': product.id,
                            'name': f'إعادة تقييم للمخزون: {product.display_name}',
                            'debit': line.total_cost,
                            'credit': 0.0,
                        }),
                        (0, 0, {
                            'account_id': credit_account.id,
                             'product_id': product.id,
                            'name': f'إعادة تقييم للمخزون: {product.display_name}',
                            'debit': 0.0,
                            'credit': line.total_cost,
                        }),
                    ]
                }
                move = self.env['account.move'].create(move_vals)
                move.action_post()
    
                # ✅ إنشاء تقييم للمخزون
                self.env['stock.valuation.layer'].create({
                    'product_id': product.id,
                    'quantity': 0,
                    'description': rec.name,
                    'company_id': rec.company_id.id,
                    'value': line.total_cost,
                    'account_move_id': move.id,
                })
    
            # ✅ إنشاء قيد واحد للأمهات
            if mother_move_lines:
                mother_move = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': fields.Date.today(),
                     'ref': f"أمهات - {rec.name}",
                    'line_ids': mother_move_lines,
                })
                mother_move.action_post()



    # def action_create_revaluation(self):
    #     for rec in self:
    #         for line in rec.line_ids_feeds:
    #             product = line.prod_animal.product_variant_id
    #             domain = [
    #                 ('product_id', '=', product.id),
    #                 ('reason', '=', rec.name),
    #                 ('company_id', '=', rec.company_id.id),
    #             ]
    #             existing = self.env['stock.valuation.layer.revaluation'].search(domain, limit=1)
    #             if existing:
    #                 continue  # لو موجود بالفعل، لا تنشئ من جديد
    
    #             self.env['stock.valuation.layer.revaluation'].create({
    #                 'product_id': product.id,
    #                 # 'company_id': rec.company_id.id,
    #                 'date': fields.Date.today(),
    #                 'added_value': line.total_cost,
    #                 # 'account_journal_id': journal_id.id,
    #                 'reason': rec.name,
    #                 # 'account_id': 2642
    #             })


    @api.depends('name')
    def _compute_picking_count(self):
        for rec in self:
            count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])
            rec.picking_count = count

    def action_create_delivery(self):
        self.ensure_one()
    
        # تحقق من المرحلة قبل الإنشاء
        if self.state != 'confirmed':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تنبيه',
                    'message': 'لا يمكن إنشاء صرف المخزن إلا بعد تأكيد المرحلة.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
        # إذا كان هناك إذن صرف موجود مسبقًا، افتحه مباشرة
        if self.picking_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.picking_id.id,
            }
    
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
    
        # نوع الإذن: Outgoing / Delivery
        picking_type = self.picking_type_id
    
        # إنشاء Stock Picking جديد
        picking_vals = {
            # 'partner_id': False,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id ,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        }
    
        picking = StockPicking.create(picking_vals)
      
        # إنشاء Stock Move واحد من بيانات السجل نفسه
        if self.feed_type and self.quantity:
            StockMove.create({
                'name': self.feed_type.name,
                'product_id': self.feed_type.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.feed_type.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })
    
        # ربط الإذن بالسجل
        self.picking_id = picking.id
        picking.action_confirm() 
    
        # فتح نموذج الإذن بعد الإنشاء
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }
    
    def _populate_animals(self):
        """ملء أسطر الحيوانات بناءً على المجموعة"""
        for record in self:
            record.line_ids_feeds = [(5, 0, 0)]  # مسح القديم
            if not record.group:
                continue
            location_ids = record.group.mapped('locaon_id').ids
            if not location_ids:
                continue
            animals = self.env['livestock.animal'].search([
                ('farm_id.locaon_id', 'in', location_ids)
            ])
            if animals:
                record.line_ids_feeds = [(0, 0, {'animal_id': a.id}) for a in animals]

    # ===========================
    # تفعيل تلقائي عند تغيير المجموعة
    # ===========================
    @api.onchange('group')
    def _onchange_group_populate_animals(self):
        self._populate_animals()

    # ===========================
    # تفعيل تلقائي عند الإنشاء أو التعديل
    # ===========================
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._populate_animals()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'group' in vals:
            self._populate_animals()
        return res
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'مرحّل'),
        ('cancel', 'ملغي')
    ], string='الحالة', default='draft', tracking=True, required=True)
    @api.depends('line_ids_feeds.total_quantity')
    def _compute_total_quatity(self):
        for line in self:
            if line.line_ids_feeds:
                total = sum(line.line_ids_feeds.mapped('total_quantity'))
                line.quantity = total
            else:
                line.quantity = 0
    @api.depends('line_ids_feeds.total_cost')
    def _compute_total_tity(self):
        for line in self:
            if line.line_ids_feeds:
                total = sum(line.line_ids_feeds.mapped('total_cost'))
                line.quantity_days = total
            else:
                line.quantity_days = 0
    @api.depends('quantity_days', 'duration_days')
    def _compute_t_quantity(self):
        for line in self:
            if line.duration_days and line.duration_days != 0:
                line.quantity_daly = line.quantity_days / line.duration_days
            else:
                line.quantity_daly = 0
    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for record in self:
            if record.date_from and record.date_to:
                delta = (record.date_to - record.date_from).days + 1
                record.duration_days = delta if delta > 0 else 0
            else:
                record.duration_days = 0
    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
        # إنشاء صرف المخزن تلقائيًا إذا لم يكن موجودًا
            if not record.picking_id:
                record.action_create_delivery()
    def action_cancel(self):
        for record in self:
        # ألغِ السجل الحالي
            record.state = 'cancel'

        # هات كل القيود المرتبطة بالاسم أو بعلاقة مباشرة
            moves = self.env['account.move'].search([('ref', '=', record.name)])
        
        # لو فيه قيود، إلغيها
            for move in moves:
                if move.state != 'cancel':
                    move.button_cancel()

    def action_set_draft(self):
        for record in self:
            record.state = 'draft'
class FeedingRecordLine(models.Model):
    _name = 'feeding.record.line'
    _description = 'بند سجل تغذية'

    record_id = fields.Many2one('feeding.record', string='سجل التغذية', required=True, ondelete='cascade')
    animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True)
    prod_animal=fields.Many2one(related='animal_id.product',string='المنتج')
    type_as = fields.Selection(related='animal_id.cow_type', string='المرحلة', readonly=True)
    feed_type = fields.Many2one(related='record_id.feed_type', string='نوع العلف/الوجبة')
    quantity = fields.Float(string='الكمية', digits=(10, 2))
    total_quantity = fields.Float(string='إجمالي الكمية',compute='_compute_total_quantity',store=True)
    total_cost = fields.Float(string='إجمالي التكلفة',compute='_compute_total_cost',store=True)
    current_weight = fields.Float(string='الوزن الحالى', compute='_compute_current_weight', store=True)
    percentage = fields.Float(string='النسبة المئوية للوزن', compute='_compute_percentage', store=True)

    @api.depends('animal_id', 'record_id.date_from', 'record_id.date_to')
    def _compute_current_weight(self):
        for line in self:
            # التأكد من وجود الحيوان وتواريخ الفلتر
            if not line.animal_id or not line.record_id.date_to:
                line.current_weight = 0.0
                continue

            # البحث عن آخر وزن للحيوان "داخل" أو "قبل" نهاية الفترة
            # ملاحظة: غالباً في التغذية بنهتم بآخر وزن وصل له الحيوان قبل ما نبدأ نحسب تكلفة أكله
            domain = [
                ('animal_id', '=', line.animal_id.id),
                ('date', '<=', line.record_id.date_to),
                ('date', '>=', line.record_id.date_from)
            ]
            
            # لو عايز الوزن يكون "حصراً" داخل الفترة (بين من وإلى) فك التهميش عن السطر الجاي:

            last_scale = self.env['livestock.scales.line'].search(domain, order='date desc', limit=1)

            if last_scale:
                line.current_weight = last_scale.weight
            else:
                # لو مفيش ميزان في الفترة دي، بناخد آخر وزن مسجل للحيوان بشكل عام كاحتياطي
                line.current_weight = line.animal_id.current_weight or 0.0

        
    @api.depends('quantity', 'record_id.duration_days')
    def _compute_total_quantity(self):
        for line in self:
            days = line.record_id.duration_days or 0
            line.total_quantity = line.quantity * days

    @api.depends('total_quantity', 'record_id.cost')
    def _compute_total_cost(self):
        for line in self:
            cost = line.record_id.cost or 0
            line.total_cost = line.total_quantity * cost

    @api.depends('current_weight', 'record_id.line_ids_feeds.current_weight')
    def _compute_percentage(self):
        for line in self:
            if not line.record_id or not line.record_id.line_ids_feeds:
                line.percentage = 0.0
                continue

            # مجموع الأوزان "المحسوبة عند التاريخ" لكل السطور في السجل
            total_weight = sum(line.record_id.line_ids_feeds.mapped('current_weight'))

            if total_weight > 0:
                line.percentage = line.current_weight / total_weight
            else:
                line.percentage = 0.0

class LivestockAnimal(models.Model):
    _name = 'livestock.animal'
    _description = 'بيانات الحيوان'
    _rec_name = 'name'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # 🟢 الحقول الأساسية
    name = fields.Char(string='اسم الحيوان', store=True ,compute='_onchange_set_temp_name')
    product = fields.Many2one('product.template', string='المنتج',readonly=True, store=True)

    tag_no = fields.Char(string='رقم التعريف', tracking=True, help='رقم RFID أو رقم يدوي للتعريف',
                         default=lambda self: self.env['ir.sequence'].next_by_code('livestock.animal'))
    type = fields.Many2one('product.category', string='النوع', required=True, store=True)

    breeding = fields.Many2one('typesss', string='السلالة', help='سلالة الحيوان أو النوع الفرعي', required=True, store=True)

    gender = fields.Selection([
        ('male', 'ذكر'),
        ('female', 'أنثى')
    ], string='الجنس', required=True, tracking=True)
    
    birth_date = fields.Date(string='تاريخ الميلاد', tracking=True, help='تاريخ ميلاد الحيوان لحساب العمر')
    
    status = fields.Selection([
        ('alive', 'حي'),
        ('sick', 'مريض'),
        ('dead', 'نافق'),
        ('sold', 'تم بيعه')
    ], string='الحالة', required=True, default='alive', tracking=True)


    product_id = fields.Many2one('product.product')
    move_type = fields.Many2one('account.move')
    purchase_value = fields.Float(string='قيمة الشراء', compute='_compute_purchase_value')

    @api.depends('product_id','move_type')
    def _compute_purchase_value(self):
        InvoiceReport = self.env['account.invoice.report']

        for rec in self:
            line = InvoiceReport.search([
            ('product_id.name', '=', rec.product.name),
            ("move_type", "=", "in_invoice"),
            # ("state", "=", "posted")
        ], order='invoice_date desc', limit=1)

            if line:
                rec.purchase_value = abs(line.price_total)
            else:
                rec.purchase_value = 0.0


    sale_value = fields.Float(string='قيمة البيع', compute='_compute_sale_value')

    @api.depends('product_id','move_type')
    def _compute_sale_value(self):
        InvoiceReport = self.env['account.invoice.report']

        for rec in self:
            line = InvoiceReport.search([
            ('product_id.name', '=', rec.product.name),
            ("move_type", "=", "out_invoice"),
            # ("state", "=", "posted")
        ], order='invoice_date desc', limit=1)

            if line:
                rec.sale_value = line.price_total
            else:
                rec.sale_value = 0.0
                

    food_total = fields.Float(string='إجمالى الطعام')
    med_total = fields.Float(string='إجمالى العلاج')
    other_cost = fields.Float(string='إجمالى مصروفات آخرى')
    animal_value_total = fields.Float(string='إجمالى قيمة الحيوان بعد الخصم',compute='_compute_animal_value_total', store=True)
    milk_revenues = fields.Float(string='ايرادات اللبن')
    birth_revenues = fields.Float(string='ايرادات الولادات', related='birth_ids.total_birth_value')
    total_revenues = fields.Float(string='إجمالى الإيرادات', compute='_compute_total_revenues', store=True)
    total_deducting = fields.Float(string='الإجمالى بعد خصم الإيرادات', compute='_compute_total_after_deducting', store=True)
    net_profit = fields.Float(string='صافي الربح', compute='_compute_net_profit', store=True)
    stay_duration = fields.Integer(
        string='مدة الجلوس الحيوان (بالأيام)',
        compute='_compute_stay_duration',
        store=True
    )
    food_record_ids = fields.One2many('livestock.food.data.line','animal_id',string='سجلات التغذية')   
    # سجلات الموازين
    scale_record_ids = fields.One2many('livestock.scales.line','animal_id',string='سجلات الموازين')
    birth_id = fields.Many2many('animal.birth', string='الولادات')
    birth_ids = fields.One2many('animal.birth', 'mother_id', string='سجلات الولادة')
    import_value = fields.Float(string="قيمة الولادات")
    profit_ratio = fields.Float(string="نسبة الربح")
    annual_rate = fields.Float(string="معدل السنوى")
    other_revenues = fields.Float(string="ايرادات اخرى")
    total_expenses = fields.Float(string="إجمالي مصروفات")
    current_weight = fields.Float(string='الوزن الحالي', compute='_compute_current_weight')

    @api.depends('scale_record_ids.weight', 'scale_record_ids.date')
    def _compute_current_weight(self):
        for rec in self:
            if rec.scale_record_ids:
                last_line = rec.scale_record_ids.sorted(
                    key=lambda l: (l.date or fields.Date.today()),
                    reverse=True
                )[0]
                rec.current_weight = last_line.weight
            else:
                rec.current_weight = 0

    
    @api.depends('entry_date', 'exit_date')
    def _compute_stay_duration(self):
        for rec in self:
            if rec.entry_date and rec.exit_date:
                rec.stay_duration = (
                    rec.exit_date - rec.entry_date
                ).days
            else:
                rec.stay_duration = 0

    @api.depends('birth_id.total_birth_value')
    def _compute_birth_value(self):
        for rec in self:
            total = 0.0
            for birth in rec.birth_id:
                total += birth.total_birth_value
            rec.import_value = total

    @api.depends('profit_ratio','animal_value_total')
    def _compute_annual_rate(self):
      for rec in self:
            rec.annual_rate = ((rec.profit_ratio / rec.stay_duration)*360)

    @api.depends('net_profit','animal_value_total')
    def _compute_profit_ratio(self):
      for rec in self:
            rec.profit_ratio = (rec.net_profit / rec.animal_value_total)

  
    @api.depends('sale_value','total_deducting')
    def _compute_net_profit(self):
      for rec in self:
            rec.net_profit = (rec.sale_value - rec.total_deducting)
        
    @api.depends('animal_value_total','total_revenues')
    def _compute_total_after_deducting(self):
      for rec in self:
            rec.total_deducting = (rec.animal_value_total - rec.total_revenues)
        
    @api.depends('milk_revenues','birth_revenues')
    def _compute_total_revenues(self):
      for rec in self:
            rec.total_revenues = (rec.milk_revenues + rec.birth_revenues)
        
    @api.depends('purchase_value','food_total','med_total','other_cost')
    def _compute_animal_value_total(self):
        for rec in self:
            rec.animal_value_total = (
                rec.purchase_value
                + rec.food_total
                + rec.med_total
                + rec.other_cost
              )
  
    def action_set_alive(self):
        for rec in self:
            rec.status = 'alive'

    def action_set_sick(self):
        for rec in self:
            rec.status = 'sick'

    def action_set_dead(self):
        for rec in self:
            rec.status = 'dead'

    def action_set_sold(self):
        for rec in self:
            rec.status = 'sold'
    @api.depends('breeding', 'type','tag_no')
    def _onchange_set_temp_name(self):
        for rec in self:
            breed = rec.breeding.name if rec.breeding else ''
            ttype = rec.type.name if rec.type else ''
            tag = rec.tag_no or ''
            rec.name = f"{ttype} {breed} {tag}".strip(' -')
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.name:
            product = self.env['product.template'].create({
                'name': rec.name,
            
            })
            rec.product = product.id
        return rec

    def write(self, vals):
        for rec in self:
            old_name = rec.name

        # نفّذ الكتابة
        result = super().write(vals)

        for rec in self:
            if rec.name != old_name:
                # إذا تغيّر الاسم، احذف المنتج القديم وأنشئ جديد
                if rec.product:
                    rec.product.write({'name': rec.name})

        return result
    cow_type = fields.Selection([('milked', 'رضاعة'),('weaning', 'فطام'),('fattening', 'تسمين'),('lactating', 'مرضعة'),('milking', 'حلابة'),], string='المرحلة', tracking=True)
    teething = fields.Char(string='التسنين', tracking=True)

    dose_ids = fields.One2many('livestock.vaccination.dose', 'animal_id', string='الجرعات')

    # 🟢 الحقول المحسوبة
    age = fields.Integer(string='العمر (بالأيام)',compute='_compute_age',store=True)

    age_years = fields.Integer(string='العمر (بالسنوات)',compute='_compute_age',store=True)

    age_months = fields.Integer(string='العمر (بالشهور)',compute='_compute_age',store=True)
    today_date = fields.Date(default=fields.Date.context_today)

    # 🟢 حقول إحصائية للوحة التحكم
    # total_animals = fields.Integer(string='عدد الحيوانات الكلي', compute='_compute_dashboard_stats', store=False)
    # alive_animals = fields.Integer(string='عدد الحيوانات الحية', compute='_compute_dashboard_stats', store=False)
    # births_this_month = fields.Integer(string='عدد الولادات هذا الشهر', compute='_compute_dashboard_stats', store=False)
    # milk_production_this_month = fields.Float(string='إجمالي إنتاج اللبن هذا الشهر (كجم)', compute='_compute_dashboard_stats', store=False)

    # 🟢 العلاقات
    # breeding_id = fields.Many2one('animal.breeding', string='عملية التكاثر', tracking=True)
    # birth_id = fields.Many2one('animal.birth', string='عملية الولادة', tracking=True)
    # production_id = fields.Many2one('meat.production', string='إنتاج اللحم')

    # 🟢 علاقات النسب
    mother_id = fields.Many2one('livestock.animal',string='الأم',domain="[('gender','=','female')]",tracking=True,help='ربط الحيوان بالأم (إن وجدت)')
    
    father_id = fields.Many2one('livestock.animal',string='الأب',domain="[('gender','=','male')]",tracking=True,help='ربط الحيوان بالأب (إن وجد)')

    # 🟢 المزرعة/الحظيرة
    farm_id = fields.Many2one('livestock.farm',string='المزرعة/الحظيرة',tracking=True,help='المزرعة أو الحظيرة التي يتواجد بها الحيوان')

    # 🟢 تواريخ الدخول والخروج
    entry_date = fields.Date(string='تاريخ الدخول',tracking=True,help='تاريخ دخول الحيوان للمزرعة/الحظيرة')
    
    exit_date = fields.Date(string='تاريخ الخروج',tracking=True,help='تاريخ خروج الحيوان من المزرعة/الحظيرة (بيع/وفاة/نقل)' )

    # 🟢 مصدر الحيوان
    origin = fields.Selection([('birth','ولادة داخلية'),('purchase', 'شراء'),('import', 'استيراد'),('other', 'أخرى')],
    string='مصدر الحيوان', tracking=True)

    # 🟢 رقم جواز السفر/شهادة صحية
    passport_no = fields.Char(string='رقم جواز السفر/الشهادة الصحية',tracking=True,help='رقم جواز السفر أو الشهادة الصحية للحيوان (إن وجدت)')

    # 🟢 الموقع الجغرافي (اختياري)
    geo_location = fields.Char(string='الموقع الجغرافي',tracking=True,help='موقع الحيوان الجغرافي أو رقم الحظيرة/المزرعة بدقة')

    # 🟢 بيانات إضافية
    image = fields.Binary(string='صورة الحيوان', attachment=True)
    color = fields.Char(string='اللون', tracking=True)
    notes = fields.Text(string='ملاحظات', tracking=True)

    # 🟢 الحقول التقنية
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        default=lambda self: self.env.company, required=True
    )

    # 🟢 القيود
    # _sql_constraints = [
    #     ('name_company_uniq', 'unique(name, company_id)', 'اسم الحيوان يجب أن يكون فريد في نفس الشركة!'),
    #     ('tag_no_company_uniq', 'unique(tag_no, company_id)', 'رقم التعريف يجب أن يكون فريد في نفس الشركة!'),
    # ]

    # ✅ حساب العمر
    @api.depends('birth_date', 'today_date')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.birth_date:
                delta = today - rec.birth_date
                rec.age = delta.days
                rec.age_years = delta.days // 365
                rec.age_months = (delta.days % 365) // 30
            else:
                rec.age = rec.age_years = rec.age_months = 0
    def action_update_all_ages(self):
        records = self.search([])
        if not records:
            raise UserError(_("لا توجد سجلات لتحديث العمر."))
        records._compute_age()
        return True
    # ✅ قيود على القيم
    @api.constrains('birth_date')
    def _check_birth_date(self):
        for rec in self:
            if rec.birth_date and rec.birth_date > date.today():
                raise ValidationError(_('تاريخ الميلاد لا يمكن أن يكون في المستقبل.'))

    @api.constrains('weight')
    def _check_weight(self):
        for rec in self:
            if rec.weight and rec.weight < 0:
                raise ValidationError(_('الوزن يجب أن يكون رقم موجب.'))

    # ✅ أزرار تغيير الحالة
    def action_mark_sick(self):
        self.write({'status': 'sick'})
        for rec in self:
            rec.message_post(body=_('تم تغيير حالة الحيوان إلى مريض.'))

    def action_mark_alive(self):
        self.write({'status': 'alive'})
        for rec in self:
            rec.message_post(body=_('تم تغيير حالة الحيوان إلى حي.'))

    def action_mark_dead(self):
        self.write({'status': 'dead'})
        for rec in self:
            rec.message_post(body=_('تم تغيير حالة الحيوان إلى نافق.'))

    def action_mark_sold(self):
        self.write({'status': 'sold'})
        for rec in self:
            rec.message_post(body=_('تم تغيير حالة الحيوان إلى مباع.'))


    # ✅ إحصائيات لوحة التحكم
    @api.model
    def get_dashboard_stats(self):
        return {
            # 'total_animals': self.search_count([]),
            # 'alive_animals': self.search_count([('status', '=', 'alive')]),
            'sick_animals': self.search_count([('status', '=', 'sick')]),
            'dead_animals': self.search_count([('status', '=', 'dead')]),
            'sold_animals': self.search_count([('status', '=', 'sold')]),
            'animals_need_vaccination': len(self.search([]).get_animals_need_vaccination()),
        }

    # ✅ الأنشطة الحديثة
    @api.model
    def get_recent_activities(self):
        activities = []
        recent = self.search([], order='create_date desc', limit=10)
        for rec in recent:
            activities.append({
                'text': f'تم إنشاء حيوان {rec.name} من نوع {rec.type}',
                'time': rec.create_date.strftime('%Y-%m-%d %H:%M'),
                'animal_id': rec.id,
            })
        return activities

    @api.depends()
    def _compute_dashboard_stats(self):
        LivestockAnimal = self.env['livestock.animal']
        Breeding = self.env['animal.breeding']
        Production = self.env['meat.production']
        today = fields.Date.today()
        month_start = today.replace(day=1)
        for rec in self:
            rec.total_animals = LivestockAnimal.search_count([])
            rec.alive_animals = LivestockAnimal.search_count([('status', '=', 'alive')])
            rec.births_this_month = Breeding.search_count([('date', '>=', month_start)])
            rec.milk_production_this_month = sum(Production.search([
                ('date', '>=', month_start)
            ]).mapped('quantity'))

    def get_animals_need_vaccination(self):
        """
        إرجاع الحيوانات التي تحتاج جرعات حسب السن بناءً على جدول التطعيمات.
        """
        VaccinationSchedule = self.env['livestock.vaccination.schedule']
        today = fields.Date.today()
        result = []
        for animal in self:
            # حساب عمر الحيوان بالأيام
            if animal.birth_date:
                age_days = (today - animal.birth_date).days
                # البحث عن جدول تطعيم مناسب
                schedules = VaccinationSchedule.search([
                    ('animal_type', 'in', [animal.type, 'all']),
                    ('age_days', '<=', age_days)
                ])
                for schedule in schedules:
                    # تحقق إذا لم يأخذ الجرعة بعد
                    taken = self.env['livestock.vaccination.dose'].search_count([
                        ('animal_id', '=', animal.id),
                        ('vaccine_name', '=', schedule.vaccine_name),
                        ('dose_number', '=', schedule.dose_number)
                    ])
                    if not taken:
                        result.append(animal)
                        break
        return result

class MilkProduction(models.Model):
    _name = 'milk.production'
    _description = 'انتاج الحليب'
    _rec_name = 'name'
    _order = 'date desc, session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='وصف',compute='_compute_name',store=True)
    
    # animal_id = fields.Many2one('livestock.animal',string='الحيوان',required=True,tracking=True)
    line_ids = fields.One2many('milk.production.line', 'production_id', string='بنود الإنتاج')
    date = fields.Date(string='التاريخ',required=True,default=fields.Date.today,tracking=True)
    
    session = fields.Selection([('morning', 'صباحي'),('afternoon', 'ظهيرة'),('evening', 'مساء'),
               ('night', 'ليلي')],string='الجلسة', required=True, default='morning', tracking=True)
    
    # quantity = fields.Float(string='الكمية (لتر)',required=True,tracking=True)
    
    quality_grade = fields.Selection([('excellent', 'ممتاز'),('good', 'جيد'),('fair', 'مقبول'),('poor', 'ضعيف')]
                   ,string='درجة الجودة', default='good', tracking=True)
    
    fat_content = fields.Float(string='نسبة الدهون (%)',tracking=True)
    
    protein_content = fields.Float(string='نسبة البروتين (%)',tracking=True )
    
    temperature = fields.Float(string='درجة الحرارة (°م)',tracking=True)
    
    milker_name = fields.Char(string='اسم الحلاب',tracking=True)
    
    equipment_used = fields.Char(string='المعدات المستخدمة',tracking=True)
    
    storage_location = fields.Char(string='مكان التخزين',tracking=True)
    total_quantity = fields.Float(string='إجمالي الكمية (لتر)', compute='_compute_total_quantity', store=True)  
    @api.depends('line_ids.quantity')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = sum(line.quantity for line in record.line_ids)
    @api.depends('name', 'date', 'session')
    def _compute_name(self):
        for record in self:
            if record.name and record.date:
                session_name = dict(record._fields['session'].selection).get(record.session, '')
                record.name = f'{record.name} - {record.date} ({session_name})'
            else:
                record.name = 'إنتاج حليب جديد'
    
    @api.depends('sold_quantity', 'price_per_liter')
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = record.sold_quantity * record.price_per_liter
    
    @api.constrains('sold_quantity', 'quantity')
    def _check_sold_quantity(self):
        for record in self:
            if record.sold_quantity > record.quantity:
                raise ValidationError(_('الكمية المباعة لا يمكن أن تكون أكبر من الكمية المنتجة'))
class MilkProductionLine(models.Model):
    _name = 'milk.production.line'
    _description = 'بند إنتاج الحليب'

    production_id = fields.Many2one('milk.production', string='سجل الإنتاج', ondelete='cascade', required=True)
    animal_id = fields.Many2one('livestock.animal', string='البقرة', domain=[('gender', '=', 'female')], required=True)
    quantity = fields.Float(string='الكمية (لتر)', required=True)

class MeatProduction(models.Model):
    _name = 'meat.production'
    _description = 'إنتاج اللحوم'
    _rec_name = 'name'
    _order = 'slaughter_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='اسم السجل',compute='_compute_name',store=True)
    
    animal_id = fields.Many2one('livestock.animal',string='الحيوان',required=True,tracking=True)
    
    slaughter_date = fields.Date(string='تاريخ الذبح',required=True,default=fields.Date.today,tracking=True)
    
    live_weight = fields.Float(string='الوزن الحي (كجم)',required=True,tracking=True)
    
    carcass_weight = fields.Float(string='وزن الذبيحة (كجم)',required=True,tracking=True)
    
    dressing_percentage = fields.Float(string='نسبة التصافي (%)',compute='_compute_dressing_percentage',store=True)
    
    meat_grade = fields.Selection([('premium', 'ممتاز'),('choice', 'اختيار'),('good', 'جيد'),('standard', 'عادي'),('commercial', 'تجاري')], string='درجة اللحم', default='good', tracking=True)
    
    cuts = fields.One2many('meat.cut','production_id',string='القطع')
    
    slaughterhouse = fields.Char(string='المسلخ',tracking=True)
    
    veterinary_inspection = fields.Boolean(string='فحص بيطري',default=True,tracking=True)
    
    halal_certified = fields.Boolean(string='شهادة حلال',default=True,tracking=True)
    
    @api.depends('animal_id', 'slaughter_date')
    def _compute_name(self):
        for record in self:
            if record.animal_id and record.slaughter_date:
                record.name = f'{record.animal_id.name} - {record.slaughter_date}'
            else:
                record.name = 'إنتاج لحوم جديد'
    
    @api.depends('live_weight', 'carcass_weight')
    def _compute_dressing_percentage(self):
        for record in self:
            if record.live_weight > 0:
                record.dressing_percentage = (record.carcass_weight / record.live_weight) * 100
            else:
                record.dressing_percentage = 0
    
    @api.depends('cuts.total_price')
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = sum(record.cuts.mapped('total_price'))
    
    @api.depends('total_revenue', 'slaughter_cost', 'processing_cost')
    def _compute_net_profit(self):
        for record in self:
            total_cost = record.slaughter_cost + record.processing_cost
            record.net_profit = record.total_revenue - total_cost


class MeatCut(models.Model):
    _name = 'meat.cut'
    _description = 'قطعة لحم'
    _rec_name = 'cut_type'

    production_id = fields.Many2one(
        'meat.production',
        string='إنتاج اللحوم',
        required=True,
        ondelete='cascade'
    )
    
    cut_type = fields.Selection([('tenderloin', 'فيليه'),('ribeye', 'ريب آي'),('sirloin', 'سيرلوين'),('chuck', 'كتف'),('brisket', 'صدر'),
    ('round', 'فخذ'),('shank', 'ساق'),('ribs', 'أضلاع'),('ground', 'مفروم'),('organs', 'أحشاء'),('other', 'أخرى')], string='نوع القطعة',
    required=True)
    
    weight = fields.Float(string='الوزن (كجم)',required=True)
    
    price_per_kg = fields.Float(string='سعر الكيلو',required=True)
    
    total_price = fields.Float(string='إجمالي السعر',compute='_compute_total_price',store=True)
    
    sold = fields.Boolean(string='مباع',default=False)
    
    buyer = fields.Char(string='المشتري')
    
    sale_date = fields.Date(string='تاريخ البيع')
    
    @api.depends('weight', 'price_per_kg')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.weight * record.price_per_kg


class EggProduction(models.Model):
    _name = 'egg.production'
    _description = 'إنتاج البيض'
    _rec_name = 'name'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='اسم السجل',
        compute='_compute_name',
        store=True
    )
    
animal_id = fields.Many2one('livestock.animal',string='الطائر',required=True,domain=[('type', 'in',
['chicken', 'duck', 'goose', 'turkey', 'quail'])],tracking=True)

class LivestockSomething(models.Model):
    _name = 'livestock.something'

    date = fields.Date(string='التاريخ', required=True, default=fields.Date.today, tracking=True)
    
    quantity = fields.Integer(string='عدد البيض',required=True,tracking=True)
    
    total_weight = fields.Float(string='الوزن الإجمالي (كجم)',tracking=True)

    average_weight = fields.Float(string='متوسط وزن البيضة (جم)',compute='_compute_average_weight',store=True)
    
    egg_size = fields.Selection([
        ('small', 'صغير'),
        ('medium', 'متوسط'),
        ('large', 'كبير'),
        ('extra_large', 'كبير جداً')
    ], string='حجم البيض', default='medium', tracking=True)
    
    quality_grade = fields.Selection([
        ('grade_aa', 'درجة AA'),
        ('grade_a', 'درجة A'),
        ('grade_b', 'درجة B'),
        ('grade_c', 'درجة C')
    ], string='درجة الجودة', default='grade_a', tracking=True)
    
    broken_eggs = fields.Integer(
        string='البيض المكسور',
        default=0,
        tracking=True
    )
    
    dirty_eggs = fields.Integer(
        string='البيض المتسخ',
        default=0,
        tracking=True
    )
    
    good_eggs = fields.Integer(
        string='البيض الجيد',
        compute='_compute_good_eggs',
        store=True
    )
    
    collection_time = fields.Selection([
        ('morning', 'صباحي'),
        ('afternoon', 'ظهيرة'),
        ('evening', 'مساء')
    ], string='وقت الجمع', default='morning', tracking=True)
    
    collector_name = fields.Char(
        string='اسم الجامع',
        tracking=True
    )
    
    storage_location = fields.Char(
        string='مكان التخزين',
        tracking=True
    )
    
    temperature = fields.Float(
        string='درجة حرارة التخزين (°م)',
        tracking=True
    )
    
    sold_quantity = fields.Integer(
        string='الكمية المباعة',
        tracking=True
    )
    
    price_per_egg = fields.Float(
        string='سعر البيضة',
        tracking=True
    )
    
    price_per_dozen = fields.Float(
        string='سعر الدستة',
        tracking=True
    )
    
    total_revenue = fields.Float(
        string='إجمالي الإيراد',
        compute='_compute_total_revenue',
        store=True
    )
    
    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )

    @api.depends('animal_id', 'date')
    def _compute_name(self):
        for record in self:
            if record.animal_id and record.date:
                record.name = f"بيض {record.animal_id.name} - {record.date}"
            else:
                record.name = "سجل بيض جديد"

    @api.depends('total_weight', 'quantity')
    def _compute_average_weight(self):
        for record in self:
            if record.quantity > 0 and record.total_weight:
                record.average_weight = (record.total_weight * 1000) / record.quantity  # Convert to grams
            else:
                record.average_weight = 0

    @api.depends('quantity', 'broken_eggs', 'dirty_eggs')
    def _compute_good_eggs(self):
        for record in self:
            record.good_eggs = record.quantity - record.broken_eggs - record.dirty_eggs

    @api.depends('sold_quantity', 'price_per_egg', 'price_per_dozen')
    def _compute_total_revenue(self):
        for record in self:
            if record.price_per_dozen and record.sold_quantity >= 12:
                dozens = record.sold_quantity // 12
                remaining = record.sold_quantity % 12
                record.total_revenue = (dozens * record.price_per_dozen) + (remaining * record.price_per_egg)
            else:
                record.total_revenue = record.sold_quantity * record.price_per_egg

    @api.constrains('quantity', 'broken_eggs', 'dirty_eggs')
    def _check_egg_quantities(self):
        for record in self:
            if record.broken_eggs + record.dirty_eggs > record.quantity:
                raise ValidationError(_('عدد البيض المكسور والمتسخ لا يمكن أن يكون أكبر من العدد الإجمالي'))


class WoolProduction(models.Model):
    _name = 'wool.production'
    _description = 'إنتاج الصوف'
    _rec_name = 'name'
    _order = 'shearing_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='اسم السجل',
        compute='_compute_name',
        store=True
    )
    
    animal_id = fields.Many2one(
        'livestock.animal',
        string='الحيوان',
        required=True,
     
        tracking=True
    )
    
    shearing_date = fields.Date(
        string='تاريخ الجز',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    raw_weight = fields.Float(
        string='الوزن الخام (كجم)',
        required=True,
        tracking=True
    )
    
    clean_weight = fields.Float(
        string='الوزن النظيف (كجم)',
        tracking=True
    )
    
    yield_percentage = fields.Float(
        string='نسبة الإنتاج (%)',
        compute='_compute_yield_percentage',
        store=True
    )
    
    wool_grade = fields.Selection([
        ('super_fine', 'فائق النعومة'),
        ('fine', 'ناعم'),
        ('medium', 'متوسط'),
        ('coarse', 'خشن'),
        ('very_coarse', 'خشن جداً')
    ], string='درجة الصوف', default='medium', tracking=True)
    
    fiber_length = fields.Float(
        string='طول الألياف (سم)',
        tracking=True
    )
    
    color = fields.Selection([
        ('white', 'أبيض'),
        ('cream', 'كريمي'),
        ('light_brown', 'بني فاتح'),
        ('brown', 'بني'),
        ('dark_brown', 'بني داكن'),
        ('black', 'أسود'),
        ('gray', 'رمادي'),
        ('mixed', 'مختلط')
    ], string='اللون', default='white', tracking=True)
    
    moisture_content = fields.Float(
        string='نسبة الرطوبة (%)',
        tracking=True
    )
    
    lanolin_content = fields.Float(
        string='نسبة اللانولين (%)',
        tracking=True
    )
    
    shearer_name = fields.Char(
        string='اسم الجزاز',
        tracking=True
    )
    
    shearing_method = fields.Selection([
        ('hand_shears', 'مقص يدوي'),
        ('electric_clippers', 'مقص كهربائي'),
        ('blade_shears', 'مقص شفرة')
    ], string='طريقة الجز', default='electric_clippers', tracking=True)
    
    storage_location = fields.Char(
        string='مكان التخزين',
        tracking=True
    )
    
    processing_status = fields.Selection([
        ('raw', 'خام'),
        ('washed', 'مغسول'),
        ('carded', 'ممشط'),
        ('spun', 'مغزول'),
        ('sold', 'مباع')
    ], string='حالة المعالجة', default='raw', tracking=True)
    
    sold_weight = fields.Float(
        string='الوزن المباع (كجم)',
        tracking=True
    )
    
    price_per_kg = fields.Float(
        string='سعر الكيلو',
        tracking=True
    )
    
    total_revenue = fields.Float(
        string='إجمالي الإيراد',
        compute='_compute_total_revenue',
        store=True
    )
    
    processing_cost = fields.Float(
        string='تكلفة المعالجة',
        tracking=True
    )
    
    net_profit = fields.Float(
        string='صافي الربح',
        compute='_compute_net_profit',
        store=True
    )
    
    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )

    @api.depends('animal_id', 'shearing_date')
    def _compute_name(self):
        for record in self:
            if record.animal_id and record.shearing_date:
                record.name = f"صوف {record.animal_id.name} - {record.shearing_date}"
            else:
                record.name = "سجل صوف جديد"

    @api.depends('raw_weight', 'clean_weight')
    def _compute_yield_percentage(self):
        for record in self:
            if record.raw_weight > 0 and record.clean_weight:
                record.yield_percentage = (record.clean_weight / record.raw_weight) * 100
            else:
                record.yield_percentage = 0

    @api.depends('sold_weight', 'price_per_kg')
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = record.sold_weight * record.price_per_kg

    @api.depends('total_revenue', 'processing_cost')
    def _compute_net_profit(self):
        for record in self:
            record.net_profit = record.total_revenue - record.processing_cost

    @api.constrains('clean_weight', 'raw_weight')
    def _check_weights(self):
        for record in self:
            if record.clean_weight and record.raw_weight and record.clean_weight > record.raw_weight:
                raise ValidationError(_('الوزن النظيف لا يمكن أن يكون أكبر من الوزن الخام'))


class ProductionRecord(models.Model):
    _name = 'production.record'
    _description = 'سجل إنتاج'
    _order = 'date desc'

    animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True, tracking=True)
    quantity = fields.Float(string='الكمية', digits=(10,2), required=True)
    unit = fields.Char(string='الوحدة', default='كجم')
    date = fields.Date(string='التاريخ', required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)


class ProductionReport(models.Model):
    _name = 'production.report'
    _description = 'تقرير الإنتاج'
    _auto = True

    animal_id = fields.Many2one('livestock.animal', string='الحيوان')
    date = fields.Date(string='التاريخ')
    
    # Milk Production
    milk_quantity = fields.Float(string='كمية الحليب (لتر)')
    milk_revenue = fields.Float(string='إيراد الحليب')
    
    # Meat Production
    meat_weight = fields.Float(string='وزن اللحم (كجم)')
    meat_revenue = fields.Float(string='إيراد اللحم')
    
    # Egg Production
    egg_quantity = fields.Integer(string='عدد البيض')
    egg_revenue = fields.Float(string='إيراد البيض')
    
    # Wool Production
    wool_weight = fields.Float(string='وزن الصوف (كجم)')
    wool_revenue = fields.Float(string='إيراد الصوف')
    
    # Totals
    total_revenue = fields.Float(string='إجمالي الإيراد')
    production_type = fields.Char(string='نوع الإنتاج الرئيسي')


class ProductionDashboard(models.Model):
    _name = 'production.dashboard'
    _description = 'لوحة تحكم الإنتاج'
    _auto = True

    # Animal Information
    animal_id = fields.Many2one('livestock.animal', string='الحيوان')
    animal_name = fields.Char(string='اسم الحيوان')
    animal_type = fields.Selection([
        ('بقرة', 'بقرة'),
        ('جاموس', 'جاموس'),
        ('ماعز', 'ماعز'),
        ('خروف', 'خروف'),
        ('دجاج', 'دجاج'),
        ('بط', 'بط'),
        ('اوز', 'إوز'),
        ('ديك رومي', 'ديك رومي'),
        ('سمان', 'سمان'),
        ('اخري', 'أخرى')
    ], string='نوع الحيوان')
    
    # Production Categories
    primary_production = fields.Char(string='الإنتاج الأساسي')
    secondary_production = fields.Char(string='الإنتاج الثانوي')
    
    # Current Month Production
    current_month_milk = fields.Float(string='حليب هذا الشهر (لتر)')
    current_month_eggs = fields.Integer(string='بيض هذا الشهر')
    current_month_wool = fields.Float(string='صوف هذا الشهر (كجم)')
    current_month_meat = fields.Float(string='لحم هذا الشهر (كجم)')
    
    # Revenue
    current_month_revenue = fields.Float(string='إيراد هذا الشهر')
    total_revenue = fields.Float(string='إجمالي الإيراد')
    
    # Performance Indicators
    production_efficiency = fields.Float(string='كفاءة الإنتاج (%)')
    last_production_date = fields.Date(string='آخر تاريخ إنتاج')
    
class TreatmentRecord(models.Model):
    _name = 'treatment.record'
    _description = 'سجل علاج بيطري'
    _order = 'date desc'

    animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True, tracking=True)
    date = fields.Date(string='تاريخ العلاج', required=True, tracking=True)
    treatment_type = fields.Selection([
        ('medication', 'دواء'),
        ('surgery', 'جراحة'),
        ('physiotherapy', 'علاج طبيعي'),
        ('other', 'أخرى')
    ], string='نوع العلاج', required=True, tracking=True)
    treatment_name = fields.Char(string='اسم الدواء/العلاج', required=True, tracking=True)
    dosage = fields.Char(string='الجرعة', tracking=True)
    duration = fields.Char(string='مدة العلاج', tracking=True)
    vet_id = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    diagnosis = fields.Text(string='سبب العلاج/التشخيص')
    result = fields.Text(string='النتائج/الملاحظات')
    cost = fields.Float(string='التكلفة', digits=(10,2))
    status = fields.Selection([
        ('scheduled', 'مجدول'),
        ('in_progress', 'جاري'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ], string='حالة العلاج', default='scheduled', tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)


class LivestockVaccinationDose(models.Model):
    _name = 'livestock.vaccination.dose'
    _description = 'جرعة التطعيم'
    _rec_name = 'vaccine_name'
    _order = 'vaccination_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # 🟢 الحقول الأساسية
    animal_id = fields.Many2one(
        'livestock.animal',
        string='الحيوان',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    vaccine_name = fields.Char(
        string='اسم اللقاح',
        required=True,
        tracking=True,
        help='اسم اللقاح أو التطعيم'
    )

    vaccine_type = fields.Selection([
        ('foot_mouth', 'الحمى القلاعية'),
        ('brucellosis', 'البروسيلا'),
        ('anthrax', 'الجمرة الخبيثة'),
        ('blackleg', 'الساق السوداء'),
        ('pneumonia', 'الالتهاب الرئوي'),
        ('diarrhea', 'الإسهال'),
        ('other', 'أخرى')
    ], string='نوع اللقاح', required=True, tracking=True)

    vaccination_date = fields.Date(
        string='تاريخ التطعيم',
        required=True,
        tracking=True,
        default=fields.Date.today
    )

    next_vaccination_date = fields.Date(
        string='موعد التطعيم القادم',
        tracking=True,
        help='موعد الجرعة التالية'
    )

    dose_number = fields.Integer(
        string='رقم الجرعة',
        required=True,
        default=1,
        tracking=True,
        help='رقم الجرعة (1، 2، 3...)'
    )

    # 🟢 العمر عند التطعيم
    animal_age_days = fields.Integer(
        string='عمر الحيوان (أيام)',
        compute='_compute_animal_age',
        store=True,
        help='عمر الحيوان بالأيام عند التطعيم'
    )

    animal_age_months = fields.Integer(
        string='عمر الحيوان (شهور)',
        compute='_compute_animal_age',
        store=True,
        help='عمر الحيوان بالشهور عند التطعيم'
    )

    # 🟢 تفاصيل التطعيم
    veterinarian = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )

    batch_number = fields.Char(
        string='رقم الدفعة',
        tracking=True,
        help='رقم دفعة اللقاح'
    )

    manufacturer = fields.Char(
        string='الشركة المصنعة',
        tracking=True,
        help='الشركة المصنعة للقاح'
    )

    expiry_date = fields.Date(
        string='تاريخ انتهاء الصلاحية',
        tracking=True,
        help='تاريخ انتهاء صلاحية اللقاح'
    )

    dosage = fields.Char(
        string='الجرعة',
        tracking=True,
        help='كمية الجرعة المعطاة'
    )

    administration_route = fields.Selection([
        ('intramuscular', 'عضلي'),
        ('subcutaneous', 'تحت الجلد'),
        ('intravenous', 'وريدي'),
        ('oral', 'فموي'),
        ('nasal', 'أنفي'),
        ('other', 'أخرى')
    ], string='طريقة الإعطاء', tracking=True)

    # 🟢 الحالة والنتائج
    status = fields.Selection([
        ('scheduled', 'مجدول'),
        ('completed', 'مكتمل'),
        ('missed', 'فائت'),
        ('cancelled', 'ملغي')
    ], string='الحالة', required=True, default='completed', tracking=True)

    reaction = fields.Selection([
        ('none', 'لا توجد'),
        ('mild', 'خفيفة'),
        ('moderate', 'متوسطة'),
        ('severe', 'شديدة')
    ], string='ردة الفعل', tracking=True)

    reaction_notes = fields.Text(
        string='ملاحظات ردة الفعل',
        tracking=True,
        help='تفاصيل ردة الفعل إن وجدت'
    )

    cost = fields.Float(
        string='التكلفة',
        digits=(10, 2),
        tracking=True,
        help='تكلفة التطعيم'
    )

    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        default=lambda self: self.env.company, required=True
    )

    # ✅ حساب عمر الحيوان عند التطعيم
    @api.depends('animal_id.birth_date', 'vaccination_date')
    def _compute_animal_age(self):
        for rec in self:
            if rec.animal_id.birth_date and rec.vaccination_date:
                age_days = (rec.vaccination_date - rec.animal_id.birth_date).days
                rec.animal_age_days = age_days
                rec.animal_age_months = age_days // 30
            else:
                rec.animal_age_days = 0
                rec.animal_age_months = 0

    # ✅ التحقق من صحة التواريخ
    @api.constrains('vaccination_date', 'next_vaccination_date', 'expiry_date')
    def _check_dates(self):
        for rec in self:
            if rec.next_vaccination_date and rec.vaccination_date and rec.next_vaccination_date <= rec.vaccination_date:
                raise ValidationError(_('موعد التطعيم القادم يجب أن يكون بعد تاريخ التطعيم الحالي'))
            
            if rec.expiry_date and rec.vaccination_date and rec.expiry_date < rec.vaccination_date:
                raise ValidationError(_('تاريخ انتهاء صلاحية اللقاح يجب أن يكون بعد تاريخ التطعيم'))

    # ✅ إنشاء التطعيم القادم تلقائياً
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.next_vaccination_date and rec.status == 'completed':
            # إنشاء تذكير للتطعيم القادم
            self.env['livestock.vaccination.dose'].create({
                'animal_id': rec.animal_id.id,
                'vaccine_name': rec.vaccine_name,
                'vaccine_type': rec.vaccine_type,
                'vaccination_date': rec.next_vaccination_date,
                'dose_number': rec.dose_number + 1,
                'status': 'scheduled',
                'veterinarian': rec.veterinarian,
                'manufacturer': rec.manufacturer,
                'dosage': rec.dosage,
                'administration_route': rec.administration_route,
                'company_id': rec.company_id.id,
            })
        return rec


class LivestockVaccinationSchedule(models.Model):
    _name = 'livestock.vaccination.schedule'
    _description = 'جدول التطعيمات'
    _rec_name = 'vaccine_name'
    _order = 'animal_type, age_days'

    # 🟢 الحقول الأساسية
    vaccine_name = fields.Char(
        string='اسم اللقاح',
        required=True,
        help='اسم اللقاح أو التطعيم'
    )

    vaccine_type = fields.Selection([
        ('foot_mouth', 'الحمى القلاعية'),
        ('brucellosis', 'البروسيلا'),
        ('anthrax', 'الجمرة الخبيثة'),
        ('blackleg', 'الساق السوداء'),
        ('pneumonia', 'الالتهاب الرئوي'),
        ('diarrhea', 'الإسهال'),
        ('other', 'أخرى')
    ], string='نوع اللقاح', required=True)

    animal_type = fields.Selection([
        ('بقرة', 'بقرة'),
        ('خروف', 'خروف'),
        ('ماعز', 'ماعز'),
        ('جمل', 'جمل'),
        ('حصان', 'حصان'),
        ('حمار', 'حمار'),
        ('جاموس', 'جاموس'),
        ('جميع الانواع', 'جميع الأنواع')
    ], string='نوع الحيوان', required=True, default='جميع الانواع')

    age_days = fields.Integer(
        string='العمر (أيام)',
        required=True,
        help='العمر المطلوب للتطعيم بالأيام'
    )

    age_months = fields.Integer(
        string='العمر (شهور)',
        compute='_compute_age_months',
        store=True,
        help='العمر المطلوب للتطعيم بالشهور'
    )

    dose_number = fields.Integer(
        string='رقم الجرعة',
        required=True,
        default=1,
        help='رقم الجرعة (1، 2، 3...)'
    )

    interval_days = fields.Integer(
        string='الفترة للجرعة التالية (أيام)',
        help='عدد الأيام للجرعة التالية'
    )

    dosage = fields.Char(
        string='الجرعة',
        help='كمية الجرعة المطلوبة'
    )

    administration_route = fields.Selection([
        ('intramuscular', 'عضلي'),
        ('subcutaneous', 'تحت الجلد'),
        ('intravenous', 'وريدي'),
        ('oral', 'فموي'),
        ('nasal', 'أنفي'),
        ('other', 'أخرى')
    ], string='طريقة الإعطاء')

    is_mandatory = fields.Boolean(
        string='إجباري',
        default=True,
        help='هل هذا التطعيم إجباري؟'
    )

    notes = fields.Text(string='ملاحظات')
    active = fields.Boolean(default=True)

    @api.depends('age_days')
    def _compute_age_months(self):
        for rec in self:
            rec.age_months = rec.age_days // 30 if rec.age_days else 0

    # ✅ الحصول على الحيوانات التي تحتاج تطعيم
    def get_animals_needing_vaccination(self):
        """الحصول على الحيوانات التي تحتاج هذا التطعيم"""
        domain = [
            ('status', '=', 'alive'),
            ('age', '>=', self.age_days),
        ]
        
        if self.animal_type != 'all':
            domain.append(('type', '=', self.animal_type))
        
        animals = self.env['livestock.animal'].search(domain)
        
        # تصفية الحيوانات التي لم تحصل على هذا التطعيم
        animals_needing = animals.filtered(
            lambda a: not a.vaccination_doses.filtered(
                lambda d: d.vaccine_type == self.vaccine_type and 
                         d.dose_number == self.dose_number and 
                         d.status == 'completed'
            )
        )
        
        return animals_needing

class VeterinaryTreatment(models.Model):
    _name = 'veterinary.treatment'
    _description = 'علاج بيطري'
    _rec_name = 'name'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='اسم العلاج',
        required=True,
        tracking=True
    )
    
    animal_id = fields.Many2one(
        'livestock.animal',
        string='الحيوان',
        required=True,
        tracking=True
    )
    
    date = fields.Date(
        string='تاريخ العلاج',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    treatment_type = fields.Selection([
        ('vaccination', 'تطعيم'),
        ('medication', 'دواء'),
        ('surgery', 'جراحة'),
        ('checkup', 'فحص دوري'),
        ('emergency', 'طوارئ'),
        ('other', 'أخرى')
    ], string='نوع العلاج', required=True, default='checkup', tracking=True)
    
    veterinarian = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    
    diagnosis = fields.Text(
        string='التشخيص',
        tracking=True
    )
    
    treatment_details = fields.Text(
        string='تفاصيل العلاج',
        tracking=True
    )
    
    medication = fields.Char(
        string='الدواء المستخدم',
        tracking=True
    )
    
    dosage = fields.Char(
        string='الجرعة',
        tracking=True
    )
    
    cost = fields.Float(
        string='التكلفة',
        tracking=True
    )
    
    next_visit_date = fields.Date(
        string='موعد الزيارة القادمة',
        tracking=True
    )
    
    status = fields.Selection([
        ('scheduled', 'مجدول'),
        ('in_progress', 'جاري'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ], string='الحالة', default='scheduled', tracking=True)
    
    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )
    
    @api.model
    def create(self, vals):
        # إنشاء نشاط تذكير للزيارة القادمة
        treatment = super().create(vals)
        if treatment.next_visit_date:
            treatment._create_next_visit_activity()
        return treatment
    
    def write(self, vals):
        result = super().write(vals)
        if 'next_visit_date' in vals:
            for record in self:
                if record.next_visit_date:
                    record._create_next_visit_activity()
        return result
    
    def _create_next_visit_activity(self):
        """إنشاء نشاط تذكير للزيارة القادمة"""
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=self.next_visit_date,
            summary=f'زيارة بيطرية للحيوان {self.animal_id.name}',
            note=f'موعد الزيارة البيطرية القادمة للحيوان {self.animal_id.name}'
        )


class VeterinaryVaccination(models.Model):
    _name = 'veterinary.vaccination'
    _description = 'تطعيم'
    _rec_name = 'vaccine_name'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    animal_id = fields.Many2one(
        'livestock.animal',
        string='الحيوان',
        required=True,
        tracking=True
    )
    
    vaccine_name = fields.Char(
        string='اسم التطعيم',
        required=True,
        tracking=True
    )
    
    date = fields.Date(
        string='تاريخ التطعيم',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    batch_number = fields.Char(
        string='رقم الدفعة',
        tracking=True
    )
    
    manufacturer = fields.Char(
        string='الشركة المصنعة',
        tracking=True
    )
    
    expiry_date = fields.Date(
        string='تاريخ انتهاء الصلاحية',
        tracking=True
    )
    
    next_vaccination_date = fields.Date(
        string='موعد التطعيم القادم',
        tracking=True
    )
    
    veterinarian = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    
    cost = fields.Float(
        string='التكلفة',
        tracking=True
    )
    
    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )
    
    @api.constrains('expiry_date', 'date')
    def _check_expiry_date(self):
        for record in self:
            if record.expiry_date and record.date and record.expiry_date < record.date:
                raise ValidationError(_('تاريخ انتهاء الصلاحية لا يمكن أن يكون قبل تاريخ التطعيم'))


class VeterinaryCheckup(models.Model):
    _name = 'veterinary.checkup'
    _description = 'فحص بيطري'
    _rec_name = 'name'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='اسم الفحص',
        required=True,
        tracking=True
    )
    
    animal_id = fields.Many2one(
        'livestock.animal',
        string='الحيوان',
        required=True,
        tracking=True
    )
    
    date = fields.Date(
        string='تاريخ الفحص',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    checkup_type = fields.Selection([
        ('routine', 'فحص دوري'),
        ('pregnancy', 'فحص حمل'),
        ('illness', 'فحص مرض'),
        ('pre_sale', 'فحص ما قبل البيع'),
        ('post_purchase', 'فحص ما بعد الشراء'),
        ('other', 'أخرى')
    ], string='نوع الفحص', required=True, default='routine', tracking=True)
    
    veterinarian = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    
    weight = fields.Float(
        string='الوزن (كجم)',
        tracking=True
    )
    
    temperature = fields.Float(
        string='درجة الحرارة (°م)',
        tracking=True
    )
    
    heart_rate = fields.Integer(
        string='معدل ضربات القلب',
        tracking=True
    )
    
    general_condition = fields.Selection([
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('poor', 'ضعيف'),
        ('critical', 'حرج')
    ], string='الحالة العامة', tracking=True)
    
    findings = fields.Text(
        string='نتائج الفحص',
        tracking=True
    )
    
    recommendations = fields.Text(
        string='التوصيات',
        tracking=True
    )
    
    next_checkup_date = fields.Date(
        string='موعد الفحص القادم',
        tracking=True
    )
    
    cost = fields.Float(
        string='التكلفة',
        tracking=True
    )
    
    notes = fields.Text(
        string='ملاحظات',
        tracking=True
    )
    
    @api.model
    def create(self, vals):
        checkup = super().create(vals)
        # تحديث وزن الحيوان إذا تم تسجيل وزن جديد
        if checkup.weight and checkup.animal_id:
            checkup.animal_id.weight = checkup.weight
        return checkup


class VeterinaryCare(models.Model):
    _name = 'veterinary.care'
    _description = 'رعاية بيطرية'
    _order = 'date desc'

    animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True, tracking=True)
    date = fields.Date(string='التاريخ', required=True, tracking=True)
    care_type = fields.Selection([
        ('vaccination', 'تطعيم'),
        ('treatment', 'علاج'),
        ('checkup', 'فحص دوري'),
        ('other', 'أخرى')
    ], string='نوع الخدمة', required=True, tracking=True)
    details = fields.Text(string='التفاصيل')
    vet_id = fields.Many2one(
        'res.partner',
        string='الطبيب البيطري',
        domain=[('category_id.name', 'ilike', 'طبيب')],
        tracking=True
    )
    cost = fields.Float(string='التكلفة', digits=(10,2))
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)



class AnimalFood(models.Model):
  _name='livestock.food.data' 
  _description = 'بيانات التغذية'
  _inherit = ['mail.thread', 'mail.activity.mixin']


  name=fields.Char(string='الوصف', compute='_compute_name', store=True)
  animal_id = fields.Many2one('livestock.animal',string='الحيوان', required=True, ondelete='cascade')
  product = fields.Many2many('product.template',string='المنتجات', required=True)
  farm=fields.Many2one('livestock.farm', string='الحظيرة', required=True)
  exchange=fields.Selection([
    ('weight','الوزن'),
    ('age','العمر'),
    ('unit','الوحده'),
  ],string='طريقة الصرف', required=True)
  company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
  line_ids = fields.One2many('livestock.food.data.line','food_date_ids')

  @api.depends('farm', 'exchange')
  def _compute_name(self):
        exchange_map = {
            'weight': 'الوزن',
            'age': 'العمر',
            'unit': 'الوحدة',
        }
        for rec in self:
            if rec.farm and rec.exchange:
                rec.name = f"{rec.farm.name} ب {exchange_map.get(rec.exchange, '')}"
            else:
                rec.name = False
  
  def action_open_lines_popup(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'بنود التغذية',
            'res_model': 'livestock.food.data.line',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('Livestock.view_livestock_food_data_line_tree_popup').id, 'list'),
                (False, 'form'),
            ],
            'domain': [('food_date_ids', '=', self.id)],
            'context': {
                'default_food_date_ids': self.id,
            },
            'target': 'new',
        }



class AnimalFoodLine(models.Model):
  _name='livestock.food.data.line' 
  _description = 'بنود بيانات التغذية'
  _order = 'date desc'

  animal_id = fields.Many2one('livestock.animal',string='الحيوان',ondelete='cascade')
  food_date_ids = fields.Many2one('livestock.food.data')
  products = fields.Many2one('product.template', string='المنتج')
  date = fields.Date(string='التاريخ')
  weight = fields.Integer(string='الوزن')
  quantity = fields.Float(string='الكمية')
  editing = fields.Selection([
    ('big_qty','كميات كبيرة'),
    ('small_qty','كميات صغيرة'),
    ('update','تعديل معدلة'),
    ('improve','تحسين'),
  ],string='لماذا التعديل')
  des = fields.Text(string='الشرح')



class ScalesAnimal(models.Model):
  _name='livestock.scales' 
  _description = ' موازين الحيوان'
  _inherit = ['mail.thread', 'mail.activity.mixin']


  name=fields.Char(string='الوصف')
  animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True, ondelete='cascade')
  last_weight=fields.Float(string='اخر وزن',compute='_compute_last_weight')
  trans_pers=fields.Float(string='معدل التحويل')
  status = fields.Selection(
    related='animal_id.status',
    string='الحالة',
    store=True,
    readonly=True
)
  company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company, required=True)
  line_ids = fields.One2many('livestock.scales.line','scales_id')
  @api.depends('line_ids.weight', 'line_ids.date')
  def _compute_last_weight(self):
        for rec in self:
            if rec.line_ids:
                last_line = rec.line_ids.sorted(
                    key=lambda l: l.date or fields.Date.today(),
                    reverse=True
                )[0]
                rec.last_weight = last_line.weight
            else:
                rec.last_weight = 0


class ScalesAnimalLine(models.Model):
  _name='livestock.scales.line' 
  _description = 'بنود موازين الحيوان'
  _order = 'date desc'

  animal_id = fields.Many2one('livestock.animal', string='الحيوان', required=True, ondelete='cascade')
  scales_id = fields.Many2one('livestock.scales')
  date = fields.Date(string='التاريخ')
  weight = fields.Integer(string='الوزن', default='1')
  we_emp = fields.Many2one('hr.employee', string='موظف الوزن')
  prog_pers = fields.Float(string='نسبة التقدم', compute='_compute_progress', store=True)
  date_diff = fields.Integer(string='فرق الأيام', compute='_compute_date_diff', store=True)

  @api.model
  def create(self, vals):
        if vals.get('scales_id') and not vals.get('animal_id'):
            scale = self.env['livestock.scales'].browse(vals['scales_id'])
            vals['animal_id'] = scale.animal_id.id

        return super().create(vals)

  @api.depends('weight', 'scales_id.line_ids.weight', 'scales_id.line_ids.date')
  def _compute_progress(self):
        for rec in self:
            progress = 0
            if rec.scales_id:
                lines = rec.scales_id.line_ids.sorted(
                    key=lambda l: l.date or fields.Date.today(),
                    reverse=True
                )

                for i, line in enumerate(lines):
                    if line.id == rec.id:
                        if i < len(lines) - 1:
                            older_line = lines[i + 1]
                            # ✅ التحقق من إن الوزن القديم مش صفر
                            if older_line.weight:
                                progress = ((line.weight - older_line.weight) / older_line.weight)

            rec.prog_pers = progress  
    
  @api.depends('date', 'scales_id.line_ids')
  def _compute_date_diff(self):
        for rec in self:
            diff = 0
            if rec.scales_id:
                lines = rec.scales_id.line_ids.sorted(key=lambda l: l.date or fields.Date.today(), reverse=True)
                for i, line in enumerate(lines):
                    if line.id == rec.id:
                        if i < len(lines) - 1:
                            next_line = lines[i + 1]
                            if line.date and next_line.date:
                                diff = (line.date - next_line.date).days
                            else:
                                diff = 0
                        else:
                            diff = 0
            rec.date_diff = diff


class DailyFeeding(models.Model):
    _name = 'daily.feeding'
    _description = 'تغذية يومية'
    _order = 'feeding_date desc, create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    feeding_date = fields.Date(string='تاريخ', required=True, default=fields.Date.context_today, tracking=True)
    farm_ids = fields.Many2many('livestock.farm',string='الحظائر',required=True,tracking=True,help='اختر الحظائر التي تريد تسجيل التغذية لها')
    line_ids = fields.One2many('daily.feeding.line','feeding_id',string='بنود التغذية')

    @api.onchange('farm_ids')
    def _onchange_farm_ids(self):

        self.line_ids = [(5,0,0)]

        foods = self.env['livestock.food.data'].search([
            ('farm', 'in', self.farm_ids.ids)
        ])

        animals = self.env['livestock.animal'].search([
            ('farm_id', 'in', self.farm_ids.ids)
        ])

        lines = []

        for animal in animals:
            for food in foods:
                if animal.farm_id == food.farm:
                    for product in food.product:
                        lines.append((0,0,{
                            'animal_id': animal.id,
                            'product_id': product.id,
                        }))

        self.line_ids = lines




class DailyFeedingLine(models.Model):
    _name = 'daily.feeding.line'
    _description = 'بند التغذية اليومية'
    _order = 'farm_id, animal_id'

    feeding_id = fields.Many2one('daily.feeding',string='سجل التغذية',ondelete='cascade')
    animal_id = fields.Many2one('livestock.animal',string='الحيوان', domain="[('farm_id', 'in', parent.farm_ids)]")
    farm_id = fields.Many2one('livestock.farm',string='الحظيرة',related='animal_id.farm_id',store=True,readonly=True)
    product_id = fields.Many2one('product.template',string='المنتج (نوع العلف)')
    required_quantity = fields.Float(string='الكمية المطلوبة',default=0.0,help='الكمية المطلوبة من هذا المنتج للحيوان')
    last_weight = fields.Float(string='آخر وزن (كجم)',help='آخر وزن مسجل للحيوان')