# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GeneralLedgerAccount(models.AbstractModel):
    _name = 'report.report_transfers_xlxx.report_transfers_xlxx'
    _inherit = 'report.report_xlsx.abstract'




    def generate_xlsx_report(self, workbook, data, partners):
        report_name = 'Otif Report'
        # One sheet by partner
        sheet = workbook.add_worksheet(report_name)
        format0 = workbook.add_format({'font_size': 11, 'align': 'center'})
        format1 = workbook.add_format(
            {'font_size': 15, 'align': 'center', 'bold': True, 'bg_color': '#adad99', 'color': 'black','border': 5})
        format2 = workbook.add_format(
            {'font_size': 15, 'align': 'center', 'bold': True,
             'border': 5})
        format3 = workbook.add_format({'align': 'center', 'bold': True, 'bg_color': '#66665e', 'color': 'black','border': 5})
        row=1
        sheet.write(row, 0, 'REF', format1)
        sheet.write(row, 1, 'Product', format1)
        sheet.write(row, 2, 'Quantity', format1)
        sheet.write(row, 3,'UOM', format1)
        products={}
        for obj in partners:
            for line in obj.move_ids_without_package:
                if line.product_id not in products.keys():
                    products[line.product_id]=line.product_uom_qty
                else:
                    products[line.product_id]+=line.product_uom_qty
        for product in products.keys():
            row+=1
            sheet.write(row, 0, product.default_code, format0)
            sheet.write(row, 1, product.name, format0)
            sheet.write(row, 2, products[product], format0)
            sheet.write(row, 3, product.uom_id.name, format0)

    #     sheet.set_column(row,0, 15)
            #     sheet.set_column(row,1, 10)
            #     sheet.set_column(row,2, 15)
            #     sheet.set_column(row,3, 15)
            #     sheet.set_column(row,4, 15)
            #     sheet.set_column(row,5, 20)
            #     sheet.set_column(row,6, 20)
            #     sheet.set_column(row,7, 10)
            #     sheet.set_column(row,8, 10)
            #     sheet.set_column(row,9, 10)
            #     sheet.write(row, 2, 'FROM : ' + str(obj.date_from), format0)
            #     sheet.write(row, 5, 'TO : ' + str(obj.date_to), format0)
            #     row+=1

        #     sheet.write(row, 3, 'Customer no', format1)
        #     sheet.write(row, 4,'Customer name ', format1)
        #     sheet.write(row, 5,'Car ID', format1)
        #     sheet.write(row, 6,'Requsted time', format1)
        #     sheet.write(row, 7,'Delivery time', format1)
        #     sheet.write(row, 8,'Result', format1)
        #     sheet.write(row, 9,'Value', format1)
        #     row+=1
        # sales = self.env['sale.order'].search([
        #     ('date_order', '>=', obj.date_from),
        #     ('date_order', '<=', obj.date_to),
        #     ('state', '=', 'sale'),
        # ],order="date_order")
        # for order in sales:
        #     satatus="in progress"
        #     car=''
        #     for picking in order.picking_ids:
        #         if picking.state=='done':
        #             satatus='Delivered'
        #         car=picking.car_id.name
        #         Delivery_time=picking.date_done or ""
        #     if Delivery_time and order.date_order:
        #         Result=round((Delivery_time-order.date_order).total_seconds()/3600,1)
        #     else:
        #         Result=""
        #     sheet.write(row, 0, order.warehouse_id.name, format0)
        #     sheet.write(row, 1, satatus, format0)
        #     sheet.write(row, 2, order.name, format0)
        #     sheet.write(row, 3, order.partner_id.ref or "", format0)
        #     sheet.write(row, 4, order.partner_id.name, format0)
        #     sheet.write(row, 5, car or '', format0)
        #     sheet.write(row, 6, str(order.date_order), format0)
        #     sheet.write(row, 7, str(Delivery_time), format0)
        #     sheet.write(row, 8, Result, format0)
        #     sheet.write(row, 9, order.amount_total, format0)
        #     row+=1
