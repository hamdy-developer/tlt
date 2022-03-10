# -*- coding: utf-8 -*-


from odoo import _, api, fields, models
from datetime import datetime, time , timedelta




class GeneralLedgerAccount(models.AbstractModel):
    _name = 'report.vendor.tax.report.vendor_tax_report_temp'
    _inherit = 'report.report_xlsx.abstract'









    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
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
            sheet.set_column(row,0, 15)
            sheet.set_column(row,1, 10)
            sheet.set_column(row,2, 15)
            sheet.set_column(row,3, 15)
            sheet.set_column(row,4, 15)
            sheet.set_column(row,5, 20)
            sheet.set_column(row,6, 20)
            sheet.set_column(row,7, 10)
            sheet.set_column(row,8, 10)
            sheet.set_column(row,9, 10)
            sheet.write(row, 2, 'FROM : ' + str(obj.date_from), format0)
            sheet.write(row, 5, 'TO : ' + str(obj.date_to), format0)
            row+=1
            sheet.write(row, 0, 'Suppller ID', format1)
            sheet.write(row, 1, 'Suppller Name', format1)
            sheet.write(row, 2,'TAX ID', format1)
            sheet.write(row, 3, 'Type of Delivery', format1)
            sheet.write(row, 4,'Percentage ', format1)
            sheet.write(row, 5,'Amount', format1)
            sheet.write(row, 6,'comment', format1)
            row+=1

            taxes = self.env['account.move.line'].search([
                ('date', '>=', obj.date_from),
                ('date', '<=', obj.date_to),
                ('tax_base_amount', '>',0),
            ],order="date")
            for tax in taxes:
                sheet.write(row, 0, tax.partner_id.id, format0)
                sheet.write(row, 1, tax.partner_id.name, format0)
                sheet.write(row, 2, tax.tax_line_id.name, format0)
                sheet.write(row, 3, tax.tax_line_id.tax_scope, format0)
                sheet.write(row, 4, str(tax.tax_line_id.amount)+'%', format0)
                sheet.write(row, 5, tax.tax_base_amount, format0)
                sheet.write(row, 6, tax.move_id.name, format0)
                row+=1
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


                # if obj.partner_ids:
                #     for partner in obj.partner_ids:
                #         balance = 0
                #         total_debit=0
                #         total_credit=0
                #         row+=3
                #         row+=3

        #         account_move_lines_balance = self.env['account.move.line'].search([
        #             ('date', '<=', obj.date_from),
        #             ('partner_id', '=', partner.id),
        #             ('account_id', '=', self.env.ref('l10n_generic_coa.1_conf_a_recv').id),
        #         ],order="date")
        #         for move_balance in account_move_lines_balance:
        #             balance=balance+move_balance.debit-move_balance.credit
        #
        #         row+=1
        #         sheet.write(row, 3,"Initial balance", format2)
        #         sheet.write(row, 7, balance, format2)
        #         row+=1
        #
        #         for move in account_move_lines:
        #             if 'BILL' not in move.move_id.name:
        #                 total_credit+=move.credit
        #                 total_debit+=move.debit
        #                 balance = balance + move.debit - move.credit
        #                 sheet.write(row, 1, move.date, format2)
        #                 sheet.write(row, 2, move.move_id.name, format2)
        #                 sheet.write(row, 3, move.ref or "", format2)
        #                 sheet.write(row, 4, move.name, format2)
        #                 sheet.write(row, 5, move.debit, format2)
        #                 sheet.write(row, 6, move.credit, format2)
        #                 sheet.write(row, 7, balance, format2)
        #                 row+=1
        #                 if 'INV'  in move.move_id.name:
        #                     account_invoice=self.env['account.invoice'].sudo().search([('number','=',move.move_id.name)],limit=1)
        #                     sheet.write(row, 3, "product", format3)
        #                     sheet.write(row, 4, 'QTY', format3)
        #                     sheet.write(row, 5, 'Amount', format3)
        #                     row+=1
        #                     for line in account_invoice.invoice_line_ids:
        #                         sheet.write(row, 3, line.product_id.name, format2)
        #                         sheet.write(row, 4, line.quantity, format2)
        #                         sheet.write(row, 5, line.price_subtotal, format2)
        #                         row+=1
        #
        #
        #         sheet.write(row, 5, total_debit, format2)
        #         sheet.write(row, 6, total_credit, format2)
        #         sheet.write(row, 7, balance, format2)
        #
        #
        #         row+=3
    #
