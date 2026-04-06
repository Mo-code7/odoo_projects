
from odoo import models,fields,api



class Property(models.Model):
    _name = 'property'
    _inherit = ['mail.thread','mail.activity.mixin']

    ref = fields.Char(default='New',readonly=1)
    name = fields.Char(translate=True)
    description = fields.Text(tracking=1)
    postcode = fields.Char()
    owner = fields.Char()
    tag = fields.Char()
    date_available = fields.Date(tracking=1)
    expected_price = fields.Float()
    selling_price = fields.Float()
    expected_selling_date = fields.Date()
    is_late = fields.Boolean()
    diff = fields.Float(compute='_compute_diff' , store=1 , readonly=1)
    bedrooms = fields.Integer()
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection([
        ('north','North'),
        ('south','South'),
        ('west','West'),
        ('east','East'),
    ])
    owner_id = fields.Many2one('owner')
    tag_ids = fields.Many2many('tag')
    line_ids = fields.One2many('property.line','properties_id')
    owner_address = fields.Char(related='owner_id.address', readonly=1)
    owner_phone = fields.Char(related='owner_id.phone', readonly=1)
    state = fields.Selection([
        ('draft','Draft'),
        ('pending','Pending'),
        ('sold','Sold'),
        ('closed', 'Closed'),
    ])
    active=fields.Boolean(default=True)
    # _sql_constraints=[('unique_name'),('unique("name")'),('This name is already exist')]

    # @api.constrian('name')
    # def _check_name_greater_zero(self):
    #     for rec in self:
    #         if rec.name==0:
    #             raise ValidationError('Please enter the valid number')
    #
    #
    #
    #     @api.model_create_multi
    #     def create(self,vals):
    #      res= super(Property,self).create(vals)
    #      print("inside create func")
    #      return res
    #
    #     @api.model
    #     def _search(self,domain,offset=0,limit=None,order=None,access_right_uid=None):
    #         res= super(Property,self)._search(domain,offset=0,limit=None,order=None,access_right_uid=None)
    #         print("inside search func")
    #         return res
    #
    #     @api.model_create_multi
    #     def write(self,vals):
    #         res= super(Property,self).write(vals)
    #         print("inside write func")
    #         return res
    #
    #     @api.model
    #     def unlink(self):
    #         res = super(Property, self).unlink()
    #         print("inside delete func")
    #         return res
    def action_draft(self):
        for rec in self:
            rec.state='draft'

    def action_pending(self):
        for rec in self:
            rec.state = 'pending'


    def action_sold(self):
        for rec in self:
            rec.state = 'sold'



    def action_closed(self):
        for rec in self:
            rec.state = 'closed'


    def check_expected_selling_date(self):
        property_ids=self.search([])
        for rec in property_ids:
            if rec.expected_selling_date and rec.expected_selling_date < fields.date.today():
                rec.is_late=True


    def action(self):
        print(self.env['owner'].create({
            'owner':'Moaz',
            'phone':'01050554233',
        }))

    # @api.depends('expected_price', 'selling_price')
    def _compute_diff(self):
        for rec in self:
            rec.diff = rec.expected_price - rec.selling_price

    @api.model
    def create(self , vals):
        res =super(Property,self).create(vals)
        if res.ref == 'New':
            res.ref=self.env['ir.sequence'].next_by_code('property_seq')
            return res

    def action_open_related_owner(self):
        action=self.env['ir.actions.actions']._for_xml_id('app_one.owner_action')
        view_id=self.env.ref('app_one.owner_view_form').id
        action['res.id']=self.owner_id.id
        action['views']=[[view_id,'form']]
        return action


    def action_open_change_state_wizard(self):
        action=self.env['ir.actions.actions']._for_xml_id('app_one.change_state_wizard_action')
        action['context']={'default_property_id':self.id}
        return action

    # def property_csv_file(self):



class PropertyLine(models.Model):
        _name = 'property.line'

        properties_id = fields.Many2one('property')
        area = fields.Float()
        description = fields.Char()

