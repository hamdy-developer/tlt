from odoo import _, api, fields, models
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta


class tem_id_sales_lunch_date_xlsx(models.AbstractModel):
    _name = 'report.otif.tem_id_sales_lunch_date_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = 'Daily transcation Report'
            # One sheet by partner
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
            days = (obj.date_to - obj.date_from).days
            row += 1
            co = 0
            sheet.write(2, co, '', format1)
            sheet.write(3, co, 'Activated Merchants', format1)
            sheet.write(4, co, 'Merchants made 1 order', format1)
            sheet.write(5, co, 'Merchants made 2 order or more', format1)
            sheet.write(6, co, 'Total orders value', format1)
            sheet.write(7, co, 'Total number of order', format1)
            sheet.write(8, co, 'AVG value order', format1)
            sheet.write(9, co, 'Number of skus sold', format1)
            row += 1
            for day in range(0, days + 1):
                co += 1
                min = datetime.combine(obj.date_from + relativedelta(days=day), datetime.min.time())
                max = datetime.combine(obj.date_from + relativedelta(days=day), datetime.max.time())
                sales = self.env['sale.order'].search([('state', 'in', ['done', 'sale']),('date_order', '>=',min),('date_order', '<=',max)], order="id")
                co_sales=len(sales)
                total=0
                number_skus=0
                made1=0
                made2=0

                for sale in sales:
                    sales_made = self.env['sale.order'].search(
                        [('state', 'in', ['done', 'sale']), ('id','<',sale.id),('partner_id', '=', sale.partner_id.id)],order="id")
                    if sales_made:
                        made2+=1
                    else:
                        made1+=1
                    total+=sale.amount_total
                    for line in sale.order_line:
                        number_skus += line.product_uom_qty

                sheet.write(2, co, str(obj.date_from + relativedelta(days=day)), format2)
                sheet.write(3, co, self.env['res.partner'].search_count(
                    [('verified_date', '>=', obj.date_from + relativedelta(days=day)),
                     ('verified_date', '<', obj.date_from + relativedelta(days=day + 1)), ]), format2)
                sheet.write(4, co, made1, format2)
                sheet.write(5, co, made2, format2)
                sheet.write(6, co, total, format2)
                sheet.write(7, co, co_sales, format2)
                if co_sales:
                    sheet.write(8, co, total/co_sales, format2)
                sheet.write(9, co, number_skus, format2)

