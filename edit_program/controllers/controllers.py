# -*- coding: utf-8 -*-
# from odoo import http


# class EditProgram(http.Controller):
#     @http.route('/edit_program/edit_program/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/edit_program/edit_program/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('edit_program.listing', {
#             'root': '/edit_program/edit_program',
#             'objects': http.request.env['edit_program.edit_program'].search([]),
#         })

#     @http.route('/edit_program/edit_program/objects/<model("edit_program.edit_program"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('edit_program.object', {
#             'object': obj
#         })
