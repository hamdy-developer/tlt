# -*- coding: utf-8 -*-
# from odoo import http


# class EditReportSales(http.Controller):
#     @http.route('/edit_report_sales/edit_report_sales/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/edit_report_sales/edit_report_sales/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('edit_report_sales.listing', {
#             'root': '/edit_report_sales/edit_report_sales',
#             'objects': http.request.env['edit_report_sales.edit_report_sales'].search([]),
#         })

#     @http.route('/edit_report_sales/edit_report_sales/objects/<model("edit_report_sales.edit_report_sales"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('edit_report_sales.object', {
#             'object': obj
#         })
