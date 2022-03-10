from odoo import api, fields, models

class sale_order(models.Model):
    _inherit = 'sale.order'

    def print_receipt(self):
        return self.env.ref('sale_order_report.id_sale_order_receipt').report_action(self)
