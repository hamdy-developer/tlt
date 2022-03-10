# -*- coding: utf-8 -*-
# from odoo import http


# class MakeCancelInSale(http.Controller):
#     @http.route('/make_cancel_in_sale/make_cancel_in_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/make_cancel_in_sale/make_cancel_in_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('make_cancel_in_sale.listing', {
#             'root': '/make_cancel_in_sale/make_cancel_in_sale',
#             'objects': http.request.env['make_cancel_in_sale.make_cancel_in_sale'].search([]),
#         })

#     @http.route('/make_cancel_in_sale/make_cancel_in_sale/objects/<model("make_cancel_in_sale.make_cancel_in_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('make_cancel_in_sale.object', {
#             'object': obj
#         })
