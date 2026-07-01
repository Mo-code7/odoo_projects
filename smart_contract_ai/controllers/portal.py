# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError
from datetime import datetime

class CustomerPortalContracts(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortalContracts, self)._prepare_home_portal_values(counters)
        if 'contract_count' in counters:
            partner = request.env.user.partner_id
            contract_count = request.env['smart.contract'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['contract_count'] = contract_count
        return values

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SmartContract = request.env['smart.contract']

        domain = [('partner_id', '=', partner.id)]

        # Count contracts for pager
        contract_count = SmartContract.search_count(domain)
        
        # Pager definition
        pager = portal_pager(
            url="/my/contracts",
            total=contract_count,
            page=page,
            step=10
        )
        
        # Search contracts
        contracts = SmartContract.search(
            domain,
            limit=10,
            offset=pager['offset'],
            order="id desc"
        )

        values.update({
            'contracts': contracts,
            'page_name': 'contract',
            'pager': pager,
            'default_url': '/my/contracts',
        })
        return request.render("smart_contract_ai.portal_my_contracts", values)

    @http.route(['/my/contract/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_my_contract_detail(self, contract_id, access_token=None, **kw):
        try:
            # Sudo is not used directly to ensure security, but we handle access validation
            contract = request.env['smart.contract'].browse(contract_id)
            # Ensure the contract belongs to the current user's partner, or the user is a manager
            is_manager = request.env.user.has_group('smart_contract_ai.group_contract_manager')
            if not is_manager and contract.partner_id.id != request.env.user.partner_id.id:
                raise AccessError(_("You are not authorized to access this contract."))
        except Exception:
            return request.redirect('/my/home')

        values = {
            'contract': contract,
            'page_name': 'contract_detail',
        }
        return request.render("smart_contract_ai.portal_contract_page", values)

    @http.route(['/my/contract/<int:contract_id>/accept'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_contract_accept(self, contract_id, **post):
        contract = request.env['smart.contract'].browse(contract_id)
        is_manager = request.env.user.has_group('smart_contract_ai.group_contract_manager')
        
        if not is_manager and contract.partner_id.id != request.env.user.partner_id.id:
            raise AccessError(_("You are not authorized to sign this contract."))

        signer_name = post.get('signer_name')
        if not signer_name:
            return request.redirect(f'/my/contract/{contract_id}?error=missing_signature')

        # Record signature details
        contract.write({
            'signed_by': signer_name,
            'signature_date': datetime.now(),
        })
        
        # Log chatter message
        contract.message_post(
            body=_("Contract signed online by %s via customer portal.") % signer_name
        )
        
        return request.redirect(f'/my/contract/{contract_id}?success=signed')
