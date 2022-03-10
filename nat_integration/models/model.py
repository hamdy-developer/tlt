from odoo import api, fields, models, _
from odoo.modules.module import get_module_resource
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import time
import json
import requests
import string
import random
import re
import requests


class product_Unit_of_Measure(models.Model):
    _name = 'product.unit_of_measure'
    _rec_name = 'uom_id'
    _description = 'New Description'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=False)
    price = fields.Float(string="Price", required=False, )
    product_id = fields.Many2one(comodel_name="product.template", string="", required=False, )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False)
    price_discount = fields.Float(string="Price after discount", required=False)
    max_qty = fields.Integer(string="Max QTY", required=False, )


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, )
    area_ids = fields.Many2many(comodel_name="area.area", string="Area", required=False, )
    sale_order_amount = fields.Float(string="Sale order amount", required=False, )
    hab_id = fields.Many2one(comodel_name="stock.warehouse", string="Hab", required=False, )
    stock_id = fields.Many2one(comodel_name="stock.location", string="stock", required=True, )


class res_partner(models.Model):
    _inherit = 'res.partner'

    device_id = fields.Char(string="device_id", required=False, )
    token = fields.Char(string="Token", required=False, readonly=True)
    shop_name = fields.Char(string="Shop Name", required=False, readonly=False)
    password = fields.Char(string="Password", required=False, readonly=False)
    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, tracking=True)
    customer_type_id = fields.Many2one(comodel_name="customer.type", string="Customer Type", required=False, )
    governorate_id = fields.Many2one(comodel_name="governorate.governorate", string="محافظه", required=False, )
    is_verified = fields.Boolean(string="is_verified", tracking=True)
    verified_date = fields.Datetime(string="Verified Date", readonly=True)
    otp = fields.Char(string="OTP", required=False, )
    x = fields.Char(string="lat", required=False, )
    y = fields.Char(string="long", required=False, )
    viitas = fields.Float(string="", required=False, tracking=True)
    viitas_action = fields.Boolean(string="", tracking=True)
    is_block = fields.Boolean(string="Block", tracking=True)
    rate_ids = fields.One2many(comodel_name="rate.almuazae", inverse_name="partner_id", string="Rate", required=False, )
    sales_order_amount = fields.Integer(string="", required=False, compute="get_sales_order", store=True)
    avr_sales = fields.Float(string="Avr. Sales", required=False, readonly=True)
    fcm_token = fields.Char(string="", required=False, )
    sale_order_count = fields.Integer(compute='get_sales_order', string='Sale Order Count', store=True)
    employee_id = fields.Many2one('hr.employee', string='Sales Rep', readonly=False)
    custom_target = fields.Float(string="Custom target",  required=False, )
    customer_invoice = fields.Float(string="Customer invoice",  required=False, compute="get_total_invoice_customer")

    @api.depends('custom_target')
    def get_total_invoice_customer(self):
        for rec in self:
            rec.customer_invoice = sum(list(self.env['account.move'].sudo().search([('partner_id', '=', rec.id),
                                                                                    ('state', '=', 'posted'),
                                                                                    ('payment_state', '=', 'paid'),
                                                                                    ('move_type', '=',
                                                                                     'out_invoice'), ]).mapped(
                'amount_total')))
            if rec.custom_target:
                if rec.customer_invoice >= rec.custom_target:
                    rec.viitas_action = True
                else:
                    rec.viitas_action = False

    def test4(self):
        partners = self.search([])
        for x in partners:
            x.get_sales_order()

    @api.constrains('is_verified')
    def get_verified_date(self):
        for rec in self:
            if rec.is_verified:
                rec.verified_date = fields.Datetime.now()

    @api.depends('name')
    def get_sales_order(self):
        for rec in self:
            sales = self.env['sale.order'].search(
                [('partner_id', '=', rec.id), ('state', 'in', ['sale', 'done'])])
            rec.sale_order_count = len(sales)
            total = 0
            for sale in sales:
                total += sale.amount_total
            rec.sales_order_amount = total
            if rec.sale_order_count:
                rec.avr_sales = total / rec.sale_order_count

    def generate_token(self):
        for rec in self:
            rec.token = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase +
                                               string.digits, k=16))
        partner = self.env['res.partner'].sudo().search([('token', '=', rec.token), ('id', '!=', rec.id)])
        if partner:
            rec.generate_token()
        if not bool(re.search(r'\d', rec.token)):
            rec.generate_token()

    def generate_otp(self):
        for rec in self:
            rec.otp = ''.join(random.choices(string.digits, k=6))
        partner = self.env['res.partner'].sudo().search([('otp', '=', rec.otp), ('id', '!=', rec.id)])
        if partner or len(rec.otp) != 6:
            rec.generate_otp()
        rec.send_sms_otp()

    def send_sms_otp(self):
        URL = "https://smsmisr.com/api/webapi/?username=%s&password=%s&language=2&sender=ALMUAZAE&mobile=%s&message=%s&DelayUntil="
        user = 'klT6gU8X'
        password = 'OM5qP6NSdh'
        mobile = str(self.phone)
        message = "الرقم السرى للدخول الى الموزع هو %s." % self.otp
        response = requests.request("POST", URL % (user, password, mobile, message))

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         name=rec.name+str(rec.phone) or ""
    #         result.append((rec.id, name))
    #     return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(res_partner, self)._name_search(name, args, operator, limit, name_get_uid)
        if name:
            res += self.search([('phone', operator, name)]).ids

        return res


