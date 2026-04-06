# -*- coding: utf-8 -*-
# from odoo import http


# class CongineerPosPrice(http.Controller):
#     @http.route('/congineer_pos_price/congineer_pos_price', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/congineer_pos_price/congineer_pos_price/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('congineer_pos_price.listing', {
#             'root': '/congineer_pos_price/congineer_pos_price',
#             'objects': http.request.env['congineer_pos_price.congineer_pos_price'].search([]),
#         })

#     @http.route('/congineer_pos_price/congineer_pos_price/objects/<model("congineer_pos_price.congineer_pos_price"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('congineer_pos_price.object', {
#             'object': obj
#         })

