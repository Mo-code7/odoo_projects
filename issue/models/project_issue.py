from odoo import models, fields, api
from odoo.exceptions import UserError
import base64 
import io
import xlsxwriter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from odoo import models, fields, api
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import base64, io

class ProjectIssue(models.Model):
    _name = 'project.issue'
    _description = 'Track project issues'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Problem Name', readonly=True)
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('project.issue')
        return super().create(vals)
    sale_order_id = fields.Many2one('sale.order', string='Sales order', required=False, store=True)
    partner_id = fields.Many2one(related='sale_order_id.partner_id',string='Client',store=True,readonly=True)
    # علاقة البنود بالمشكلة
    line_ids = fields.One2many('project.issue.line', 'issue_id', string='Problem items')
    line_count = fields.Integer(string='Number of Items', compute='_compute_line_count')

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('project.issue') or 'New'
    #     return super(ProjectIssue, self).create(vals)


    @api.model
    def get_singleton(self):
        """ارجاع السجل الوحيد، أو إنشاءه إذا لم يوجد"""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({'name': 'New Problem'})
        return rec

    def action_get_last_record(self):
        last_line = self.env['project.issue.line'].search([], order='id desc', limit=1)
        if last_line:
            return {
                'name': 'Last Problem Item',
                'type': 'ir.actions.act_window',
                'res_model': 'project.issue.line',
                'view_mode': 'form',
                'res_id': last_line.id,
                'target': 'current',
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Info',
                'message': 'No records found!',
                'type': 'warning',
                'sticky': False,
            }
        }

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def action_view_lines(self):
        self.ensure_one()
        return {
            'name': 'Problem Items',
            'type': 'ir.actions.act_window',
            'res_model': 'project.issue.line',
            'view_mode': 'tree,form',
            'domain': [('issue_id', '=', self.id)],
            'context': {'default_issue_id': self.id},
        }

    def action_set_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_set_resolved(self):
        for rec in self:
            rec.state = 'resolved'