class area_area(models.Model):
    _name = 'area.area'
    _rec_name = 'name'
    _description = 'areas'

    name = fields.Char(required=True, string="name")
    governorate_id = fields.Many2one(comodel_name="governorate.governorate", string="محافظه", required=False, )

    @api.model
    def create(self, vals_list):
        res = super(area_area, self).create(vals_list)
        analytic_account = self.env['account.analytic.account'].create({
            'name': res.name,
            'area_id': res.id
        })
        return res


class res_users(models.Model):
    _inherit = 'res.users'

    area_ids = fields.Many2many(comodel_name="area.area", column1="area1", column2="area2", string="Areas", )
    areas_ids = fields.Char(string="", required=False, )


class governorate(models.Model):
    _name = 'governorate.governorate'
    _rec_name = 'name'
    _description = 'governorate'

    name = fields.Char(required=True)


class sale_order(models.Model):
    _inherit = 'sale.order'

    customer_pthone = fields.Char(string="", required=False, related="partner_id.phone")
    lat = fields.Char(string="lat", required=False, )
    long = fields.Char(string="long", required=False, )
    order_count = fields.Integer(string="Order Count", required=False, readonly=True)


    @api.onchange('partner_id')
    def get_order_count(self):
        for rec in self:
            order_count = self.search_count([('partner_id', '=', rec.partner_id.id),
                                             ('state', '=', 'sale'), ])
            rec.order_count = order_count

    @api.constrains('partner_id')
    def check_quotations_opened(self):
        for rec in self:
            check_quotations_opened = self.search([('partner_id', '=', rec.partner_id.id),
                                                   ('state', '=', 'draft'),('id','!=',rec.id) ], limit=1)
            if check_quotations_opened:
                raise UserError(
                    _("This customer has a quotation number %s, you must take action" % check_quotations_opened.name))

    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        self.partner_id.sudo().get_sales_order()
        return res

    @api.model
    def create(self, vals_list):
        res = super(sale_order, self).create(vals_list)
        res.analytic_account_id = self.env['account.analytic.account'].sudo().search([('area_id', '=', res.area_id.id)],
                                                                                     limit=1).id
        # res.sudo().recompute_coupon_lines()
        return res

    # def write(self, vals):
    #     # self.sudo().recompute_coupon_lines()
    #     return super(sale_order, self).write(vals)

    # @api.constrains('order_line')
    # def con_recompute_coupon_lines(self):
    #     print('con_recompute_coupon_lines')
    #     x=True
    #     for line in self.order_line:
    #         if line.price_subtotal<0:
    #             x=False
    #     print('xxxxxxxxxxxxxxx',x)
    #     if x:
    #         self.recompute_coupon_lines()

    def action_cancel_button(self):
        res = super(sale_order, self).action_cancel_button()
        for rec in self:
            rec.partner_id.sudo().get_sales_order()
        return res

    # def action_confirm(self):
    #     res = super(sale_order, self).action_confirm()
    #
    #     return res

    payment_method_type = fields.Selection(string="Payment Method Type",
                                           selection=[('كاش', 'Cash'), ('بي', 'Bee'), ('محفظه', 'viitas'),
                                                      ('فوري', 'فورى')],
                                           required=False, default='كاش')
    is_verified = fields.Boolean(string="", )
    is_allowed = fields.Boolean(string="", compute='get_is_allowed')
    bee_code = fields.Char(string="Bee Code", required=False, )
    delivery_date = fields.Date(string="Delivery Date", required=False, readonly=True, )
    test1 = fields.Char(string="", required=False, )
    test2 = fields.Char(string="", required=False, )
    statu_code = fields.Char(string="StatusCode", required=False, )
    is_paid = fields.Boolean(string="", )
    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, related="partner_id.area_id",
                              store=True)
    is_done = fields.Boolean(string="", compute="get_is_done")
    employee_id = fields.Many2one('hr.employee', string='Sales Rep', readonly=False)
    device_id = fields.Char(string="device_id", required=False, )

    @api.depends('name')
    def get_is_done(self):
        for rec in self:
            rec.is_done = True
            if not rec.picking_ids:
                rec.is_done = False
            for picking in rec.picking_ids:
                if picking.state != 'done':
                    rec.is_done = False
                    break

    def get_bee_code(self):
        date = "%s.%s.%s %s:%s:24" % (
            fields.Datetime.now().year, fields.Datetime.now().month, fields.Datetime.now().day,
            fields.Datetime.now().hour,
            fields.Datetime.now().minute)
        xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <Request action="1" version="1">
                    <Login>al.muazae</Login>
                    <Password>1a6d169328fe26fb89d2e3ca0bdd8d86f46fecf8</Password>
                    <Code>5405268465886036397013248724696085282132</Code>
                    <OrderId>%s</OrderId>
                    <OrderDate>%s</OrderDate>
                    <OrderAmount>%s</OrderAmount>
                    <OrderExpiryDate>2040.03.01 15:06:24</OrderExpiryDate>
                    <OrderDesc>%s</OrderDesc>
                    <ReservedParamIn1></ReservedParamIn1>
                    <ReservedParamIn2></ReservedParamIn2>
                    <ReservedParamIn3></ReservedParamIn3>
                    </Request>""" % (self.id, date, str(self.amount_total), self.name)
        # xml = """<?xml version="1.0" encoding="UTF-8"?>
        #                <Request action="1" version="1">
        #                <Login>al.muazae</Login>
        #                <Password>1a6d169328fe26fb89d2e3ca0bdd8d86f46fecf8</Password>
        #                <Code>5405268465886036397013248724696085282132</Code>
        #                <OrderId>456789123</OrderId>
        #                <OrderDate>2021.02.28 15:06:24</OrderDate>
        #                <OrderAmount>123.45</OrderAmount>
        #                <OrderExpiryDate>2022.03.01 15:06:24</OrderExpiryDate>
        #                <OrderDesc>SamSung Galaxy S5</OrderDesc>
        #                <ReservedParamIn1></ReservedParamIn1>
        #                <ReservedParamIn2></ReservedParamIn2>
        #                <ReservedParamIn3></ReservedParamIn3>
        #                </Request>"""
        headers = {'Content-Type': 'application/xml'}  # set what your server accepts
        request = requests.post('https://nx-staging.bee.com.eg:6443/xmlgw/merchant', data=xml, headers=headers)
        self.test1 = request_text = request.text
        self.test2 = date
        order_bee_id = request_text[request_text.find("<PGWOrderId>") + 12:request_text.find("</PGWOrderId>")]
        self.statu_code = request_text[request_text.find("<StatusCode>") + 12:request_text.find("</StatusCode>")]
        self.bee_code = order_bee_id

    def action_confirm(self):
        for rec in self:
            if self.env.user.id not in self.env.ref('base.group_system').users.ids:
                for line in rec.order_line:
                    if line.qty_available < line.product_uom_qty and line.price_unit>0:
                        mass="تاكد من وجود كمية متاحة  من %s" % line.product_id.name
                        raise UserError(_(mass))
                minimum = self.env['ir.config_parameter'].sudo().get_param('nat.minimum_order', )
                minimum_product = self.env['ir.config_parameter'].sudo().get_param('nat.minimum_product', )
                if float(minimum) > rec.amount_total:
                    mass = "الحد الادني لطلب الشراء %s " % minimum
                    raise UserError(_(mass))
                if float(minimum_product) > len(rec.order_line.ids):
                    mass = "الحد الادني لعدد المنتجات هو %s " % minimum_product
                    raise UserError(_(mass))
            rec.partner_id.sudo().get_sales_order()
        self.recompute_coupon_lines()
        res = super(sale_order, self).action_confirm()
        self.get_delivery_date()
        return res

    def get_delivery_date(self):
        for rec in self:
            today = fields.Date.today()
            last_delivery = self.env['ir.config_parameter'].sudo().get_param('nat.last_delivery')
            time = fields.Datetime.now().hour + (fields.Datetime.now().minute / 60)
            if float(time) <= float(last_delivery):
                rec.delivery_date = today
            else:
                rec.delivery_date = today + timedelta(days=1)

    @api.depends('name')
    def get_is_allowed(self):
        for rec in self:
            minimum = self.env['ir.config_parameter'].sudo().get_param('nat.minimum_order', )
            allowed = False
            if float(minimum) < rec.amount_total:
                allowed = True
            rec.is_allowed = allowed

    @api.constrains('order_line')
    def check_cancel(self):
        for rec in self:
            if len(rec.order_line.ids) == 0:
                rec.state = 'cancel'
    @api.onchange('order_line')
    def get_price_unit_liens(self):
        for rec in self:
            for line in rec.order_line:
                if line.price_unit > 0:
                    line.sudo().get_price_unit()

    def action_location(self):
        for rec in self:
            if rec.partner_id:
                url = "https://www.google.com/maps/?q=%s,%s" % (rec.partner_id.x, rec.partner_id.y)
                return {
                    'type': 'ir.actions.act_url',
                    'target': '_blank',
                    'url': url,
                }

    def action_draft(self):
        for line in self.order_line:
            line.get_product_domain()
        return super(sale_order, self).action_draft()


