from odoo import models,fields


class AccountOrder(models.Model):
    _inherit='account.move'

    def action_do_something(self):
        print(self,'inside'
              )
