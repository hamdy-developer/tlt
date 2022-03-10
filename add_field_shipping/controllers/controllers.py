# -*- coding: utf-8 -*-
# from odoo import http


# class AddFieldShipping(http.Controller):
#     @http.route('/add_field_shipp/add_field_shipp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_field_shipp/add_field_shipp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_field_shipp.listing', {
#             'root': '/add_field_shipp/add_field_shipp',
#             'objects': http.request.env['add_field_shipp.add_field_shipp'].search([]),
#         })

#     @http.route('/add_field_shipp/add_field_shipp/objects/<model("add_field_shipp.add_field_shipp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_field_shipp.object', {
#             'object': obj
#         })