class product_template_inh(models.Model):
    _inherit = 'product.template'

    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, )
    uom_ids = fields.One2many(comodel_name="product.unit_of_measure", inverse_name="product_id", string="",
                              required=False, )
    is_discount = fields.Boolean(string="", )
    percentage = fields.Float(string="", required=False, )
    price_discount = fields.Float(string="Price after discount", required=False, compute="get_price_discount")
    date_start = fields.Date(string="Date start", required=False, )
    customer_type_ids = fields.Many2many(comodel_name="customer.type", string="Type", required=False, )
    sequence = fields.Integer(string="sequence", required=False, )
    free_qty = fields.Float(string="Free QTY", required=False, compute="get_free_qty")
    related_product = fields.Many2many(comodel_name="product.template", relation="relation", string="Product Related",
                                       column1="related_column1", column2="related_column2")
    default_code = fields.Char('Internal Reference', index=True, readonly=True)
    note = fields.Text(string="Note", required=False, )
    lst_price = fields.Float(
        'Public Price', compute='_compute_product_lst_price',
        digits='Product Price', inverse='_set_product_lst_price',
        help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.",
        tracking=True)
    max_qty = fields.Integer(string="Max QTY", required=False, )

    #
    # @api.returns('self', lambda value: value.id)
    # def copy(self, default=None):
    #     if default is None:
    #         default = {}
    #     if self.barcode:
    #         default.update({'barcode': _("%s" % self.barcode)})
    #     default.update({'uom_ids':[(0,0,{'price':self.list_price})]})
    #     self.barcode=False
    #     return super(product_template_inh, self).copy(default)

    @api.model
    def create(self, vals):
        amazon_import_export_seq = self.env['ir.sequence'].next_by_code('ref.product')
        vals.update({'default_code': amazon_import_export_seq})
        res = super(product_template_inh, self).create(vals)
        return res

    @api.depends('purchased_product_qty', 'virtual_available')
    def get_free_qty(self):
        for rec in self:
            rec.free_qty = rec.virtual_available - rec.purchased_product_qty

    @api.onchange('is_discount')
    def get_data(self):
        for rec in self:
            if rec.is_discount == False:
                rec.percentage = False
                rec.price_discount = False
                rec.date_start = False

    @api.depends('percentage', 'uom_ids', 'list_price')
    def get_price_discount(self):
        for rec in self:
            if rec.is_discount:
                rec.price_discount = rec.lst_price * (1 - (rec.percentage / 100))
                for line in rec.uom_ids:
                    line.price_discount = line.price * (1 - (rec.percentage / 100))
            else:
                rec.percentage = 0
                rec.price_discount = 0
                for line in rec.uom_ids:
                    line.price_discount = 0

    def testtest(self):
        products = (self.env['product.template']).sudo().search([('attachment_id', '=', False)])
        for product in products:
            product.attach_image_1920()

    @api.constrains("image_1920")
    def attach_image_1920(self):
        for rec in self:
            if not rec.attachment_id or rec.attachment_id.name != rec.name:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.name, "type": 'binary', 'datas': rec.image_1920, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.image_1920


