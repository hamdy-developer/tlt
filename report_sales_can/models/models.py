# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class product_category(models.Model):
    _inherit = 'product.category'

    designer_share = fields.Float(string="Designer Share %",  required=False, )
    i_s_share = fields.Float(string="I/S Share %",  required=False, )



class designer_share(models.TransientModel):
    _name = 'designer.share'
    _description = 'general ledger wizard'

    date_from = fields.Datetime(string="Date From", required=True, )
    date_to = fields.Datetime(string="Date To", required=True, )

    def export_product(self):
        return self.env.ref('report_sales_can.report_action_id_designer_share').report_action(self)




class GeneralLedgerAccount(models.AbstractModel):
    _name = 'report.report_sales_can.designer_share'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = 'designer share'
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
            sheet.set_column(row, 0, 15)
            sheet.set_column(row, 1, 10)
            sheet.set_column(row, 2, 15)
            sheet.set_column(row, 3, 15)
            sheet.set_column(row, 4, 15)
            sheet.set_column(row, 5, 20)
            sheet.set_column(row, 6, 20)
            sheet.set_column(row, 7, 10)
            sheet.set_column(row, 8, 10)
            sheet.set_column(row, 9, 10)
            sheet.write(row, 2, 'FROM : ' + str(obj.date_from), format0)
            sheet.write(row, 5, 'TO : ' + str(obj.date_to), format0)
            row += 1
            sheet.write(row, 0, 'Designer', format1)
            sheet.write(row, 1, 'Sum', format1)
            sheet.write(row, 2, 'Designer Share', format1)
            sheet.write(row, 3, 'I/S Share', format1)
            sheet.write(row, 4, 'Net profit ', format1)

            orders = self.env['pos.order'].search([
                ('date_order', '>=', obj.date_from),
                ('date_order', '<=', obj.date_to),
                ('state', 'in', ['paid','done','invoiced']),
            ])

            categorys=self.env['product.category'].search([])
            for category in categorys:
                products=self.env['product.product'].search([('categ_id','=',category.id)])
                lines=self.env['pos.order.line'].search([('product_id','in',products.ids),('order_id','in',orders.ids)])
                total=0
                for line in lines:
                    total+=line.price_subtotal
                if total>0:
                    row += 1
                    sheet.write(row, 0, str(category.name), format2)
                    sheet.write(row, 1, str(round(total,2)), format2)
                    if category.designer_share:
                        sheet.write(row, 2, str(round(total*(category.designer_share/100),2)), format2)
                    else:
                        sheet.write(row, 2, "0", format2)
                    if category.i_s_share:
                        sheet.write(row, 3, str(round(total*(category.i_s_share/100),2)), format2)
                    else:
                        sheet.write(row, 3, "0", format2)
                    sheet.write(row, 4, str(round(total*((100-category.i_s_share-category.designer_share)/100),2)), format2)