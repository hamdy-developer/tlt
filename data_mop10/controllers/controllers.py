from odoo import http
from odoo.http import request


HEADERS = {'Content-Type': 'application/json'}
class NatApi(http.Controller):

    @http.route('/api/get/data/mop10', type='json', methods=['POST'], auth='public', sitemap=False)
    def get_customer_type(self, **kw):
        request.env['ir.config_parameter'].sudo().set_param('kw.kw', kw)