class product_brand(models.Model):
    _inherit = 'product.brand'

    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, )
    customer_type_ids = fields.Many2many(comodel_name="customer.type", string="Type", required=False, )

    @api.constrains("brand_image")
    def attachbrand_image(self):
        for rec in self:
            if not rec.attachment_id:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.name, "type": 'binary', 'datas': rec.brand_image, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.brand_image


class product_template(models.Model):
    _inherit = 'product.category'

    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, )
    image_1920 = fields.Image("Image", compute="get_image", readonly=False)
    brand_ids = fields.Many2many(comodel_name="product.brand", string="Brands")
    is_soon = fields.Boolean(string="Soon", )
    customer_type_ids = fields.Many2many(comodel_name="customer.type", string="Type", required=False, )
    sequence = fields.Integer(string="sequence", required=False, )

    @api.constrains('is_soon')
    def if_is_soon(self):
        for rec in self:
            categorys = self.env['product.category'].search([('parent_id', '=', rec.id)])
            for category in categorys:
                category.is_soon = rec.is_soon

    @api.constrains('customer_type_ids')
    def get_customer_type_ids(self):
        for rec in self:
            categorys = self.env['product.category'].search([('parent_id', '=', rec.id)])
            for category in categorys:
                category.customer_type_ids = rec.customer_type_ids.ids
            products = self.env['product.template'].search([('categ_id', '=', rec.id)])
            for product in products:
                product.customer_type_ids = rec.customer_type_ids.ids

    @api.depends("attachment_id")
    def get_image(self):
        for rec in self:
            if rec.attachment_id:
                rec.image_1920 = rec.attachment_id.datas

    @api.onchange("image_1920")
    def attach_image_1920(self):
        for rec in self:
            if not rec.attachment_id and rec.name:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.name, "type": 'binary', 'datas': rec.image_1920, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.image_1920


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    sequence_sr = fields.Integer(string="SR", required=False, readonly=True)
    qty_available = fields.Float(string="", required=False, compute='qty_available_product', store=True)

    @api.depends('product_id', 'product_uom')
    def qty_available_product(self):
        for rec in self:
            warehousess = self.env['stock.warehouse'].sudo().search(
                [])
            warehouses = False
            for ware in warehousess:
                if rec.order_id.partner_id.area_id.id in ware.area_ids.ids:
                    warehouses = ware
            if not warehouses:
                warehouses = warehousess[0]

            stock_quant = self.env['stock.quant'].sudo().search(
                [('product_id', '=', rec.product_id.id), ('location_id', '=', warehouses.stock_id.id), ])
            qty_available = 0
            max_qty = 0
            for stock in stock_quant:
                qty_available += stock.available_quantity
            product_id = rec.product_id
            if product_id.type == "consu":
                qty_available = 1000
            if rec.product_uom:
                qty_available = round(qty_available * rec.product_uom.factor, 2)
            if product_id.uom_id.id == rec.product_uom.id:
                max_qty = product_id.max_qty
            else:
                max_qty = self.env['product.unit_of_measure'].sudo().search(
                    [('uom_id', '=', rec.product_uom.id), ('product_id', '=', product_id.product_tmpl_id.id)],
                    limit=1).max_qty
            if max_qty < qty_available and max_qty != 0 and max_qty:
                qty_available = max_qty
            rec.qty_available = qty_available

    @api.model
    def create(self, values):
        res = super(sale_order_line, self).create(values)
        for rec in res:
            rec.sequence_sr = self.search_count([('order_id', '=', rec.order_id.id)])
        return res

    @api.constrains('product_id', 'product_uom_qty', 'product_uom')
    def get_price_unit(self):
        for rec in self:
            if rec.product_id.price_discount:
                price_unit = self.env['product.unit_of_measure'].sudo().search(
                    [('product_id', '=', rec.product_template_id.id), ('uom_id', '=', rec.product_uom.id)],
                    limit=1).price_discount or rec.product_id.price_discount
            else:
                price_unit = self.env['product.unit_of_measure'].sudo().search(
                    [('product_id', '=', rec.product_template_id.id), ('uom_id', '=', rec.product_uom.id)],
                    limit=1).price or rec.product_id.lst_price
            rec.price_unit = price_unit

    test = fields.Boolean(string="", )

    @api.onchange('product_id')
    def get_product_domain(self):
        for rec in self:
            uom_list = [rec.product_id.uom_id.id]
            for uom in rec.product_id.uom_ids:
                uom_list.append(uom.uom_id.id)
            domain = {'domain': {'product_uom': [('id', 'in', uom_list)]}}
            return domain


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    code = fields.Char(string="Code", required=False, readonly=True, compute="generate_code", store=True, copy=False)
    is_verified = fields.Boolean(string="", copy=False)
    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, related="sale_id.area_id")
    state = fields.Selection(
        [
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('picked', 'picked'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")
    driver_id = fields.Many2one('hr.employee', string="Driver", tracking=True, help="Employee")

    def act_picked(self):
        for rec in self:
            rec.state = "picked"

    @api.depends("sale_id")
    def generate_code(self):
        for rec in self:
            if rec.sale_id and not rec.code:
                rec.code = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase +
                                                  string.digits, k=4))
                # stock = self.env['stock.picking'].sudo().search([('code', '=', rec.code), ('id', '!=', rec.id)])
                # if stock:
                #     rec.generate_code()
                if not bool(re.search(r'\d', rec.code)):
                    rec.generate_code()
            else:
                rec.code = rec.code


class coupon_program(models.Model):
    _inherit = 'coupon.program'

    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, )
    image_1920 = fields.Image("Image", compute="get_image", readonly=False)
    limit_promotion = fields.Integer(string="Limit Promotion", required=False, )

    @api.depends("attachment_id")
    def get_image(self):
        for rec in self:
            if rec.attachment_id:
                rec.image_1920 = rec.attachment_id.datas

    @api.onchange("image_1920")
    def attach_image_1920(self):
        for rec in self:
            if not rec.attachment_id and rec.name:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.name, "type": 'binary', 'datas': rec.image_1920, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.image_1920


