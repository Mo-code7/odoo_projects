from odoo.tests.common import TransactionCase
from odoo import fields

class TestProperty(TransactionCase):
        def setUp(self,*args,**kwargs):
            super(TestProperty, self).setUp()

            self.property_01_record=self.env['property'].create({
                'ref':'PTR1000',
                'name': 'Moaz',
                'postcode': '123456'
            })


        def test_01_property_values(self):
            property_id=self.property_01_record
            self.assertRecordValues(property_id,[{
                'ref': 'PTR1000',
                'name': 'Moaz',
                'postcode': '123456'
            }])