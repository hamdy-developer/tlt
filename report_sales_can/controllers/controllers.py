# -*- coding: utf-8 -*-
# from odoo import http


# class ReportSalesCan(http.Controller):
#     @http.route('/report_sales_can/report_sales_can/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_sales_can/report_sales_can/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_sales_can.listing', {
#             'root': '/report_sales_can/report_sales_can',
#             'objects': http.request.env['report_sales_can.report_sales_can'].search([]),
#         })

#     @http.route('/report_sales_can/report_sales_can/objects/<model("report_sales_can.report_sales_can"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_sales_can.object', {
#             'object': obj
#         })