class payment_acquirer(models.Model):
    _inherit = 'payment.acquirer'

    is_bee = fields.Boolean(string="Bee", )


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    last_delivery = fields.Float(string="Last time for delivery", required=False, )
    minimum_order = fields.Float(string="Minimum Order", required=False, )
    minimum_product = fields.Float(string="Minimum Prodect in order", required=False, )
    version_number = fields.Char(string="Version Number", required=False, )
    version_code = fields.Float(string="Version Code", required=False, )
    force_update = fields.Boolean(string="Force Update", required=False, )
    under_maintenance = fields.Boolean(string="Under Maintenance", required=False, )
    advertiments = fields.Boolean(string="Advertiments", required=False, )
    otp_default = fields.Char(string="otp default", required=False, )

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('nat.last_delivery',
                                                         self.last_delivery)
        self.env['ir.config_parameter'].sudo().set_param('nat.otp_default',
                                                         self.otp_default)
        self.env['ir.config_parameter'].sudo().set_param('nat.minimum_order',
                                                         self.minimum_order)
        self.env['ir.config_parameter'].sudo().set_param('nat.minimum_product',
                                                         self.minimum_product)
        self.env['ir.config_parameter'].sudo().set_param('nat.version_number',
                                                         self.version_number)
        self.env['ir.config_parameter'].sudo().set_param('nat.version_code',
                                                         str(self.version_code))
        self.env['ir.config_parameter'].sudo().set_param('nat.force_update',
                                                         self.force_update)
        self.env['ir.config_parameter'].sudo().set_param('nat.under_maintenance',
                                                         self.under_maintenance)
        self.env['ir.config_parameter'].sudo().set_param('nat.advertiments',
                                                         self.advertiments)
        res = super(res_config_settings, self).set_values()
        return res

    def get_values(self):
        res = super(res_config_settings, self).get_values()
        delivery = self.env['ir.config_parameter'].sudo().get_param(
            'nat.last_delivery',
            self.last_delivery)
        minimum = self.env['ir.config_parameter'].sudo().get_param(
            'nat.minimum_order',
            self.minimum_order)
        minimum_product = self.env['ir.config_parameter'].sudo().get_param(
            'nat.minimum_product',
            self.minimum_product)
        version_number = self.env['ir.config_parameter'].sudo().get_param(
            'nat.version_number',
            self.version_number)
        version_code = float(self.env['ir.config_parameter'].sudo().get_param(
            'nat.version_code',
            self.version_code))
        force_update = self.env['ir.config_parameter'].sudo().get_param(
            'nat.force_update',
            self.force_update)
        under_maintenance = self.env['ir.config_parameter'].sudo().get_param(
            'nat.under_maintenance',
            self.under_maintenance)
        advertiments = self.env['ir.config_parameter'].sudo().get_param(
            'nat.advertiments',
            self.advertiments)
        otp_default = self.env['ir.config_parameter'].sudo().get_param(
            'nat.otp_default',
            self.otp_default)
        res.update(
            minimum_product=minimum_product
        )
        res.update(
            otp_default=otp_default
        )
        res.update(
            last_delivery=delivery
        )
        res.update(
            minimum_order=minimum
        )
        res.update(
            version_number=version_number
        )
        res.update(
            version_code=version_code
        )
        res.update(
            force_update=force_update
        )
        res.update(
            under_maintenance=under_maintenance
        )
        res.update(
            advertiments=advertiments
        )
        return res


