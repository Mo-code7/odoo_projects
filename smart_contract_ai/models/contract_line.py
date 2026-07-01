# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SmartContractLine(models.Model):
    _name = 'smart.contract.line'
    _description = 'Contract Line Item'

    contract_id = fields.Many2one(
        'smart.contract', 
        string='Contract Reference', 
        required=True, 
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', 
        string='Service / Product', 
        required=True
    )
    name = fields.Text(
        string='Description', 
        required=True
    )
    quantity = fields.Float(
        string='Quantity', 
        default=1.0, 
        required=True
    )
    price_unit = fields.Monetary(
        string='Unit Price', 
        required=True, 
        currency_field='currency_id'
    )
    price_subtotal = fields.Monetary(
        string='Subtotal', 
        compute='_compute_price_subtotal', 
        store=True, 
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency', 
        related='contract_id.currency_id', 
        string='Currency', 
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.get_product_multiline_description_sale()
            self.price_unit = self.product_id.lst_price

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
