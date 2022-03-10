# -*- coding: utf-8 -*-


from odoo import _, api, fields, models


class vendor_tax_report(models.TransientModel):
    _name = 'vendor.tax.report'

    date_from = fields.Date(string="Date From", required=True, )
    date_to = fields.Date(string="Date To", required=True, )

    def export_product(self):
        return self.env.ref('vendor_tax_report.vendor_tax_report').report_action(self)
