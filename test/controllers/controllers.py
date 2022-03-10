# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response



class Test(http.Controller):

    @http.route('/test',type='json', methods=['POST'], auth='public', sitemap=False)
    def index(self, **kw):
        # """ {
        #      "params": {
        #          "name":name,
        #          "price":0.0
        #
        #      }}"""
        if kw.get('name', False):
            product=request.env['product.template'].sudo().search([('barcode','=',kw.get('name', False))])
            if product:
                if kw.get('price') == product.list_price:
                    return [False,product.name]
                else:
                    product.list_price=kw.get('price')
                    return [True,product.name]
            else:
                return ["not Found",product.name]




