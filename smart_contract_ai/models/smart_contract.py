# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)

class SmartContract(models.Model):
    _name = 'smart.contract'
    _description = 'AI-Powered Smart Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Contract Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: _('New')
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Client/Partner', 
        required=True, 
        tracking=True
    )
    start_date = fields.Date(
        string='Start Date', 
        required=True, 
        default=fields.Date.context_today, 
        tracking=True
    )
    end_date = fields.Date(
        string='End Date', 
        required=True, 
        tracking=True
    )
    contract_term_months = fields.Integer(
        string='Contract Term (Months)', 
        compute='_compute_contract_term', 
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Active'),
        ('pending_renewal', 'Pending Renewal'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, copy=False)
    
    line_ids = fields.One2many(
        'smart.contract.line', 
        'contract_id', 
        string='Contract Lines', 
        copy=True
    )
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        required=True, 
        default=lambda self: self.env.company.currency_id
    )
    
    total_amount = fields.Monetary(
        string='Total Value', 
        compute='_compute_total_amount', 
        currency_field='currency_id', 
        store=True, 
        tracking=True
    )
    
    raw_contract_text = fields.Text(
        string='Raw Contract text / OCR Input', 
        help='Paste contract terms here to simulate OCR or AI analysis'
    )
    
    ai_summary = fields.Html(
        string='AI Analytical Summary', 
        readonly=True,
        help='Summarized analysis provided by LLM engine'
    )
    
    signed_by = fields.Char(
        string='Signed By (Client)', 
        readonly=True, 
        copy=False
    )
    signature_date = fields.Datetime(
        string='Signature Timestamp', 
        readonly=True, 
        copy=False
    )
    is_signed = fields.Boolean(
        string='Is Signed', 
        compute='_compute_is_signed', 
        store=True
    )
    
    invoice_ids = fields.One2many(
        'account.move', 
        'contract_id', 
        string='Invoices', 
        readonly=True
    )
    invoice_count = fields.Integer(
        string='Invoice Count', 
        compute='_compute_invoice_count'
    )
    active = fields.Boolean(
        string='Active', 
        default=True
    )

    @api.depends('start_date', 'end_date')
    def _compute_contract_term(self):
        for record in self:
            if record.start_date and record.end_date:
                diff = record.end_date - record.start_date
                record.contract_term_months = max(1, round(diff.days / 30.0))
            else:
                record.contract_term_months = 0

    @api.depends('line_ids.price_subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('price_subtotal'))

    @api.depends('signed_by', 'signature_date')
    def _compute_is_signed(self):
        for record in self:
            record.is_signed = bool(record.signed_by and record.signature_date)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('Contract End Date must be after the Start Date.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('smart.contract') or _('New')
        return super(SmartContract, self).create(vals_list)

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('You cannot activate a contract without any lines.'))
            record.state = 'open'
            record.message_post(body=_("Contract Activated and Status set to Active."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Contract cancelled."))

    def action_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Reset to Draft state."))

    def action_run_ai_ocr(self):
        """
        Simulates an integration with LLM API (e.g. Gemini) to analyze contract documents.
        This parses the raw text and populates fields as well as a structured summary.
        """
        for record in self:
            if not record.raw_contract_text:
                raise UserError(_('Please provide contract text in the OCR Input field first.'))
            
            # Simulated AI Response Parsing
            text = record.raw_contract_text.lower()
            
            # Extracted keywords and values based on text content
            detected_value = 0.0
            if 'value' in text or 'total' in text:
                # Mock extracting values
                detected_value = record.total_amount or 15000.0
            
            sla_terms = "Standard 99.9% Uptime Support SLA"
            if 'sla' in text or 'support' in text:
                sla_terms = "Premium 99.99% Uptime SLA with 2-Hour Response Time"
                
            billing_cycle = "Monthly Invoicing Cycle"
            if 'annual' in text or 'yearly' in text:
                billing_cycle = "Annual Upfront Invoicing"
            
            # Construct a beautiful HTML analytical summary card
            ai_html = f"""
            <div class="card border-primary mb-3 shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h5 class="card-title mb-0"><i class="fa fa-magic"></i> AI Contract Analysis Report</h5>
                </div>
                <div class="card-body">
                    <p class="card-text text-muted">Document parsed successfully using Gemini API Model.</p>
                    <table class="table table-sm table-striped">
                        <tbody>
                            <tr>
                                <th><strong>Entity / Client</strong></th>
                                <td>{record.partner_id.name}</td>
                            </tr>
                            <tr>
                                <th><strong>Contract Duration</strong></th>
                                <td>{record.contract_term_months} Months ({record.start_date} to {record.end_date})</td>
                            </tr>
                            <tr>
                                <th><strong>Billing Terms</strong></th>
                                <td>{billing_cycle}</td>
                            </tr>
                            <tr>
                                <th><strong>Service SLA</strong></th>
                                <td><span class="badge badge-success bg-success">{sla_terms}</span></td>
                            </tr>
                            <tr>
                                <th><strong>Risk Factor</strong></th>
                                <td><span class="badge badge-info bg-info">Low Risk - Standard Terms</span></td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="alert alert-info mt-2">
                        <strong>AI Key Summary:</strong> This contract binds <em>{record.partner_id.name}</em> to a service term. 
                        The payment condition matches {billing_cycle}. 
                        Liability limits are standard, and intellectual property ownership remains with the vendor.
                    </div>
                </div>
            </div>
            """
            record.write({
                'ai_summary': ai_html
            })
            record.message_post(body=_("AI contract analysis executed successfully. Summary updated."))

    def action_generate_invoice(self):
        """
        Creates a draft customer invoice from the contract lines.
        """
        self.ensure_one()
        if self.state not in ['open', 'pending_renewal']:
            raise UserError(_('You can only generate invoices for active or pending-renewal contracts.'))
            
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_('Please define a Sales Journal in Accounting Settings first.'))
            
        invoice_lines = []
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'name': f"Billing for {line.product_id.name} - Contract {self.name}",
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'account_id': line.product_id.property_account_income_id.id or self.env['account.account'].search([('account_type', '=', 'income')], limit=1).id,
            }))
            
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.context_today(self),
            'contract_id': self.id,
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.message_post(
            body=_("Invoice %s generated in Draft state from contract lines.") % invoice.name,
            partner_ids=[self.partner_id.id]
        )
        return invoice

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        action['domain'] = [('contract_id', '=', self.id)]
        action['context'] = {'default_move_type': 'out_invoice', 'default_contract_id': self.id}
        return action

    def action_send_renewal_reminder(self):
        self.ensure_one()
        template = self.env.ref('smart_contract_ai.email_template_contract_renewal_warning', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.message_post(body=_("Contract renewal warning email sent to client."))
        else:
            raise UserError(_("Mail template not found!"))

    @api.model
    def _cron_check_expiring_contracts(self):
        """
        Scheduled action run daily. Checks active contracts expiring in 30 days.
        Marks them as pending_renewal and creates activities for managers.
        """
        warning_date = date.today() + timedelta(days=30)
        contracts = self.search([
            ('state', '=', 'open'),
            ('end_date', '<=', warning_date)
        ])
        _logger.info("Cron found %s expiring contracts.", len(contracts))
        
        for contract in contracts:
            contract.write({'state': 'pending_renewal'})
            contract.action_send_renewal_reminder()
            
            # Create high-priority activity for manager
            manager_group = self.env.ref('smart_contract_ai.group_contract_manager')
            managers = manager_group.users if manager_group else self.env.user
            
            for manager in managers:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': _('Contract %s is expiring soon on %s. Please reach out to client for renewal.') % (contract.name, contract.end_date),
                    'summary': _('Contract Expiry Notification'),
                    'res_id': contract.id,
                    'res_model_id': self.env['ir.model']._get('smart.contract').id,
                    'user_id': manager.id,
                    'date_deadline': fields.Date.today()
                })


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one(
        'smart.contract', 
        string='Source Contract', 
        readonly=True, 
        copy=False
    )