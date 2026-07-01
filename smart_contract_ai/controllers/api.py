# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

# Mock API security token for demonstration
API_TOKEN = "odoo_secure_api_gateway_token_2026"

class SmartContractApiController(http.Controller):

    def _validate_auth(self, req_headers_or_params):
        """
        Validate custom authorization tokens.
        """
        auth_token = req_headers_or_params.get('Authorization') or req_headers_or_params.get('token')
        if auth_token and auth_token.startswith('Bearer '):
            auth_token = auth_token.split(' ')[1]
            
        if auth_token != API_TOKEN:
            return False
        return True

    @http.route('/api/v1/contracts', type='http', auth='public', methods=['GET'], csrf=False)
    def api_get_contracts(self, **kw):
        """
        Exposes GET endpoint to fetch contract list in JSON format.
        Example: GET /api/v1/contracts?token=odoo_secure_api_gateway_token_2026
        """
        if not self._validate_auth(kw):
            return request.make_response(
                json.dumps({'error': 'Unauthorized access - Invalid token'}),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
            
        contracts = request.env['smart.contract'].sudo().search([])
        result = []
        for contract in contracts:
            result.append({
                'id': contract.id,
                'reference': contract.name,
                'partner': {
                    'id': contract.partner_id.id,
                    'name': contract.partner_id.name,
                    'email': contract.partner_id.email
                },
                'start_date': str(contract.start_date) if contract.start_date else None,
                'end_date': str(contract.end_date) if contract.end_date else None,
                'total_value': contract.total_amount,
                'state': contract.state,
                'is_signed': contract.is_signed,
            })
            
        return request.make_response(
            json.dumps({'status': 'success', 'data': result}),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route('/api/v1/contract/create', type='json', auth='public', methods=['POST'], csrf=False)
    def api_create_contract(self, **post):
        """
        Exposes POST endpoint to create contracts from external CRM.
        Payload format:
        {
           "token": "odoo_secure_api_gateway_token_2026",
           "partner_id": 1,
           "start_date": "2026-06-10",
           "end_date": "2027-06-10",
           "raw_text": "Terms of cooperation ...",
           "lines": [
                {"product_id": 1, "quantity": 12.0, "price_unit": 500.0}
           ]
        }
        """
        # Read the payload
        body = request.dispatcher.jsonrequest
        if not self._validate_auth(body):
            return {'status': 'error', 'message': 'Unauthorized - Invalid API token'}
            
        partner_id = body.get('partner_id')
        start_date = body.get('start_date')
        end_date = body.get('end_date')
        lines_data = body.get('lines', [])
        
        if not partner_id or not start_date or not end_date:
            return {'status': 'error', 'message': 'Missing mandatory fields: partner_id, start_date, end_date'}
            
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            return {'status': 'error', 'message': f'Partner ID {partner_id} not found.'}
            
        # Compile lines values
        line_vals = []
        for line in lines_data:
            product_id = line.get('product_id')
            product = request.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                return {'status': 'error', 'message': f'Product ID {product_id} not found.'}
                
            line_vals.append((0, 0, {
                'product_id': product_id,
                'name': product.name,
                'quantity': line.get('quantity', 1.0),
                'price_unit': line.get('price_unit', product.lst_price),
            }))
            
        # Create contract record
        try:
            contract = request.env['smart.contract'].sudo().create({
                'partner_id': partner_id,
                'start_date': start_date,
                'end_date': end_date,
                'raw_contract_text': body.get('raw_text', ''),
                'line_ids': line_vals
            })
            return {
                'status': 'success',
                'contract_id': contract.id,
                'reference': contract.name,
                'message': 'Contract created and registered in draft state'
            }
        except Exception as e:
            _logger.error("API Contract Creation Failed: %s", str(e))
            return {'status': 'error', 'message': str(e)}
