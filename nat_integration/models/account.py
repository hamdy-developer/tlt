from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, )
