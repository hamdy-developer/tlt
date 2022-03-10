# -*- coding: utf-8 -*-
# import base64
# import json
# import logging
# import requests
from datetime import datetime, date

from odoo import http
from odoo.http import request
import ast

# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import logging

_logger = logging.getLogger(__name__)
HEADERS = {'Content-Type': 'application/json'}


class NatApi(http.Controller):

    def get_customer(self, token):
        customer = request.env['res.partner'].sudo().search([('token', '=', token)], limit=1)
        return customer

    def get_subcategory(self, category_id):
        categorys = request.env['product.category'].sudo().search([('parent_id', '=', category_id.id)],
                                                                  order="sequence")
        data = []
        for category in categorys:
            data.append(self.category_data(category))
        return data

    def category_data(self, category):
        base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        if category.attachment_id.local_url:
            image_url = base_path + category.attachment_id.local_url
        brand = "Null"

        return {'id': category.id, 'name': category.name, 'image': image_url, "soon": category.is_soon,
                'subcategory': self.get_subcategory(category), 'parent_id': category.parent_id.id or 0}

    def units_of_measure_data(self, uom):
        return {'id': uom.id, 'name': uom.name, "max_qty": uom.max_qty}

    def product_data(self, product, customer):
        out_of_stock = True
        if self.qty_available_product(product.product_variant_id.id, customer) > 0:
            out_of_stock = False
        base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        bundle = []
        if product.attachment_id.local_url:
            image_url = base_path + product.attachment_id.local_url
        brand = "Null"
        if product.brand_id:
            brand = {'id': product.brand_id.id, 'name': product.brand_id.name, }
        units_of_measure = [
            {'id': product.uom_id.id, 'name': product.uom_id.name, 'price': round(product.list_price, 2),
             "price after discount": round(product.price_discount, 2), "max_qty": product.max_qty}]
        if product.uom_ids:
            for uom in product.uom_ids:
                units_of_measure.append(
                    {'id': uom.uom_id.id, 'name': uom.uom_id.name, 'price': round(uom.price, 2),
                     "price after discount": round(uom.price_discount, 2), "max_qty": uom.max_qty})
        if product.bom_ids:
            product_bom = request.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', product.id)], limit=1)
            for line_bom in product_bom.bom_line_ids:
                bundle.append({
                    'product_data': self.product_data(line_bom.product_tmpl_id, customer),
                    'qty': line_bom.product_qty,
                    'units_of_measure': self.units_of_measure_data(line_bom.product_uom_id),
                }
                )
        description = ""
        if product.description_sale:
            description = product.description_sale
        note = ""
        if product.note:
            note = product.note
        if product.barcode:
            Barcode = product.barcode
        else:
            Barcode = ""
        return {'id': product.id, 'name': product.name, 'image': image_url, 'discount': product.is_discount,
                'discount_percentage': product.percentage, 'internal_reference': product.default_code,
                'Barcode': Barcode, 'brand': brand, 'units_of_measure': units_of_measure,
                "description": description, "note": note, 'bundle': bundle, 'out_of_stock': out_of_stock}

    def product_sort(self, products, customer):
        products_sort = []
        for product in products:
            if self.qty_available_product(product.product_variant_id.id, customer) > 0:
                products_sort.insert(0, product)
            else:
                products_sort.append(product)
        return products_sort

    def employee_data(self, employee):
        return {'id': employee.id, 'name': employee.name}

    def promotion_data(self, promotion):
        if not promotion.rule_date_from:
            base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            image_url = "Null"
            if promotion.attachment_id.local_url:
                image_url = base_path + promotion.attachment_id.local_url
            return {'id': promotion.id, 'name': promotion.name, 'image': image_url}
        else:
            if promotion.rule_date_from <= datetime.now():
                base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url = "Null"
                if promotion.attachment_id.local_url:
                    image_url = base_path + promotion.attachment_id.local_url

                return {'id': promotion.id, 'name': promotion.name, 'image': image_url}

    def brand_data(self, brand):
        base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        if brand.attachment_id.local_url:
            image_url = base_path + brand.attachment_id.local_url
        return {'id': brand.id, 'name': brand.name, 'image': image_url, }

    def best_seller(self, customer):
        stock_quant = request.env['stock.quant'].sudo().search(
            [('location_id', '=', request.env.ref('stock.stock_location_customers').id)], limit=20,
            order="quantity desc",
        )  # available_quantity'
        data = []
        for stock in stock_quant:
            if stock.product_id.active and stock.product_id.sale_ok:
                data.append(self.product_data(stock.product_id.product_tmpl_id, customer))
        return data

    def products_offers(self, customer=None):
        products_offer = request.env['product.template'].sudo().search(
            [('is_discount', '=', True)], order="date_start", )
        # , ('date_start', '<=', datetime.now().date)
        data = []
        products_offer = self.filter_product_qty_available(products_offer, customer)
        products_offer = self.product_sort(products_offer, customer)
        for product in products_offer:
            if product.active and product.sale_ok:
                data.append(self.product_data(product, customer))
        return data

    def sale_order_data(self, sale_order, customer=None):
        if sale_order.state != 'sale':
            sale_order.sudo().get_price_unit_liens()
            sale_order.sudo().recompute_coupon_lines()
        line_data = []
        bee_code = ""
        rest_is_on_promotion = 0
        rest_is_on_promotion_name = ""
        discount = 0
        state = 'لم يتم التأكد بعد'
        for line in sale_order.order_line:
            base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            image_url = "Null"
            if line.product_id.attachment_id.local_url:
                image_url = base_path + line.product_id.attachment_id.local_url
            if line.price_subtotal >= 0:
                # line_data.append({"id": line.id,
                #                   "product": {"id": line.product_id.id, "name": line.product_id.name,
                #                               "image": image_url}, "quantity": line.product_uom_qty,
                #                   "units_of_measure": {"id": line.product_uom.id,
                #                                        "name": line.product_uom.name},
                #                   "subtotal": line.price_subtotal,
                #                   "unit_price": line.price_unit, })
                subtotal_before_discount = line.price_subtotal
                unit_price_before_discount = line.price_unit
                if line.product_id.is_discount:
                    subtotal_before_discount = line.price_subtotal * 100 / (100 - line.product_id.percentage)
                    unit_price_before_discount = line.price_unit * 100 / (100 - line.product_id.percentage)
                max_qty = 0
                if line.product_id.uom_id.id == line.product_uom.id:
                    max_qty = line.product_id.max_qty
                else:
                    max_qty = request.env['product.unit_of_measure'].sudo().search(
                        [('uom_id', '=', line.product_uom.id), ('product_id', '=', line.product_id.product_tmpl_id.id)],
                        limit=1).max_qty

                line_data.append({"id": line.id,
                                  "product": {"id": line.product_id.id, "name": line.product_id.name,
                                              "image": image_url}, "quantity": line.product_uom_qty,
                                  "units_of_measure": {"id": line.product_uom.id,
                                                       "name": line.product_uom.name},
                                  'discount': line.product_id.is_discount,
                                  "subtotal": subtotal_before_discount,
                                  "subtotal_after_discount": line.price_subtotal,
                                  "unit_price": unit_price_before_discount,
                                  "unit_price_after_discount": line.price_unit,
                                  "max_qty": max_qty})
            else:
                discount += -line.price_subtotal
        pick = False
        delivery_date = "Null"
        if sale_order.delivery_date:
            delivery_date = "غدا (لا يتم التوصيل يوم الجمعه)"
            if sale_order.delivery_date == date.today():
                delivery_date = "اليوم (لا يتم التوصيل يوم الجمعه)"
        for picking in sale_order.picking_ids:
            if picking.state == 'done':
                pick = True
            else:
                pick = False
            if pick == False:
                break
        if sale_order.state == 'sale' and pick:
            state = 'تم التوصيل'
            delivery_date = "Null"
        elif sale_order.state == 'sale':
            state = 'قيد الانتظار'

        if sale_order.bee_code:
            bee_code = sale_order.bee_code
        if not discount:
            promotions = request.env['coupon.program'].sudo().search(
                ['|', ('rule_date_to', '=', False), ('rule_date_to', '>=', datetime.now())])
            for promotion in promotions:
                customers = request.env['res.partner'].sudo().search(
                    ast.literal_eval(promotion.rule_partners_domain))
                if promotion.rule_minimum_amount > sale_order.amount_untaxed >= promotion.rule_minimum_amount * 0.75 and customer.id in customers.ids:
                    rest_is_on_promotion = promotion.rule_minimum_amount - sale_order.amount_untaxed
                    rest_is_on_promotion_name = promotion.name
        minimum = request.env['ir.config_parameter'].sudo().get_param('nat.minimum_order', )
        viitas = 0
        if sale_order.partner_id.viitas_action:
            viitas = sale_order.partner_id.viitas

        return {"id": sale_order.id, "name": sale_order.name, "date": sale_order.date_order,
                "delivery_date": delivery_date,
                "total_befor_discount": round(sale_order.amount_untaxed + discount, 2),
                "tax": round(sale_order.amount_tax, 2),
                "discount": discount,
                "total": round(sale_order.amount_total, 2),
                "allowed": sale_order.is_allowed,
                "minimum_order": minimum,
                "payment_method_type": sale_order.payment_method_type,
                "payment_code": bee_code,
                'viitas': viitas,
                'state': state,
                "is_verified": sale_order.is_verified,
                "is_paid": sale_order.is_paid,
                "rest_is_on_promotion": rest_is_on_promotion,
                "rest_is_on_promotion_name": rest_is_on_promotion_name,
                "lines": line_data, }

    def customer_data(self, customer):
        area_data = {}
        if customer.area_id:
            area_data = {'id': customer.area_id.id, 'name': customer.area_id.name}
        governorate_data = {}
        if customer.governorate_id:
            governorate_data = {'id': customer.governorate_id.id, 'name': customer.governorate_id.name}
        customer_type_data = {}
        if customer.customer_type_id:
            customer_type_data = {'id': customer.customer_type_id.id, 'name': customer.customer_type_id.name}
        return {
            "token": customer.token,
            "password": customer.password,
            "name": customer.name,
            "shop_name": customer.shop_name,
            "email": customer.email,
            "mobile": customer.phone,
            "area": area_data,
            "governorate": governorate_data,
            "customer_type": customer_type_data,
            "zip": customer.zip,
            "street": customer.street,
            "street2": customer.street2,
            "is_verified": customer.is_verified,
            "active": customer.active,
            "lat": customer.x,
            "long": customer.y
        }

    def qty_available_product(self, product, customer, uom=None):
        warehousess = request.env['stock.warehouse'].sudo().search(
            [])
        warehouses = False
        for ware in warehousess:
            if customer.area_id.id in ware.area_ids.ids:
                warehouses = ware
        if not warehouses:
            warehouses = warehousess[0]

        stock_quant = request.env['stock.quant'].sudo().search(
            [('product_id', '=', product), ('location_id', '=', warehouses.stock_id.id), ])
        uom_id = request.env['uom.uom'].sudo().search(
            [('id', '=', uom)], limit=1)
        qty_available = 0
        max_qty = 0
        for stock in stock_quant:
            qty_available += stock.available_quantity
        product_id = request.env['product.product'].sudo().search([('id', '=', product)])
        if product_id.type == "consu":
            qty_available = 1000
        if uom_id:
            qty_available = round(qty_available * uom_id.factor, 2)
        if product_id.uom_id.id == uom_id.id:
            max_qty = product_id.max_qty
        else:
            max_qty = request.env['product.unit_of_measure'].sudo().search(
                [('uom_id', '=', uom), ('product_id', '=', product_id.product_tmpl_id.id)], limit=1).max_qty
        if max_qty < qty_available and max_qty != 0 and max_qty:
            qty_available = max_qty
        return qty_available

    def filter_product_qty_available(self, products=None, customer=None):
        data = request.env['product.template'].sudo()
        for product in products:
            if product.brand_id:
                data |= product
        return data
        return products

    @http.route('/api/check/customer', type='json', methods=['POST'], auth='public', sitemap=False)
    def check_customer(self, **kw):
        """{
            "params": {
                "mobile_number": "0100"
            }
        }"""
        if not kw:
            response = {"code": 401, "message": "All required data are missing!"}
            return response
        else:
            if kw.get('mobile_number', False):
                custome = request.env['res.partner'].sudo().search([('phone', '=', kw.get('mobile_number'))],
                                                                   limit=1)
                if custome:
                    response = {"code": 200, "message": "العميل بالفعل موجود", "data": True}
                    return response
                else:
                    response = {"code": 200, "message": "العميل غير موجود", "data": False}
                    otp = request.env['otp.partner'].sudo().create({
                        'name': kw.get('mobile_number')
                    })
                    otp.sudo().generate_otp()
                return response
            else:
                response = {"code": 401, "message": "All required data are missing!"}
                return response

    @http.route('/api/check/otp', type='json', methods=['POST'], auth='public', sitemap=False)
    def check_otp(self, **kw):
        """{
                    "params": {
                        "mobile_number":"mobile_number",
                        "otp":"otp"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "data is missing!"}
            return response
        else:
            if kw.get('mobile_number', False):
                otp = request.env['ir.config_parameter'].sudo().get_param('nat.otp_default')
                otp_customer = request.env['otp.partner'].sudo().search(
                    [('otp', '=', str(kw.get('otp'))),
                     ('name', '=', kw.get('mobile_number'))], limit=1)
                if otp_customer:
                    otp_customer.sudo().unlink()
                    response = {"code": 200, "message": "otp successful", "data": True}
                    return response
                if otp == kw.get('otp', False):
                    response = {"code": 200, "message": "otp successful", "data": True}
                    return response
            response = {"code": 400, "message": "الرقم السري خطأ!", "data": False}
            return response

    @http.route('/api/get/area', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_area(self, **kw):
        data = []
        ereas = request.env['area.area'].sudo().search([])
        for erea in ereas:
            data.append({'id': erea.id, 'name': erea.name})
        response = {"code": 200, "message": "All areas", "data": data}
        return response

    @http.route('/api/get/governorate', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_governorate(self, **kw):
        data_governorates = []
        governorates = request.env['governorate.governorate'].sudo().search([])
        for governorate in governorates:
            data_area = []
            ereas = request.env['area.area'].sudo().search([('governorate_id', '=', governorate.id)])
            for erea in ereas:
                data_area.append({'id': erea.id, 'name': erea.name})
            data_governorates.append({'id': governorate.id, 'name': governorate.name, 'areas': data_area})
        response = {"code": 200, "message": "All areas", "data": data_governorates}
        return response

    @http.route('/api/get/customer_type', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_customer_type(self, **kw):
        data = []
        customer_types = request.env['customer.type'].sudo().search([])
        for customer_type in customer_types:
            data.append({'id': customer_type.id, 'name': customer_type.name})
        response = {"code": 200, "message": "All areas", "data": data}
        return response

    @http.route('/api/get/advertisement', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_promotion_frist(self, **kw):
        data = []
        image_url = "Null"
        base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        promotion_frists = request.env['promotion.frist'].sudo().search([('active', '=', True)])
        for promotion_frist in promotion_frists:
            if promotion_frist.attachment_id.local_url:
                image_url = base_path + promotion_frist.attachment_id.local_url
            data.append({'id': promotion_frist.id, 'name': promotion_frist.name, 'image': image_url})
        response = {"code": 200, "message": "All areas", "data": data}
        return response

    @http.route('/api/create/customer', type='json', methods=['POST'], auth='public', sitemap=False)
    def create_customer(self, **kw):
        """{
                    "params": {
                        "name": "tttttttt",
                        "password": "123",
                        "shop_name": "shop_name",
                        "email": "email",
                        "mobile": "0100",
                        "area": "city",
                        "governorate_id": "governorate_id",
                        "customer_type_id": "customer_type_id",
                        "zip": "zip",
                        "street": "street",
                        "street2": "street2"
                        "lat": "lot"
                        "long": "long"
                        "sales_rep": "sales_rep"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "All required data are missing!"}
            return response
        else:
            customer = request.env['res.partner'].sudo().search([('phone', '=', kw.get('mobile'))], limit=1)
            area = request.env['area.area'].sudo().search([('id', '=', int(kw.get('area')))], limit=1)
            area_id = False
            if area:
                area_id = area.id
            governorate = request.env['governorate.governorate'].sudo().search(
                [('id', '=', int(kw.get('governorate_id', False)))], limit=1)
            governorate_id = False
            if governorate:
                governorate_id = governorate.id
            if customer:
                response = {"code": 400, "message": "العميل بالفعل موجود", "data": True}
                return response

            if kw.get('name', False) and kw.get('password', False):
                customer_type_id = False
                if kw.get('customer_type_id', False):
                    customer_type_id = int(kw.get('customer_type_id'))
                vals = {
                    'is_company': False,
                    'customer_rank': 1,
                    'type': 'private',
                    'name': kw.get('name'),
                    'shop_name': kw.get('shop_name'),
                    'email': kw.get('email'),
                    'phone': kw.get('mobile'),
                    'area_id': area_id,
                    'governorate_id': governorate_id,
                    'customer_type_id': customer_type_id,
                    'zip': kw.get('zip'),
                    'street': kw.get('street'),
                    'street2': kw.get('street2'),
                    'password': kw.get('password'),
                    'x': kw.get('lat', False),
                    'y': kw.get('long', False),
                    'device_id': kw.get('device_id', False),
                    # 'active': False,
                }

                new_customer = request.env['res.partner'].sudo().create(vals)
                employee_id = request.env['hr.employee'].sudo().search([('id', '=', kw.get('sales_rep'))],
                                                                       limit=1)
                new_customer.sudo().generate_token()
                new_customer.fcm_token = kw.get('fcm_token', False)
                if employee_id:
                    new_customer.employee_id = employee_id.id
                valus = self.customer_data(new_customer)
                response = {"code": 200, "message": "create new customer", "data": valus}
                return response
            else:
                response = {"code": 401, "message": "password or name is missing!"}
                return response

    @http.route('/api/edit/customer', type='json', methods=['POST'], auth='public', sitemap=False)
    def edit_customer(self, **kw):
        """{
                    "params": {
                        "token": "token",
                        "name": "tttttttt",
                        "password": "123",
                        "shop_name": "shop_name",
                        "email": "email",
                        "mobile": "0100",
                        "area": "city",
                        "governorate_id": "governorate_id",
                        'customer_type_id': customer_type_id,
                        "zip": "zip",
                        "street": "street",
                        "street2": "street2"
                        "lat": "lat"
                        "long": "long"
                    }
                }"""
        if not kw:
            response = {"result": {"code": 401, "message": "All required data are missing!"}}
            return response
        else:
            area = request.env['area.area'].sudo().search([('id', '=', int(kw.get('area', False)))], limit=1)
            area_id = False
            if area:
                area_id = area.id
            governorate = request.env['governorate.governorate'].sudo().search(
                [('id', '=', int(kw.get('governorate_id', False)))], limit=1)
            governorate_id = False
            if governorate:
                governorate_id = governorate.id
            if kw.get('name', False) and kw.get('password', False) and kw.get('token', False):
                customer_type_id = False
                if kw.get('customer_type_id', False):
                    customer_type_id = int(kw.get('customer_type_id'))
                vals = {
                    'is_company': False,
                    'customer_rank': 1,
                    'type': 'private',
                    'name': kw.get('name'),
                    'shop_name': kw.get('shop_name'),
                    'email': kw.get('email'),
                    'phone': kw.get('mobile'),
                    'area_id': area_id,
                    'governorate_id': governorate_id,
                    'customer_type_id': customer_type_id,
                    'zip': kw.get('zip'),
                    'street': kw.get('street'),
                    'street2': kw.get('street2'),
                    'password': kw.get('password'),
                    'x': kw.get('lat', False),
                    'y': kw.get('long', False),
                }
                customer = self.get_customer(kw.get('token'))
                if customer:
                    customer.sudo().write(vals)
                    vals = self.customer_data(customer)
                    response = {"code": 200, "message": "Edit customer data", "data": vals}
                    return response
                else:
                    response = {"code": 401, "token": "missing"}
                    return response
            else:
                response = {"code": 401, "message": "password or name or token is missing!"}
                return response

    @http.route('/api/delete/customer', type='json', methods=['POST'], auth='public', sitemap=False)
    def delete_customer(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "All required data are missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    customer.sudo().unlink()
                    response = {"code": 200, "message": "Customer deleted", "data": {}}
                    return response
                else:
                    response = {"code": 401, "token": "Not Exist"}
                    return response
            else:
                response = {"code": 401, "message": "token is missing!"}
                return response

    @http.route('/api/reset/password', type='json', methods=['POST'], auth='public', sitemap=False)
    def reset_password(self, **kw):
        """{
                    "params": {
                        "mobile": "0100",
                        "password": "123",
                        "otp": "otp",
                    }
                }"""
        if kw.get('otp', False):
            if not kw:
                response = {"code": 401, "message": "All required data are missing!"}
                return response
            else:
                if kw.get('mobile', False):
                    customer = request.env['res.partner'].sudo().search(
                        [('phone', '=', kw.get('mobile'))], limit=1)
                    if customer and not kw.get('password', False):
                        response = {"code": 200, "message": "otp successful", "data": True}
                        return response
                    if customer:
                        otp = request.env['ir.config_parameter'].sudo().get_param('nat.otp_default')
                        if customer.otp == str(kw.get('otp')) or customer.otp == otp:
                            customer.sudo().generate_token()
                            customer.sudo().password = kw.get('password')
                            customer.otp = False
                            # vals=self.customer_data(customer)
                            response = {"code": 200, "message": "تم تغير كلمة السر", "data": True}
                            return response

                    response = {"code": 401, "message": "العميل غير موجود", "data": False}
                    return response
                else:
                    response = {"code": 401, "message": "mobile or password is missing!"}
                    return response
        else:
            if not kw:
                response = {"code": 401, "message": "All required data are missing!"}
                return response
            else:
                if kw.get('mobile', False):
                    customer = request.env['res.partner'].sudo().search(
                        [('phone', '=', kw.get('mobile'))], limit=1)
                    if customer:
                        customer.sudo().generate_otp()
                        # customer.sudo().password = kw.get('password')
                        # vals = self.customer_data(customer)
                        response = {"code": 200, "message": "تم ارسال رساله بالرقم السري اليك", "data": True}
                        return response
                    else:
                        response = {"code": 401, "message": "العميل غير موجود", "data": False}
                        return response
                else:
                    response = {"code": 401, "message": "mobile or password is missing!"}
                    return response

    @http.route('/api/get/brand', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_brand(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "subcategory":"category_id"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    category = request.env['product.category'].sudo().search(
                        [('id', '=', int(kw.get('subcategory')))], order="sequence")
                    base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    image_url = "Null"
                    if category.attachment_id.local_url:
                        image_url = base_path + category.attachment_id.local_url
                    data = [{"id": 0, "name": "الكل", 'image': image_url}]
                    brand_ids = request.env['product.brand'].sudo().search(
                        [('id', 'in', category.brand_ids.ids)], order="brand_number")
                    for brand in brand_ids:
                        if customer.customer_type_id in brand.customer_type_ids or not brand.customer_type_ids:
                            data.append(self.brand_data(brand))
                    response = {"code": 200, "message": "All brands", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/all/brand', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_all_brand(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    # category = request.env['product.category'].sudo().search(
                    #     [('id', '=', int(kw.get('subcategory')))], order="sequence")
                    # base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    data = []
                    brand_ids = request.env['product.brand'].sudo().search(
                        [], order="brand_number")
                    for brand in brand_ids:
                        if customer.customer_type_id in brand.customer_type_ids or not brand.customer_type_ids:
                            data.append(self.brand_data(brand))
                    response = {"code": 200, "message": "All brands", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/brand/product', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_brand_product(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "brand":"brand.id"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    products = []
                    if bool(kw.get('brand', False)):
                        products = request.env['product.template'].sudo().search(
                            [('brand_id', '=', int(kw.get('brand')))],
                            order="sequence")
                    data = []
                    products = self.filter_product_qty_available(products, customer)
                    products = self.product_sort(products, customer)
                    for product in products:
                        if product.active and product.sale_ok:
                            if customer.customer_type_id in product.customer_type_ids or not product.customer_type_ids:
                                data.append(self.product_data(product, customer))
                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/category', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_category(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    root_categorys = request.env['product.category'].sudo().search([('parent_id', '=', False)],
                                                                                   order="sequence")
                    data = []
                    for root_category in root_categorys:
                        categorys = request.env['product.category'].sudo().search(
                            [('parent_id', '=', root_category.id)], order="sequence")
                        if categorys:
                            if customer.customer_type_id in root_category.customer_type_ids or not root_category.customer_type_ids:
                                data.append(self.category_data(root_category))
                    response = {"code": 200, "message": "All categorys", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/login/customer', type='json', methods=['POST'], auth='public', sitemap=False)
    def login_customer(self, **kw):
        """{
                    "params": {
                        "mobile": "0100",
                        "password": "123",
                        "fcm_token": "123",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "All required data are missing!"}
            return response
        else:
            if kw.get('mobile', False) and kw.get('password', False):
                customer = request.env['res.partner'].sudo().search(
                    [('password', '=', kw.get('password')), ('phone', '=', kw.get('mobile'))], limit=1)
                if customer.is_block:
                    response = {"code": 401, "message": "هذا العميل محظور"}
                    return response
                if customer:
                    if customer.area_id:
                        area_data = {'id': customer.area_id.id, 'name': customer.area_id.name}
                    customer.sudo().generate_token()
                    customer.fcm_token = kw.get('fcm_token', False)
                    valus = self.customer_data(customer)
                    response = {"code": 200, "message": "login", "data": valus}
                    return response
                else:
                    response = {"code": 401, "message": "العميل غير موجود"}
                    return response
            else:
                response = {"code": 401, "message": "mobile or password is missing!"}
                return response

    @http.route('/api/get/product', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_product(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "subcategory":"subcategory.id",
                        "brand":"brand.id"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    if bool(kw.get('brand', False)) != True or int(kw.get('brand', False)) == 0:
                        products = request.env['product.template'].sudo().search(
                            [('categ_id', '=', int(kw.get('subcategory')))], order="sequence")
                    else:
                        products = request.env['product.template'].sudo().search(
                            [('categ_id', '=', int(kw.get('subcategory'))), ('brand_id', '=', int(kw.get('brand')))],
                            order="sequence")
                    data = []
                    products = self.filter_product_qty_available(products, customer)
                    products = self.product_sort(products, customer)
                    for product in products:
                        if product.active and product.sale_ok:
                            if customer.customer_type_id in product.customer_type_ids or not product.customer_type_ids:
                                data.append(self.product_data(product, customer))
                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/home/data', type='json', methods=['POST'], auth='public', sitemap=False)
    def home_data(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    root_categorys = request.env['product.category'].sudo().search([('parent_id', '=', False)],
                                                                                   order="sequence")
                    data = []
                    for root_category in root_categorys:
                        categorys = request.env['product.category'].sudo().search(
                            [('parent_id', '=', root_category.id)], order="sequence")
                        if categorys:
                            data.append(self.category_data(root_category))
                    promotions = request.env['coupon.program'].sudo().search(
                        ['|', ('rule_date_to', '=', False), ('rule_date_to', '>=', datetime.now())], limit=10)
                    response = {"code": 200, "message": "Home Data",
                                "data": {'categorys': data, "best_seller": self.best_seller(customer),
                                         "products_offers": self.products_offers(customer),
                                         "promotions": [self.promotion_data(promotion) for promotion in promotions],
                                         "viitas": customer.viitas
                                         }}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/add/card', type='json', methods=['POST'], auth='public', sitemap=False)
    def add_card(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "products":[{
                        "id":"id",
                        "quantity":"quantity",
                        "units_of_measure":"uom.id"}]
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                for product in kw.get('products'):
                    if customer:
                        sale_order = request.env['sale.order'].sudo().search(
                            [('partner_id', '=', customer.id), ('state', 'in', ['draft', 'sent'])], limit=1)
                        product_variant_id = request.env['product.template'].sudo().search(
                            [('id', '=', int(product.get("id")))], limit=1, order="sequence").product_variant_id.id
                        product_variant = request.env['product.template'].sudo().search(
                            [('id', '=', int(product.get("id")))], limit=1, order="sequence").product_variant_id
                        qty_available_product = self.qty_available_product(product_variant_id, customer,
                                                                           int(product.get("units_of_measure")))
                        if sale_order:
                            sale_order_line = request.env['sale.order.line'].sudo().search(
                                [('order_id', '=', sale_order.id), ('product_id', '=', product_variant_id),
                                 ('product_uom', '=', int(product.get("units_of_measure")))],
                                limit=1)
                            if sale_order_line:
                                if int(product.get("quantity")) == 0:
                                    sale_order_line.sudo().unlink()
                                    sale_order.sudo().check_cancel()
                                else:

                                    new_qty = sale_order_line.product_uom_qty + int(product.get("quantity"))
                                    if new_qty > qty_available_product:
                                        mass = "اكبر كمية متاحه من %s هي %s" % (
                                            product_variant.name, qty_available_product)
                                        response = {"code": 401, "message": mass}
                                        return response

                                    sale_order_line.product_uom_qty = new_qty
                                    # sale_order_line.product_uom = int(product.get("units_of_measure"))

                            elif int(product.get("quantity")) != 0:
                                if float(product.get("quantity")) > qty_available_product:
                                    mass = "اكبر كمية متاحه من %s هي %s" % (
                                        product_variant.name, qty_available_product)
                                    response = {"code": 401, "message": mass}
                                    return response
                                sale_order.order_line = [(0, 0,
                                                          {
                                                              "product_id": product_variant_id,
                                                              "product_uom_qty": int(
                                                                  product.get("quantity")) or False,
                                                              "product_uom": int(
                                                                  product.get("units_of_measure")) or False,
                                                          })]
                        elif int(product.get("quantity")) != 0:
                            if float(product.get("quantity")) > qty_available_product:
                                mass = "اكبر كمية متاحه من %s هي %s" % (
                                    product_variant.name, qty_available_product)
                                response = {"code": 401, "message": mass}
                                return response
                            warehousess = request.env['stock.warehouse'].sudo().search(
                                [])
                            warehouses = False
                            for ware in warehousess:
                                if customer.area_id.id in ware.area_ids.ids:
                                    warehouses = ware
                            if not warehouses:
                                warehouses = warehousess[0]
                            sale_order = request.env['sale.order'].sudo().create({
                                "partner_id": customer.id,
                                "order_line": [(0, 0,
                                                {
                                                    "product_id": product_variant_id,
                                                    "product_uom_qty": int(product.get("quantity")) or False,
                                                    "product_uom": int(
                                                        product.get("units_of_measure")) or False,
                                                })]
                            })
                        # sale_order.sudo().price()
                        response = {"code": 200, "message": "Add Card",
                                    "data": {"sale_order": {'id': sale_order.id, "name": sale_order.name}}}
                    else:
                        response = {"code": 401, "message": "token is missing!"}
                        return response
                return response

    @http.route('/api/sale/order/details', type='json', methods=['POST'], auth='public', sitemap=False)
    def sale_order_details(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "sale_oedr_id":"sale_oedr.id"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "All data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    if kw.get('sale_oedr_id', False):
                        sale_order = request.env['sale.order'].sudo().search(
                            [('id', '=', int(kw.get('sale_oedr_id')))], limit=1)
                    else:
                        sale_order = request.env['sale.order'].sudo().search(
                            [('partner_id', '=', customer.id), ('state', 'in', ['draft', 'sent'])], limit=1)

                    data = {}
                    if sale_order:
                        sale_order.sudo().recompute_coupon_lines()
                        data = self.sale_order_data(sale_order, customer)
                    response = {"code": 200, "message": "sale order data", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/sale/order/edit', type='json', methods=['POST'], auth='public', sitemap=False)
    def sale_order_edit(self, **kw):
        """{
                    "params": {
                    "token":"token",
                    "payment_method_type":1 or 2 or 3 or 4,
                    "sales_rep":1,
                    "device_id":1,
                    "data":[{
                        "line_id":"line.id",
                        "quantity":"quantity",
                    },{
                        "line_id":"line.id",
                        "quantity":"quantity",
                    }]}
                }"""
        if not kw:
            response = {"code": 401, "message": "All data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    for line in kw.get('data', False):
                        line_id = request.env['sale.order.line'].sudo().search(
                            [('id', '=', int(line.get('line_id', False)))], limit=1)
                        if line.get('quantity', False):
                            line_id.product_uom_qty = line.get('quantity')
                        else:
                            line_id.sudo().unlink()
                    sale_order = request.env['sale.order'].sudo().search(
                        [('partner_id', '=', customer.id), ('state', 'in', ['draft', 'sent'])], limit=1)
                    data = {}
                    if sale_order:
                        data = self.sale_order_data(sale_order, customer)
                        if int(kw.get('payment_method_type', False)) == 2:
                            sale_order.payment_method_type = "بي"
                        elif int(kw.get('payment_method_type', False)) == 4:
                            sale_order.payment_method_type = "محفظه"
                        elif int(kw.get('payment_method_type', False)) == 3:
                            sale_order.payment_method_type = "فوري"

                    sale_order.sudo().recompute_coupon_lines()
                    response = {"code": 200, "message": "sale order data", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/sale/order/confirm', type='json', methods=['POST'], auth='public', sitemap=False)
    def sale_order_confirm(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "All data is missing!"}
            return response
        else:
            if kw.get('token', False):
                minimum = request.env['ir.config_parameter'].sudo().get_param('nat.minimum_order', )
                minimum_product = request.env['ir.config_parameter'].sudo().get_param('nat.minimum_product', )
                customer = self.get_customer(kw.get('token'))
                if customer:
                    if customer.is_block:
                        response = {"code": 401, "message": "هذا العميل محظور", "data": "block"}
                        return response
                    if not customer.is_verified:
                        response = {"code": 401, "message": "انت غير مفعل الان!"}
                        return response
                    sale_order = request.env['sale.order'].sudo().search(
                        [('partner_id', '=', customer.id), ('state', 'in', ['draft', 'sent'])], limit=1)
                    data = {}
                    if sale_order:

                        warehousess = request.env['stock.warehouse'].sudo().search(
                            [])
                        warehouses = False
                        for ware in warehousess:
                            if customer.area_id.id in ware.area_ids.ids:
                                warehouses = ware
                        if not warehouses:
                            warehouses = warehousess[0]
                        if warehouses:
                            if warehouses.sale_order_amount < sale_order.amount_total and warehouses.hab_id.id:
                                sale_order.warehouse_id = warehouses.hab_id.id
                            else:
                                sale_order.warehouse_id = warehouses.id
                        if float(minimum) > sale_order.amount_total:
                            response = {"code": 401, "message": "الحد الادني لطلب الشراء %s " % minimum}
                            return response
                        if float(minimum_product) > len(sale_order.order_line.ids):
                            response = {"code": 401, "message": "الحد الادني لعدد المنتجات هو %s " % minimum_product}
                            return response
                        if sale_order.payment_method_type == 'محفظه':
                            if customer.viitas_action != True or customer.viitas < sale_order.amount_total:
                                response = {"code": 401, "message": "المحفظه غير كافيه او غير مفعلة!"}
                                return response


                        # if sale_order.payment_method_type=='بي':
                        #     state_bee_code=sale_order.sudo().get_bee_code()
                        #     if sale_order.statu_code!="INITIATED":
                        #         response = {"code": 401, "message": "هناك مشكله ما في بي يرجي المحاوله في وقت أخر"}
                        #         return response
                        elif sale_order.payment_method_type == 'محفظه':
                            customer.viitas -= sale_order.amount_total
                        mass = ''
                        for line in sale_order.order_line:
                            qty_available_product = self.qty_available_product(line.product_id.id, customer,
                                                                               line.product_uom.id)
                            if line.product_uom_qty > qty_available_product and line.product_id.type == "product":
                                mass += "اكبر كمية متاحه من %s هي %s" % (line.product_id.name, qty_available_product)
                        if mass != '':
                            response = {"code": 401, "message": mass}
                            return response
                        employee_id = request.env['hr.employee'].sudo().search([('id', '=', kw.get('sales_rep'))],
                                                                               limit=1)
                        if employee_id:
                            sale_order.employee_id = employee_id.id

                        sale_order.lat = kw.get('lat', False)
                        sale_order.long = kw.get('long', False)

                        device_bolck = request.env['device.bolck'].sudo().search(
                            [('name', '=', kw.get('device_id', False))],
                            limit=1)
                        if device_bolck:
                            response = {"code": 401, "message": 'هذا الموبيل لا يمكنه تأكيد الطلب'}
                            return response
                        sale_order.device_id = kw.get('device_id', False)
                        sale_order.sudo().recompute_coupon_lines()
                        sale_order.sudo().action_confirm()
                        # sale_order.sudo().get_delivery_date()
                        for picking in sale_order.picking_ids:
                            if picking.state == "confirmed":
                                picking.sudo().action_assign()
                        data = self.sale_order_data(sale_order, customer)
                    response = {"code": 200, "message": "sale order data", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/sale/order/history', type='json', methods=['POST'], auth='public', sitemap=False)
    def order_history(self, **kw):
        """{"params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    sale_orders = request.env['sale.order'].sudo().search(
                        [('partner_id', '=', customer.id), ('state', 'in', ['sale'])])
                    data = []
                    for sale_order in sale_orders:
                        data.append(self.sale_order_data(sale_order, customer))
                    response = {"code": 200, "message": "order history", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/sale/order/reorder', type='json', methods=['POST'], auth='public', sitemap=False)
    def order_reorder(self, **kw):
        """{"params": {
                        "token":"token",
                        "sale_order":"sale_order_id",

                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    sale_order = request.env['sale.order'].sudo().search(
                        [('id', '=', int(kw.get('sale_order')))], limit=1)
                    data = {}
                    if sale_order:
                        order = sale_order.sudo().copy()
                        data = self.sale_order_data(order, customer)
                    response = {"code": 200, "message": "order data", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/customer/verified', type='json', methods=['POST'], auth='public', sitemap=False)
    def customer_verified(self, **kw):
        """{"params": {
                        "token":"token",
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                data = {"is_verified": customer.is_verified}
                if customer:
                    response = {"code": 200, "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/order/verified', type='json', methods=['POST'], auth='public', sitemap=False)
    def order_verified(self, **kw):
        """{"params": {
                        "token":"token",
                        "sale_order":"sale_order.id",
                        "code":"code"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    picking = request.env['stock.picking'].sudo().search(
                        [('code', '=', kw.get('code')), ('sale_id', '=', int(kw.get('sale_order'))),
                         ('state', 'not in', ['done', 'cancel'])], limit=1)
                    if picking:
                        picking.sudo().write({'is_verified': True})
                        picking.sale_id.is_verified = True
                        response = {"code": 200, "message": "order verified!", "data": True}
                        return response
                    else:
                        response = {"code": 400, "message": "لم يتم التحقق من كود الاستلام برجاء ادخال الكود الصحيح",
                                    "data": False}
                        return response

                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/promotion', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_promotion(self, **kw):
        """{"params": {
                        "token":"token"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    data = []
                    promotions = request.env['coupon.program'].sudo().search(
                        ['|', ('rule_date_to', '=', False), ('rule_date_to', '>=', datetime.now())])
                    if promotions:
                        data = [self.promotion_data(promotion) for promotion in promotions]
                    else:
                        date = False
                    return {"code": 200, "message": "promotions data", "data": data}
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/payment/paid', type='json', methods=['POST'], auth='public', sitemap=False)
    def payment_paid(self, **kw):
        """{"params": {
                        "UserName":"Bee",
                        "Password":"8mk25CGRwp",
                        "Code":"@A4bxjPAxm%fmEp5Gy*y",
                        "payment_code":"9585755750"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('payment_code', False) and kw.get('UserName', False) == 'Bee' and kw.get('Password',
                                                                                               False) == '8mk25CGRwp' and kw.get(
                'Code', False) == '@A4bxjPAxm%fmEp5Gy*y':
                sale_order = request.env['sale.order'].sudo().search(
                    [('bee_code', '=', str(kw.get('payment_code')))])
                if sale_order:
                    sale_order.is_paid = True
                    # payment = request.env['sale.confirm.payment'].sudo().create({
                    #     "acquirer_id": request.env['payment.acquirer'].sudo().search([('is_bee', '=', True)],
                    #                                                                  limit=1).id or False,
                    #     "amount": sale_order.amount_total,
                    #     "currency_id": sale_order.currency_id.id,
                    #     "payment_date": date.today(),
                    #     "order": sale_order.id,
                    # })
                    # payment.sudo().api_data(sale_order.id)
                    # response = {"code": 200, "message": "Done"}
                    response = {"status": True, "message": "done"}
                    return response
                else:
                    # response = {"code": 401, "message": "payment_code is missing!"}
                    response = {"status": False, "message": "payment_code is missing!"}
                    return response
            else:
                # response = {"code": 401, "message": "data is missing!"}
                response = {"status": False, "message": "data is missing!"}
                return response

    @http.route('/api/payment/paid/<int:payment_code>', type='json', methods=['GET'], auth='public', sitemap=False)
    def payment_paid12(self, payment_code):
        sale_order = request.env['sale.order'].sudo().search(
            [('bee_code', '=', payment_code)])
        if sale_order:
            sale_order.is_paid = True
            # payment = request.env['sale.confirm.payment'].sudo().create({
            #     "acquirer_id": request.env['payment.acquirer'].sudo().search([('is_bee', '=', True)],
            #                                                                  limit=1).id or False,
            #     "amount": sale_order.amount_total,
            #     "currency_id": sale_order.currency_id.id,
            #     "payment_date": date.today(),
            #     "order": sale_order.id,
            # })
            # payment.sudo().api_data(sale_order.id)
            response = {"code": 200, "message": "Done"}
            return response
        else:
            response = {"code": 401, "message": "payment_code is missing!"}
            return response

    @http.route('/api/search/name', type='json', methods=['POST'], auth='public', sitemap=False)
    def search_name(self, **kw):
        """{"params": {
                        "token":"token",
                        "product_name":"product_name"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    products = request.env['product.template'].sudo().search(
                        [('name', 'ilike', kw.get('product_name', False))], order="sequence")
                    data = []
                    products = self.product_sort(products, customer)
                    for product in products:
                        if product.active and product.sale_ok and product.brand_id:
                            data.append(self.product_data(product, customer))
                    if not data:
                        return {"code": 204, "message": "المنتج غير موجود", "data": data}
                    return {"code": 200, "message": "product data", "data": data}
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/search/code', type='json', methods=['POST'], auth='public', sitemap=False)
    def search_code(self, **kw):
        """{"params": {
                               "token":"token",
                               "barcode":"barcode"
                           }
                       }"""
        if not kw:
            response = {"code": 401, "message": "all data is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    product = request.env['product.template'].sudo().search(
                        [('barcode', '=', kw.get('barcode', False))], order="sequence")
                    if product.active and product.sale_ok:
                        return {"code": 200, "message": "product data", "data": self.product_data(product, customer)}
                    else:
                        return {"code": 204, "message": "المنتج غير موجود", "data": {}}
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/product/discount', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_product_discount(self, **kw):
        """{
                    "params": {
                        "token":"token"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    products = request.env['product.template'].sudo().search(
                        [('is_discount', '=', True)], order="sequence")
                    data = []
                    products = self.product_sort(products, customer)
                    for product in products:
                        if product.active and product.sale_ok:
                            if customer.customer_type_id in product.customer_type_ids or not product.customer_type_ids:
                                data.append(self.product_data(product, customer))
                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/version/details', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_version_details(self, **kw):

        data = {
            "version_number": request.env['ir.config_parameter'].sudo().get_param('nat.version_number'),
            "version_code": request.env['ir.config_parameter'].sudo().get_param('nat.version_code'),
            "force_update": request.env['ir.config_parameter'].sudo().get_param('nat.force_update'),
            "under_maintenance": request.env['ir.config_parameter'].sudo().get_param('nat.under_maintenance'),
            "advertiments": request.env['ir.config_parameter'].sudo().get_param('nat.advertiments', )
        }
        response = {"code": 200, "message": "All products", "data": data}
        return response

    @http.route('/api/custom/rate', type='json', methods=['POST'], auth='public', sitemap=False)
    def custom_rate(self, **kw):
        """{
                    "params": {
                        "token":"token"
                        "rate_state": "1" or "2" or "3",
                        "comment":"comment"
                        "order_id":"order_id"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    new_rate = request.env['rate.almuazae'].sudo().create({
                        "partner_id": customer.id,
                        "rate_state": kw.get('rate_state', False),
                        "commit": kw.get('comment', False),
                        "order": int(kw.get('order_id', False)),
                        "date": date.today(),
                    })
                    response = {"code": 200, "message": "All products", "data": True}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/fcm/token', type='json', methods=['POST'], auth='public', sitemap=False)
    def fcm_token(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "fcm_token": "fcm_token"
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    customer.fcm_token = kw.get('fcm_token', False)
                    response = {"code": 200, "message": "Done", "data": True}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/product/by/id', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_product_py_id(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "product_id":"product.id"

                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    product = request.env['product.template'].sudo().search(
                        [('id', '=', int(kw.get('product_id')))], )
                    related_product = [self.product_data(related, customer) for related in product.related_product]
                    product_data = self.product_data(product, customer)
                    product_data["related_product"] = related_product
                    data = [product_data]
                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/product/related', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_product_related(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "product_id":"product.id"

                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    product = request.env['product.template'].sudo().search(
                        [('id', '=', int(kw.get('product_id')))], )
                    related_product = [self.product_data(related, customer) for related in product.related_product]
                    data = {"related_product": related_product}

                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response

    @http.route('/api/get/warehouses/employees', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_warehouses_employees(self, **kw):
        """{
                    "params": {
                        "token":"token",
                    }
                }"""
        # if not kw:
        #     response = {"code": 401, "message": "token is missing!"}
        #     return response
        # else:cd
        if True:
            customer = self.get_customer(kw.get('token'))
            warehousess = request.env['stock.warehouse'].sudo().search(
                [('employee_ids', '!=', False)])
            if warehousess:
                warehouses = warehousess[0]
                for ware in warehousess:
                    if customer.area_id.id in ware.area_ids.ids:
                        warehouses = ware
                if not warehouses:
                    warehouses = warehousess[0]
                data = []
                for employee in warehouses.employee_ids:
                    data.append(self.employee_data(employee))
                response = {"code": 200, "message": "employees", "data": data}
                return response

        response = {"code": 401, "message": "token is missing!"}
        return response

    @http.route('/api/get/Promotion/product', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_Promotion_product(self, **kw):
        """{
                    "params": {
                        "token":"token",
                        "promotion":1,
                    }
                }"""
        if not kw:
            response = {"code": 401, "message": "token is missing!"}
            return response
        else:
            if kw.get('token', False):
                customer = self.get_customer(kw.get('token'))
                if customer:
                    promotion = request.env['coupon.program'].sudo().search([('id', '=', kw.get('promotion', False))])
                    products = request.env['product.product'].sudo().search(
                        ast.literal_eval(promotion.rule_products_domain))
                    products = self.product_sort(products, customer)
                    # products = self.filter_product_qty_available(products.mapped('product_tmpl_id'), customer)
                    products = products[0:10]
                    data = []
                    for product in products:
                        if product.brand_id:
                            data.append(self.product_data(product.product_tmpl_id, customer))
                    response = {"code": 200, "message": "All products", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response
            else:
                response = {"code": 401, "message": "token is missing!"}
                return response
