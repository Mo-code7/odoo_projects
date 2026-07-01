# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta

class TestSmartContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSmartContract, cls).setUpClass()
        
        # Create a test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Client Corporation',
            'email': 'client@testcorp.com'
        })
        
        # Create a test service product
        cls.product = cls.env['product.product'].create({
            'name': 'SaaS Cloud Infrastructure Support',
            'type': 'service',
            'lst_price': 1500.0,
            'sale_ok': True
        })

    def test_01_contract_lifecycle_and_calculations(self):
        """
        Verify contract creation, line total, activation workflow, AI processing and invoicing.
        """
        # 1. Create a draft contract
        contract = self.env['smart.contract'].create({
            'partner_id': self.partner.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365), # 1 Year
            'raw_contract_text': 'This agreement outlines a total value of 18000 USD for SaaS Cloud Infrastructure Support.'
        })
        
        # Verify sequence and default states
        self.assertEqual(contract.state, 'draft', "Contract should default to Draft state.")
        self.assertNotEqual(contract.name, 'New', "Contract sequence reference should be generated.")
        self.assertEqual(contract.contract_term_months, 12, "Contract term calculation should be 12 months.")
        
        # 2. Add contract line items
        self.env['smart.contract.line'].create({
            'contract_id': contract.id,
            'product_id': self.product.id,
            'name': 'Annual SaaS Subscription Support',
            'quantity': 12.0,
            'price_unit': 1500.0
        })
        
        # Verify totals
        self.assertEqual(contract.total_amount, 18000.0, "Total contract amount must be sum of line subtotals.")
        
        # 3. Confirm/Activate contract
        contract.action_confirm()
        self.assertEqual(contract.state, 'open', "State should change to Active (open) upon activation.")
        
        # 4. Trigger simulated AI processing
        contract.action_run_ai_ocr()
        self.assertTrue(contract.ai_summary, "AI summary should be populated after running analysis.")
        self.assertIn("AI Contract Analysis Report", contract.ai_summary, "Summary should contain report headers.")
        
        # 5. Generate Invoice
        invoice = contract.action_generate_invoice()
        self.assertTrue(invoice, "Invoice should be created successfully.")
        self.assertEqual(invoice.state, 'draft', "Generated invoice should start in Draft status.")
        self.assertEqual(invoice.contract_id.id, contract.id, "Invoice must be linked to the source contract.")
        self.assertEqual(contract.invoice_count, 1, "Invoice count on contract should update to 1.")

    def test_02_contract_expiry_cron(self):
        """
        Verify that the scheduled cron job identifies expiring contracts and alerts the managers.
        """
        # Create a contract expiring in 15 days
        expiring_contract = self.env['smart.contract'].create({
            'partner_id': self.partner.id,
            'start_date': date.today() - timedelta(days=350),
            'end_date': date.today() + timedelta(days=15), # Expiring in 15 days (less than 30)
            'state': 'open' # Make active
        })
        
        # Create a line item so active validation rules pass if checked
        self.env['smart.contract.line'].create({
            'contract_id': expiring_contract.id,
            'product_id': self.product.id,
            'name': 'Cloud SLA Support',
            'quantity': 1.0,
            'price_unit': 500.0
        })
        
        # Trigger the cron method manually
        self.env['smart.contract']._cron_check_expiring_contracts()
        
        # Assert state changed to pending_renewal
        self.assertEqual(expiring_contract.state, 'pending_renewal', "Contract state should change to 'pending_renewal'.")
        
        # Check that a renewal activity was created for the user
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'smart.contract'),
            ('res_id', '=', expiring_contract.id)
        ])
        self.assertTrue(activities, "A mail.activity should be created warning managers about expiration.")
        self.assertIn("expiring soon", activities[0].note, "Activity details should mention expiration warning.")

    def test_03_invalid_dates_validation(self):
        """
        Test validation constraint that blocks start_date > end_date.
        """
        with self.assertRaises(ValidationError, msg="Odoo should block end_date being prior to start_date."):
            self.env['smart.contract'].create({
                'partner_id': self.partner.id,
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=1)
            })
