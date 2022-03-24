# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InhStockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    employee_ids = fields.Many2many(comodel_name="hr.employee", string="",domain=lambda self: [('department_id', '=', self.env.ref('add_field_shipp.id_creat_data_department').id)])






