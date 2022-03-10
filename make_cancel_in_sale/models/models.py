# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CancelReasonPopup(models.Model):
    _name = 'cancel.reason.popup'
    _description = 'New Description'

    cancel_reason_id = fields.Many2one(comodel_name="cancel.reason", string="Reason", required=False, )
    sale_id = fields.Many2one(comodel_name="sale.order", string="", required=False, )

    def make_cancel(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.cancel_reason_id = rec.cancel_reason_id.id
                rec.sale_id.action_cancel()



class CancelReason(models.Model):
    _name = 'cancel.reason'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Text("Reason", required=True)


class EditSaleOrder(models.Model):
    _inherit = 'sale.order'

    cancel_reason_id = fields.Many2one(comodel_name="cancel.reason", string="Reason Of Cancel", required=False, )

    def action_cancel_button(self):
        for stock in self.picking_ids:
            if stock.state !='cancel':
                stock.sh_cancel()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reason of Cancl',
            'res_model': 'cancel.reason.popup',
            'view_mode': 'form',
            'target': 'new',
            # 'res_id': self.id,
            'context': {'default_sale_id': self.id},
        }


class stock_move(models.Model):
    _inherit = 'stock.move'

    cancel_reason_id = fields.Many2one(comodel_name="cancel.reason", string="Return Reason", readonly=True, )


class stock_return_picking_line(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    cancel_reason_id = fields.Many2one(comodel_name="cancel.reason", string="Return Reason", readonly=False,
                                       required=True)


class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'cancel_reason_id': return_line.cancel_reason_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def create_returns(self):
        for rec in self:
            for line in rec.product_return_moves:
                if not line.cancel_reason_id:
                    raise UserError(_("You must choose a reason for the return"))
            res = super(stock_return_picking, self).create_returns()
            return res


class return_report(models.TransientModel):
    _name = 'return.report'
    _description = 'New Description'

    date_to = fields.Datetime(string="To", required=False, )
    date_from = fields.Datetime(string="From", required=False, )

    def export_product(self):
        return self.env.ref('make_cancel_in_sale.report_action_id_return_report_wizard').report_action(self)
