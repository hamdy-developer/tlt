from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError,Warning,UserError
from dateutil.relativedelta import relativedelta

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    discount_all = fields.Float(string="Discount for all %", required=False, )
    message = fields.Char(string="Message", required=False, )
    apply_after = fields.Date(string="Apply After", required=False, )
    discount = fields.Float(string="Discount %", required=False, )
    tolerance = fields.Float(string="Tolerance %", required=False, )
    purchase_discount_id = fields.Many2one(comodel_name="purchase.order", string="", required=False, )
    is_discount_done = fields.Boolean(string="", )

    def button_cancel(self):
        res= super(purchase_order, self).button_cancel()
        for rec in self:
            for picking in rec.picking_ids:
                if picking.state=='done':
                    raise UserError("you cannot cancel")
        return res

    @api.onchange('partner_id')
    def get_discount(self):
        for rec in self:
            purchase = self.env['purchase.order'].search(
                [('partner_id', '=', rec.partner_id.id), ('is_discount_done', '=', False),
                 ('apply_after', '<=', fields.Date.today())])
            if purchase:
                rec.discount_all = purchase.discount
                rec.purchase_discount_id = purchase, id

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        self = self.with_company(self.company_id)
        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.with_company(self.company_id).get_fiscal_position(partner.id)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = fields.Datetime.now()

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            if line.product_qty >0:
                # Compute name
                product_lang = line.product_id.with_context(
                    lang=partner.lang,
                    partner_id=partner.id
                )
                name = product_lang.display_name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase

                # Compute taxes
                taxes_ids = fpos.map_tax(
                    line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids

                # Compute quantity and price_unit
                if line.product_uom_id != line.product_id.uom_po_id:
                    product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                    price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
                else:
                    product_qty = line.product_qty
                    price_unit = line.price_unit

                if requisition.type_id.quantity_copy != 'copy':
                    product_qty = 0

                # Create PO line
                order_line_values = line._prepare_purchase_order_line(
                    name=name, product_qty=product_qty, price_unit=price_unit,
                    taxes_ids=taxes_ids)
                order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

    @api.onchange('partner_id')
    def message_message(self):
        for rec in self:
            purchase = self.env['purchase.order'].search(
                [('partner_id', '=', rec.partner_id.id), ('is_discount_done', '=', False),
                 ('apply_after', '<=', fields.Date.today())])
            if purchase:
                warning_mess = {
                    'title': _('Message'),
                    'message': _('%s' % purchase.message),
                }
                return {'warning': warning_mess}


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    stock = fields.Float(string="Stock", required=False, related="product_id.qty_available")
    avr_sales = fields.Float(string="Avr. Sales", required=False, readonly=True)
    coverage = fields.Float(string="Coverage", required=False, )
    coverage_a_o = fields.Float(string="Coverage A/O", required=False, )

    @api.onchange("product_id", 'product_qty')
    def default_avr_Sales(self):
        for rec in self:
            if rec.order_id.discount_all:
                rec.discount = rec.order_id.discount_all
            avr_sales = 0
            # yaster = datetime.today() - relativedelta(days=1)
            pickings = self.env['stock.picking'].search([("state", '!=', 'cancel'),('picking_type_code', '=', 'outgoing')])
            for picking in pickings:
                lines = self.env['stock.move'].search(
                    [("picking_id", '=', picking.id), ('product_id', '=', rec.product_id.id)])

                for line in lines:
                    avr_sales += line.product_uom_qty
            rec.avr_sales = avr_sales
            if rec.avr_sales != 0:
                rec.coverage = rec.stock / rec.avr_sales
                rec.coverage_a_o = (rec.stock + rec.product_qty) / rec.avr_sales


class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'

    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse", required=False, )

    def action_in_progress(self):
        res=super(purchase_requisition, self).action_in_progress()
        if not self.vendor_id:
            raise UserError("يجب اختيار المورد")

        return res

class purchase_requisition_line(models.Model):
    _inherit = 'purchase.requisition.line'

    stock = fields.Float(string="Stock", required=False)
    avr_sales = fields.Float(string="Avr. Sales", required=False, readonly=True,compute="default_avr_Sales")
    coverage = fields.Float(string="Coverage", required=False, )
    coverage_a_o = fields.Float(string="Coverage A/O", required=False, )
    vendor_id = fields.Many2one('res.partner', string="Vendor",related='product_id.vendor_id')

    @api.model
    def create(self, vals_list):
        res= super(purchase_requisition_line, self).create(vals_list)
        res.default_avr_Sales()
        return res

    @api.depends("product_id", 'product_qty')
    def default_avr_Sales(self):
        for rec in self:
            avr_sales = 0
            yaster = datetime.today() - relativedelta(days=int( self.env['ir.config_parameter'].sudo().get_param('nat.avr_sales_day',)))
            sale_orders = self.env['sale.order'].search([("state", '=', 'sale'),("date_order", '>=', yaster)])
            for order in sale_orders:
                sale_order_line = self.env['sale.order.line'].search(
                    [("order_id", '=', order.id), ('product_id', '=', rec.product_id.id)])

                for line in sale_order_line:
                    avr_sales += line.product_uom_qty
            rec.avr_sales = avr_sales
            if rec.avr_sales != 0:
                rec.coverage = rec.stock / rec.avr_sales
                rec.coverage_a_o = (rec.stock + rec.product_qty) / rec.avr_sales


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.onchange('quantity_done')
    def error_tolerance(self):
        for rec in self:
            if (1 + rec.picking_id.purchase_id.tolerance / 100) * rec.product_uom_qty < rec.quantity_done:
                raise ValidationError(_('The quantity is greater than the allowed'))

class product_template(models.Model):
    _inherit = 'product.template'

    vendor_id = fields.Many2one('res.partner', string="Vendor",compute="get_vendor")

    @api.depends('seller_ids')
    def get_vendor(self):
        for rec in self:
            rec.vendor_id=False
            for line in rec.seller_ids:
                rec.vendor_id=line.name.id
                break


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    avr_sales_day = fields.Integer(string="Avr. Sales Days", required=False, readonly=False)

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('nat.avr_sales_day',
                                                         self.avr_sales_day)
        res = super(res_config_settings, self).set_values()
        return res

    def get_values(self):
        res = super(res_config_settings, self).get_values()
        avr_sales_day = self.env['ir.config_parameter'].sudo().get_param(
            'nat.avr_sales_day',
            self.avr_sales_day)
        res.update(
            avr_sales_day=avr_sales_day)

        return res