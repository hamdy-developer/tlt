# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>)

from odoo import http
from odoo.http import request


class DownloadCSVController(http.Controller):

    @http.route('/image/bounce/csv/download/<int:bounce_msg_id>', auth='user')
    def bounce_csv_download(self, bounce_msg_id, **kw):
        out_msg_wizard = request.env['output.message'].browse(int(bounce_msg_id))
        csv = out_msg_wizard._csv_download()
        return request.make_response(csv, headers=[('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename=IMAGE_BOUNCE_FILE.csv')])
