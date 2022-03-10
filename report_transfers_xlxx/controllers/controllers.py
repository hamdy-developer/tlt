# -*- coding: utf-8 -*-
# from odoo import http


# class ReportTransfersXlxx(http.Controller):
#     @http.route('/report_transfers_xlxx/report_transfers_xlxx/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_transfers_xlxx/report_transfers_xlxx/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_transfers_xlxx.listing', {
#             'root': '/report_transfers_xlxx/report_transfers_xlxx',
#             'objects': http.request.env['report_transfers_xlxx.report_transfers_xlxx'].search([]),
#         })

#     @http.route('/report_transfers_xlxx/report_transfers_xlxx/objects/<model("report_transfers_xlxx.report_transfers_xlxx"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_transfers_xlxx.object', {
#             'object': obj
#         })