class customer_type(models.Model):
    _name = 'customer.type'
    _rec_name = 'name'
    _description = 'customer typy'

    name = fields.Char(string="", required=True, )


class promotion_frist(models.Model):
    _name = 'promotion.frist'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="", required=True, )
    attachment_id = fields.Many2one(comodel_name="ir.attachment", string="image", required=False, )
    image_1920 = fields.Image("Image", readonly=False, related="attachment_id.datas")
    active = fields.Boolean(string="active", default=True)

    @api.depends("attachment_id")
    def get_image(self):
        for rec in self:
            if rec.attachment_id:
                rec.image_1920 = rec.attachment_id.datas
            else:
                rec.image_1920 = rec.image_1920

    @api.onchange("name", "image_1920")
    def attach_image_1920(self):
        for rec in self:
            if not rec.attachment_id:
                attachment = self.env['ir.attachment'].sudo().create(
                    {"name": rec.id, "type": 'binary', 'datas': rec.image_1920, 'public': True})
                rec.attachment_id = attachment.id
            else:
                rec.attachment_id.datas = rec.image_1920


class otp_partner(models.Model):
    _name = 'otp.partner'
    _rec_name = 'name'

    name = fields.Char()
    otp = fields.Char(string="OTP", required=False, )

    def generate_otp(self):
        for rec in self:
            rec.otp = ''.join(random.choices(string.digits, k=6))
        partner = self.env['otp.partner'].sudo().search([('otp', '=', rec.otp), ('id', '!=', rec.id)])
        if partner or len(rec.otp) != 6:
            rec.generate_otp()
        rec.send_sms_otp()

    def send_sms_otp(self):
        URL = "https://smsmisr.com/api/webapi/?username=%s&password=%s&language=2&sender=ALMUAZAE&mobile=%s&message=%s&DelayUntil="
        user = 'klT6gU8X'
        password = 'OM5qP6NSdh'
        mobile = str(self.name)
        message = "الرقم السرى للدخول الى الموزع هو %s." % self.otp
        response = requests.request("POST", URL % (user, password, mobile, message))


