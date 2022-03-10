# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class data_mop10(models.Model):
#     _name = 'data_mop10.data_mop10'
#     _description = 'data_mop10.data_mop10'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
