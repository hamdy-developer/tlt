from odoo import api, fields, models

class CarCArwModule(models.Model):
    _name = 'car.car'
    _rec_name = 'name'
    _description = 'car'

    name = fields.Char(string="Name", required=True, )


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    car_id = fields.Many2one(comodel_name="car.car", string="Car", required=False, )