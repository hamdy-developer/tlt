# -*- coding: utf-8 -*-
import base64
import json
import logging
import requests
from datetime import datetime, date

from odoo import http
from odoo.http import request, Response
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

HEADERS = {'Content-Type': 'application/json'}


class mobil_notification_api(http.Controller):

    def get_customer(self, token):
        customer = request.env['res.partner'].sudo().search([('token', '=', token)], limit=1)
        return customer

    def pop_up_data(self, pop_up):
        title=""
        notification=""
        base_path = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = "Null"
        if pop_up.attachment_id.local_url:
            image_url = base_path + pop_up.attachment_id.local_url
        if pop_up.title:
            title=pop_up.title
        if pop_up.notification:
            notification=pop_up.notification
        date = {
            "title": title,
            "notification": notification,
            "image": image_url,
        }
        return date

    @http.route('/api/get/pop_up', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_pop_up(self, **kw):
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
                    pop_up = request.env['mobil_notification.mobil_notification'].sudo().search([ ('pop_up', '=', True)], limit=1)
                    if pop_up:
                        data = self.pop_up_data(pop_up)
                    else:
                        data=None
                    response = {"code": 200, "message": "pop_up", "data": data}
                    return response
                else:
                    response = {"code": 401, "message": "token is missing!"}
                    return response