class rate_rate(models.Model):
    _name = 'rate.almuazae'
    # _rec_name = 'name'
    _description = 'Rate Almuazae'
    _order = "date"

    partner_id = fields.Many2one('res.partner', string='Customer')
    order_id = fields.Many2one('sale.order', string='Order')
    rate_state = fields.Selection(string="", selection=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')],
                                  required=False, )
    commit = fields.Char(string="", required=False, )
    date = fields.Datetime(string="", required=False, default=fields.Datetime.now)


class uom_uom(models.Model):
    _inherit = 'uom.uom'

    the_number_of_pieces = fields.Integer(string="the number of pieces", required=True, )

    # def asdasd(self):
    #     cr = self._cr
    #     cr.execute(""" update uom_uom set  category_id = 1 where id= '113';""")


class stock_move(models.Model):
    _inherit = 'stock.move'

    all_name_uom = fields.Char(string="UOM Note", required=False, compute="get_new_field")

    @api.depends('name')
    def get_new_field(self):
        for rec in self:
            line = self.env['sale.order.line'].sudo().search(
                [('product_id', '=', rec.product_id.id), ('order_id', '=', rec.picking_id.sale_id.id)], limit=1)
            rec.all_name_uom = "%s (%s)" % (line.product_uom_qty, line.product_uom.name)


class device_bolck(models.Model):
    _name = 'device.bolck'
    _rec_name = 'name'
    _description = 'Device Bolck'

    name = fields.Char(string="device", required=True)
