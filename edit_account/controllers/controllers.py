# -*- coding: utf-8 -*-
# from odoo import http


# class EditAccount(http.Controller):
#     @http.route('/edit_account/edit_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/edit_account/edit_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('edit_account.listing', {
#             'root': '/edit_account/edit_account',
#             'objects': http.request.env['edit_account.edit_account'].search([]),
#         })

#     @http.route('/edit_account/edit_account/objects/<model("edit_account.edit_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('edit_account.object', {
#             'object': obj
#         })
