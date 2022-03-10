from odoo import models, fields, api, _
from datetime import datetime

class SaleOrder(models.Model):    
    _inherit="sale.order"
    
    purchase_order_ids = fields.Many2many('purchase.order',string='Purchase Order')
    
    def action_view_purchase_order(self):
        po = self.mapped('purchase_order_ids')
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if len(po) > 1:
            action['domain'] = [('id', 'in', po.ids)]
        elif len(po) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = po.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for po in self.purchase_order_ids:
            po.button_confirm()
        return res