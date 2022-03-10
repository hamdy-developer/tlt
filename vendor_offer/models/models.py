# -*- coding: utf-8 -*-

from odoo import models, fields, api


class vendor_offer(models.Model):
    _name = 'vendor_offer.vendor_offer'
    _rec_name = "partner_id"
    _description = 'vendor_offer.vendor_offer'

    partner_id = fields.Many2one('res.partner', string="Vendor", domain="[('company_id', '=', False)]")
    date = fields.Date(string="Date", required=False,default=fields.Date.today )
    offer_valid_from = fields.Date(string="Offer Valid From", required=False)
    offer_valid_to = fields.Date(string="Offer Valid To", required=False )
    line_ids = fields.One2many(comodel_name="vendor_offer.line", inverse_name="vendor_offer_id", string="", required=False, )

    @api.constrains('partner_id','line_ids')
    def create_Vendor_list(self):
        for rec in self:
            for line in rec.line_ids:
                vendor_list=self.env['product.supplierinfo'].sudo().search([('name','=',rec.partner_id.id),('product_tmpl_id','=',line.product_id.id)],limit=1)
                if vendor_list:
                    vendor_list.discount_dealy=line.discount
                    vendor_list.min_qty=line.qty
                else:
                    vendor_list = self.env['product.supplierinfo'].sudo().create({
                        'name':rec.partner_id.id,
                        'product_tmpl_id':line.product_id.id,
                        'discount_dealy':line.discount,
                        'min_qty':line.qty,
                    })



class vendor_offer(models.Model):
    _name = 'vendor_offer.line'
    _description = 'vendor_offer.vendor_offer'

    vendor_offer_id = fields.Many2one(comodel_name="vendor_offer.vendor_offer", string="", required=False, )

    categ_id = fields.Many2one('product.category', 'Product Category')
    product_id = fields.Many2one(comodel_name="product.template", string="Product", required=False, )
    qty = fields.Float('Quantity', default=1)
    price_unit = fields.Float(string='Unit Price',)
    total_amount = fields.Float(string='Total Amount',)
    target_details = fields.Char(string="Target Details", required=False, )
    offer_details = fields.Char(string="Offer Details", required=False, )
    discount = fields.Float(string='Discount (%)', default=0.0)

class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'





    direct_discount = fields.Float(string="direct Discount %",  required=False,  )
    cost_unite = fields.Float(string=" Unit cost",  required=False,  compute="get_cost")

    indirect_monthly = fields.Float(string="Indirect Monthly %",  required=False,  )
    cost_indirect_monthly = fields.Float(string=" cost afterIndirect Monthly",  required=False,  compute="get_cost")
    indirect_quarter = fields.Float(string="Indirect Quarter %",  required=False,  )
    cost_indirect_quarter = fields.Float(string="Cost Indirect Quarter",  required=False,  compute="get_cost")
    indirect_semi_annual = fields.Float(string="Indirect Semi annual %",  required=False,  )
    cost_indirect_semi_annual = fields.Float(string="Cost Indirect Semi annual",  required=False,  compute="get_cost")
    indirect_annual = fields.Float(string="Indirect annual %",  required=False,  )
    net_cost = fields.Float(string="Net Cost",  required=False,  compute="get_cost")


    # cost = fields.Float(string="Cost",  required=False, compute="get_cost")
    # discount_dealy = fields.Float(string="Discount Dealy%",  required=False, )
    # net_cost = fields.Float(string="Net Cost",  required=False, compute="get_net_cost")
    #
    @api.depends('price','indirect_monthly','indirect_quarter','indirect_semi_annual','indirect_annual','direct_discount')
    def get_cost(self):
        for rec in self:
            rec.cost_unite=rec.price-rec.price*(rec.direct_discount/100)
            rec.cost_indirect_monthly=rec.cost_unite-rec.cost_unite*(rec.indirect_monthly/100)
            rec.cost_indirect_quarter=rec.cost_indirect_monthly-rec.cost_indirect_monthly*(rec.indirect_quarter/100)
            rec.cost_indirect_semi_annual=rec.cost_indirect_quarter-rec.cost_indirect_quarter*(rec.indirect_semi_annual/100)
            rec.net_cost=rec.cost_indirect_semi_annual-rec.cost_indirect_semi_annual*(rec.indirect_annual/100)

    # @api.depends('discount_dealy','cost','price')
    # def get_net_cost(self):
    #     for rec in self:
    #         rec.net_cost=rec.cost-rec.price*(rec.discount_dealy/100)


class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'

    def qty_available_product(self,product):
        stock_quant = self.env['stock.quant'].sudo().search(
            [('product_id', '=', product), ('location_id.usage', '=', 'internal'), ])
        qty_available = 0
        for stock in stock_quant:
            qty_available += stock.available_quantity
        return qty_available

    @api.onchange('vendor_id','warehouse_id')
    def get_lines(self):
        for rec in self:
            rec.line_ids=False
            location=rec.warehouse_id.lot_stock_id
            products=self.env['product.product'].sudo().search([],order='vendor_id')
            line_ids=[]
            for product in products:
                line_ids.append((0,0,{
                    'product_id':product.id,
                    'stock':self.qty_available_product(product.id),
                    'product_uom_id':product.uom_id.id,
                }))
            rec.line_ids=line_ids
            if rec.vendor_id:
                vendor_lists=self.env['product.supplierinfo'].sudo().search([('name','=',rec.vendor_id.id)])
                line_ids = []
                rec.line_ids=False
                for vendor_list in vendor_lists:
                    product_id=False
                    if vendor_list.product_tmpl_id.product_variant_ids:
                        for product in vendor_list.product_tmpl_id.product_variant_ids:
                            product_id=product
                    if product_id:
                        line_ids.append((0, 0, {
                            'product_id': product_id.id,
                            'stock': self.qty_available_product(product_id.id),
                            'product_uom_id': vendor_list.product_uom.id,
                        }))


                rec.line_ids = line_ids

class purchase_requisition_line(models.Model):
    _inherit = 'purchase.requisition.line'

    price_unit = fields.Float(string="Unit Price",  compute="get_price_unit" )

    @api.depends('product_id')
    def get_price_unit(self):
        for rec in self:
            rec.price_unit=rec.price_unit
            if not rec.price_unit and rec.requisition_id.vendor_id:
                vendor_lists = self.env['product.supplierinfo'].sudo().search([('name', '=', rec.vendor_id.id),('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)],limit=1)
                rec.price_unit=vendor_lists.price


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def get_discount(self):
        for rec in self:
            list= self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),],limit=1)
            rec.price_unit= list.cost_unite

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res=super(purchase_order_line, self)._onchange_quantity()
        self.get_discount()
        return res


class CouponProgram(models.Model):
    _inherit = 'coupon.program'


    def _compute_order_count(self):
        for program in self:
            program.order_count = self.env['sale.order.line'].search_count([('order_id.state','=','sale'),('product_id','=',program.discount_line_product_id.id)])
            # program.order_count = mapped_data.get(program.discount_line_product_id.id, 0)