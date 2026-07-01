# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contract_ids = fields.One2many(
        'smart.contract', 
        'partner_id', 
        string='Contracts'
    )
    contract_count = fields.Integer(
        string='Contract Count', 
        compute='_compute_contract_count'
    )

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for partner in self:
            partner.contract_count = len(partner.contract_ids)

    def action_view_partner_contracts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('smart_contract_ai.action_smart_contract')
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action