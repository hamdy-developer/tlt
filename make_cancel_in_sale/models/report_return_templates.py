# -*- coding: utf-8 -*-


from odoo import _, api, fields, models
from datetime import datetime, time, timedelta


class GeneralLedgerAccount(models.AbstractModel):
    _name = 'report.make_cancel_in_sale.return_report_tem'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = 'Return Report'
            # # One sheet by partner
            sheet = workbook.add_worksheet(report_name)
            format0 = workbook.add_format({'font_size': 11, 'align': 'center'})
            format1 = workbook.add_format(
                {'font_size': 15, 'align': 'center', 'bold': True, 'bg_color': '#adad99', 'color': 'black',
                 'border': 5})
            format2 = workbook.add_format(
                {'font_size': 15, 'align': 'center', 'bold': True,
                 'border': 5})
            format3 = workbook.add_format(
                {'align': 'center', 'bold': True, 'bg_color': '#66665e', 'color': 'black', 'border': 5})
            row = 1
            sheet.set_column(row,0, 15)
            sheet.set_column(row,1, 10)
            sheet.set_column(row,2, 15)
            sheet.set_column(row,3, 15)
            sheet.set_column(row,4, 15)
            sheet.set_column(row,5, 20)
            if obj.date_from and obj.date_to:
                sheet.write(row, 2, 'FROM : ' + str(obj.date_from), format0)
                sheet.write(row, 5, 'TO : ' + str(obj.date_to), format0)
                stock_pickings = self.env['stock.picking'].sudo().search(
                    [('origin', 'ilike', 'Return'), ('state', '=', 'done'), ('date_done', '>=', obj.date_from),
                     ('date_done', '<=', obj.date_to)])
            elif obj.date_from:
                sheet.write(row, 2, 'FROM : ' + str(obj.date_from), format0)
                stock_pickings = self.env['stock.picking'].sudo().search(
                    [('origin', 'ilike', 'Return'), ('state', '=', 'done'), ('date_done', '>=', obj.date_from),
                     ])
            elif obj.date_to:
                sheet.write(row, 5, 'TO : ' + str(obj.date_to), format0)
                stock_pickings = self.env['stock.picking'].sudo().search(
                    [('origin', 'ilike', 'Return'), ('state', '=', 'done'),
                     ('date_done', '<=', obj.date_to)])
            else:
                stock_pickings = self.env['stock.picking'].sudo().search(
                    [('origin', 'ilike', 'Return'), ('state', '=', 'done')])

            row+=1
            sheet.write(row, 0, 'Serial No', format1)
            sheet.write(row, 1, 'SKU', format1)
            sheet.write(row, 2,'Description', format1)
            sheet.write(row, 3, 'Date', format1)
            sheet.write(row, 4,'Return Reason ', format1)
            sheet.write(row, 5,'Qty', format1)
            row+=1
            for rec in stock_pickings:
                for line in rec.move_ids_without_package:
                    sheet.write(row, 0, str(rec.origin), format0)
                    sheet.write(row, 1, str(line.product_id.default_code), format0)
                    sheet.write(row, 2, str(line.product_id.name), format0)
                    sheet.write(row, 3, str(rec.date_done), format0)
                    sheet.write(row, 4, str(line.cancel_reason_id.name), format0)
                    sheet.write(row, 5, str(line.product_uom_qty), format0)
                    row += 1
