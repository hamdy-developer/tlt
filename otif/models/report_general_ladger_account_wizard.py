# -*- coding: utf-8 -*-


from odoo import _, api, fields, models


class ImportantJournalLedger(models.TransientModel):
    _name = 'general.ledger.wizard'
    _description = 'general ledger wizard'

    date_from = fields.Date(string="Date From", required=True, )
    date_to = fields.Date(string="Date To", required=True, )

    def export_product(self):
        return self.env.ref('otif.report_action_id_general_ledger_wizard').report_action(self)

class sales_lunch_to_date(models.TransientModel):
    _name = 'sales.lunch.date'

    date_from = fields.Date(string="Date From", required=False, )
    date_to = fields.Date(string="Date To", required=False, )
    is_xlsx = fields.Boolean(string="Xlsx",  )
    activated_merchants = fields.Integer(string="", required=False,)
    merchants_1_order = fields.Integer(string="", required=False,)
    merchants_2_order = fields.Integer(string="", required=False, )
    total_order_value = fields.Integer(string="", required=False, )
    total_number_order = fields.Integer(string="", required=False, )
    avg_order = fields.Integer(string="", required=False, )
    number_skus = fields.Integer(string="", required=False, )


    def export_product(self):
        self.activated_merchants=self.env['res.partner'].search_count([('is_verified','=',True)])
        self.merchants_1_order=self.env['res.partner'].search_count([('sale_order_count','=',1)])
        self.merchants_2_order=self.env['res.partner'].search_count([('sale_order_count','>',1)])
        orders=self.env['sale.order'].search([('state','in',['done','sale'])])
        self.total_number_order=len(orders)
        total_order_value=0
        number_skus=0
        for order in orders:
            total_order_value+=order.amount_total
            for line in order.order_line:
                number_skus+=line.product_uom_qty
        self.total_order_value=total_order_value
        self.avg_order=self.total_order_value/self.total_number_order
        self.number_skus=number_skus
        return self.env.ref('otif.report_action_id_sales_lunch_date').report_action(self)
    def export_product_Xlsx(self):
        return self.env.ref('otif.report_action_id_sales_lunch_date_xlsx').report_action(self)
