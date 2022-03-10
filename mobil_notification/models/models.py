# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import json


class mobil_notification(models.Model):
    _name = 'mobil_notification.mobil_notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'mobil_notification.mobil_notification'
    title = fields.Char(string="Title", required=False, tracking=True)
    notification = fields.Text(string="Notification", required=False, tracking=True)
    product_id = fields.Many2one(comodel_name="product.template", string="Product", required=False, tracking=True)
    brand_id = fields.Many2one(comodel_name="product.brand", string="Brand", required=False, tracking=True)
    category_id = fields.Many2one(comodel_name="product.category", string="Category", required=False,
                                  domain="[('brand_ids', 'in', [brand_id])]", tracking=True)
    customer_ids = fields.Many2many(comodel_name="res.partner", column1="customer1", column2="customer2", tracking=True
                                    , string="Customers")
    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, tracking=True)
    image_1920 = fields.Image("Image", compute="get_image", readonly=False, tracking=True)
    pop_up = fields.Boolean(string="Pop-up", tracking=True)
    send = fields.Char(string="Send", required=False, tracking=True)

    @api.depends("attachment_id")
    def get_image(self):
        for rec in self:
            if rec.attachment_id:
                rec.image_1920 = rec.attachment_id.datas

    @api.onchange("image_1920")
    def attach_image_1920(self):
        for rec in self:
            if not rec.attachment_id and rec.title:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.title, "type": 'binary', 'datas': rec.image_1920, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.image_1920

    def product_data(self, product):
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        bundle = []
        if product.attachment_id.local_url:
            image_url = base_path + product.attachment_id.local_url
        brand = "Null"
        if product.brand_id:
            brand = {'id': product.brand_id.id, 'name': product.brand_id.name, }
        units_of_measure = []
        if product.uom_ids:
            for uom in product.uom_ids:
                units_of_measure.append(
                    {'id': uom.uom_id.id, 'name': uom.uom_id.name, 'price': round(uom.price, 2),
                     "price after discount": round(uom.price_discount, 2), })
        units_of_measure.append(
            {'id': product.uom_id.id, 'name': product.uom_id.name, 'price': round(product.list_price, 2),
             "price after discount": round(product.price_discount, 2), })
        if product.bom_ids:
            product_bom = self.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', product.id)], limit=1)
            for line_bom in product_bom.bom_line_ids:
                bundle.append({
                    'product_data': self.product_data(line_bom.product_tmpl_id),
                    'qty': line_bom.product_qty,
                    'units_of_measure': self.units_of_measure_data(line_bom.product_uom_id),
                }
                )
        return {'id': product.id, 'name': product.name, 'image': image_url, 'discount': product.is_discount,
                'discount_percentage': product.percentage,
                'Barcode': product.barcode, 'brand': brand, 'units_of_measure': units_of_measure,
                "description": product.description_sale or "", "note": product.note, 'bundle': bundle}

    def brand_data(self, brand):
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        if brand.attachment_id.local_url:
            image_url = base_path + brand.attachment_id.local_url
        return {'id': brand.id, 'name': brand.name, 'image': image_url, }

    def act_send(self):
        for rec in self:
            rec.send = "False"
            to = "/topics/general"
            to_key = "to"
            product_data = {}
            brand_data = {}
            if rec.brand_id:
                brand_data = self.brand_data(rec.brand_id)
            category_id = rec.category_id.id or 0
            if rec.product_id:
                product_data = self.product_data(rec.product_id)
            if rec.customer_ids:
                to = []
                to_key = "registration_ids"
                for customer in rec.customer_ids:
                    if customer.fcm_token:
                        to.append(customer.fcm_token)
            base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            body = ''
            title = ''
            if rec.notification:
                body = rec.notification
            if rec.title:
                title = rec.title
            if self.attachment_id.local_url:
                image_url = base_path + self.attachment_id.local_url
                data = {to_key: to,
                        "data": {
                            "body": body,
                            "title": title,
                            "image_url": image_url,
                            "product_data": product_data,
                            "category_id": category_id,
                            "brand_data": brand_data,
                            "sound": "Enabled"
                        }
                        }
            else:
                data = {to_key: to,
                        "data": {
                            "body": body,
                            "title": title,
                            "image_url": "",
                            "product_data": product_data,
                            "category_id": category_id,
                            "brand_data": brand_data,
                            "sound": "Enabled"
                        }
                        }

            headers = {
                "Authorization": "key=AAAAf2BjSwE:APA91bEu6odO-ngCd5DavtSI3iQ89ZT0SJzv11yBUp3_zwK53OZnlDvo87vDl9YCHZUOa6jKIRHXxhHSU53dRcXG2j0XlLT6rsQz6wj50180B0RdCVB2x3CGVqsuXmB-Orzx3jo4vNsZ",
                "Sender": "id=547077966593", "Content-Type": "application/json"
            }
            url = "https://fcm.googleapis.com/fcm/send"
            result_dict = requests.post(url=url, data=json.dumps(data), headers=headers)
            rec.send = False
            rec.send = "Done"