class ProjectIssueLine(models.Model):
    _name = 'project.issue.line'
    _description = 'Problem List'
    _rec_name = 'description'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sale_order_id = fields.Many2one(related='issue_id.sale_order_id', string='Sales order', required=False, store=True)
    partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
        string='Client',
        store=True,
        readonly=True
    )
    pdf_file = fields.Binary(string='PDF File', readonly=True)
    pdf_file_name = fields.Char(string='PDF Filename', readonly=True)

    issue_id = fields.Many2one('project.issue', string='Problem', ondelete='cascade',readonly=True)
    product_id = fields.Many2one('product.product', string=' Product', required=False)
    created_by_id = fields.Many2one('res.users', string='Who added the item')
    issue_date = fields.Date(string='Issue date', default=fields.Date.context_today)
    actual_date = fields.Date(string='actual date' ,readonly=True)
    solution_date = fields.Date(string='action date', default=fields.Date.context_today)
    issue_type = fields.Selection([
        ('technical', 'Technical office'),
        ('production', 'Production'),
        ('installation', 'Installation'),
        ('supply_chain', 'Supply chain')
    ], string='DEPT', required=True)
    responsible_id = fields.Many2one('res.users', string='Assign To', required=False)
    resolved_by_id = fields.Many2one('res.users', string='By', required=False)
    who_caused_the_problem = fields.Many2one('res.users', string='Caused by', required=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In progress'),
        ('done', 'Done')
    ], string='Status', default='draft')

    image_url = fields.Char(string='URL')
    reason = fields.Text(string='Cause')
    production_id = fields.Many2one('mrp.production', string='MO', ondelete='set null', required=False)
    sale_order_id2 = fields.Many2one('sale.order', string="Sale Order 2")
    Causing = fields.Many2one('res.users', string='Caused by', store=True)
    maintenance_id = fields.Many2one('repair.order', string='RO', ondelete='set null', required=False)
    description = fields.Text(string='Description')
    solving_problem = fields.Text(string='Resolution')
    notes = fields.Text(string='Notes')
    final_solution = fields.Text(string='Final Solution')
    is_late = fields.Boolean()
    # ======= Actions =======
    def action_set_in_progress(self):
        for rec in self:
            if rec.state != 'in_progress':  # ← يمنع التكرار
                rec.state = 'in_progress'
                user_to_assign = rec.resolved_by_id
                if rec.issue_id and user_to_assign:
                    model = self.env['ir.model'].search([('model', '=', 'project.issue')], limit=1)
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'res_id': rec.issue_id.id,
                        'res_model_id': model.id,
                        'user_id': user_to_assign.id,
                        'summary': f"Follow-up: {rec.description or 'Issue Line'}",
                        'note': f"New action required for line: {rec.description or ''}",
                        'date_deadline': rec.solution_date,
                    })
                    rec.issue_id.message_post(
                        body=f"Activity assigned to <b>{user_to_assign.name}</b> for following up this issue."
                    )

    def action_set_resolved(self):
        for rec in self:
            if rec.state != 'done':  # ← يمنع التكرار
                rec.state = 'done'
                rec.actual_date = fields.Date.today()
                activities = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model']._get('project.issue').id),
                ('res_id', '=', rec.issue_id.id),
                ('user_id', '=', rec.resolved_by_id.id if rec.resolved_by_id else False),
                ('state', '=', 'planned')  # فقط النشاطات المفتوحة
            ])
                activities.action_done()  # ← ينهي الأنشطة
                ticket = self.env['helpdesk.ticket'].search([
                    ('name', '=', f"Follow up on {rec.issue_id.name or 'Issue'}"),
                    ('user_id', '=', rec.resolved_by_id.id if rec.resolved_by_id else False),
                    ('partner_id', '=', rec.partner_id.id if rec.partner_id else False),
                    ('team_id', '=', self.env['helpdesk.team'].search([], limit=1).id),
                ], limit=1)
                if ticket:
                    ticket.write({'stage_id': 4})    
    # def action_set_in_progress(self):
    #     for rec in self:
    #         rec.state = 'in_progress'
    #         user_to_assign =  rec.resolved_by_id
    #         model = self.env['ir.model'].search([('model', '=', 'project.issue')], limit=1)
    #         if rec.issue_id:              
    #             self.env['mail.activity'].create({
    #             'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
    #             'res_id': rec.issue_id.id,        # ← النشاط يظهر في الـ Issue
    #             'res_model_id': model.id,     # ← مهم جداً
    #             'user_id': user_to_assign.id,
    #             'summary': f"Follow-up: {rec.description or 'Issue Line'}",
    #             'note': f"New action required for line: {rec.description or ''}",
    #             'date_deadline': fields.Date.today(),
    #         })
    #         rec.issue_id.message_post(
    #         body=f"Activity assigned to <b>{user_to_assign.name}</b> for following up this issue."
    #     )

    # def action_set_resolved(self):
    #     for rec in self:
    #         rec.state = 'done'
    #         ticket = self.env['helpdesk.ticket'].search([
    #             ('name', '=', f"Follow up on {rec.issue_id.name or 'Issue'}"),
    #             ('user_id', '=', rec.resolved_by_id.id if rec.resolved_by_id else False),
    #             ('partner_id', '=', rec.partner_id.id if rec.partner_id else False),
    #             ('team_id', '=', self.env['helpdesk.team'].search([], limit=1).id),
    #         ], limit=1)
    #         if ticket:
    #             ticket.write({'stage_id': 4})



    # ---------------- تصدير Excel ----------------
    def action_export_excel(self):
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet("Problem Items")

        headers = ["Problem", "Description", "Type", "Responsible", "Solved By", "Caused By",
                   "State", "Issue Date", "Solution Date", "Product", "Sale Order", "Notes"]
        for col, head in enumerate(headers):
            sheet.write(0, col, head)

        row = 1
        for line in self:
            sheet.write(row, 0, line.issue_id.name or '')
            sheet.write(row, 1, line.description or '')
            sheet.write(row, 2, dict(line._fields['issue_type'].selection).get(line.issue_type, ''))
            sheet.write(row, 3, line.responsible_id.name or '')
            sheet.write(row, 4, line.resolved_by_id.name or '')
            sheet.write(row, 5, line.who_caused_the_problem.name or '')
            sheet.write(row, 6, dict(line._fields['state'].selection).get(line.state, ''))
            sheet.write(row, 7, str(line.issue_date or ''))
            sheet.write(row, 8, str(line.solution_date or ''))
            sheet.write(row, 9, line.product_id.name or '')
            sheet.write(row, 10, line.sale_order_id.name or '')
            sheet.write(row, 11, line.notes or '')
            row += 1

        workbook.close()
        buffer.seek(0)
        data = base64.b64encode(buffer.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'problem_items.xlsx',
            'datas': data,
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self[0].id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    # ---------------- تصدير PDF ----------------
    def action_export_pdf(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # عنوان التقرير
        elements.append(Paragraph("Project Issue Lines", styles['Title']))
        elements.append(Spacer(1, 12))

        # إعداد بيانات الجدول
        data = [[
            '#', 'Problem', 'Description', 'Type', 'Responsible', 'Solved By',
            'Caused By', 'Status', 'Issue Date', 'Solution Date', 'Product',
            'Sale Order', 'Notes'
        ]]

        for i, line in enumerate(self, start=1):
            data.append([
                i,
                line.issue_id.name or '',
                line.description or '',
                dict(line._fields['issue_type'].selection).get(line.issue_type, ''),
                line.responsible_id.name or '',
                line.resolved_by_id.name or '',
                line.who_caused_the_problem.name or '',
                dict(line._fields['state'].selection).get(line.state, ''),
                str(line.issue_date or ''),
                str(line.solution_date or ''),
                line.product_id.name or '',
                line.sale_order_id.name or '',
                line.notes or '',
            ])

        table = Table(data, colWidths=[15, 50, 60, 45, 45, 45, 45, 35, 40, 40, 50, 50, 40, 40, 60])
        table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkgrey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 6),  # حجم أصغر للخط
        ('BOTTOMPADDING', (0,0),(-1,0), 3),
        ('GRID', (0,0), (-1,-1), 0.2, colors.black),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        pdf_data = base64.b64encode(buffer.read())

        # حفظ المرفق
        first_line = self[0]
        first_line.pdf_file = pdf_data
        first_line.pdf_file_name = "Project_Issue_Lines.pdf"

        attachment = self.env['ir.attachment'].create({
            'name': 'Project_Issue_Lines.pdf',
            'datas': pdf_data,
            'type': 'binary',
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': first_line.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }
    def deadline(self):
        issue_ids=self.search([])
        for rec in issue_ids:
            if rec.solution_date and rec.solution_date < fields.date.today():
                rec.is_late=True
          
