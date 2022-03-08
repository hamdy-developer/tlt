# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        res= super(ReportSaleDetails, self).get_sale_details(date_start,date_stop,config_ids,session_ids)
        products=res.get('products',False)
        new_products=[]
        if products:
            for product in products:
                rec_product=self.env['product.product'].sudo().search([('id','=',product.get('product_id',False))],limit=1)
                product['brand']=rec_product.categ_id.name
                product['tax']='14%'
                product['tax_amount']=round(product.get('price_unit',0)*0.14/1.14,2)
                product['total_amount']=round(product.get('price_unit',0),2)
                product['price_unit']=round((product.get('price_unit',0)-product.get('tax_amount',0)),2)

                new_products.append(product)
        res['products']=new_products
        return res
