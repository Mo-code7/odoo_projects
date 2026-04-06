from odoo import models,fields


class Tag(models.Model):
    _name = 'tag'

    tag = fields.Char()

