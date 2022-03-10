# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, fields, api


class coupon_program(models.Model):
    _inherit = 'coupon.program'

    maximum_purchase_of = fields.Float(string="Maximum Purchase Of", required=False, )
    rule_maximum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')], default="tax_excluded")
    product_ids = fields.Many2many(comodel_name="product.product", string="Exception Prouduct", )

    @api.model
    def _filter_on_mimimum_amount(self, order):
        res = super(coupon_program, self)._filter_on_mimimum_amount(order)
        program_ids = list()
        for program in res:
            no_effect_lines = order._get_no_effect_on_threshold_lines()
            order_lins = self.env['sale.order.line'].sudo().search(
                [('order_id', '=', order.id), ('product_id', 'in', program.product_ids.ids)])
            order.order_line_ids = False
            order.order_line_ids = order_lins.ids
            no_effect_lines |= order_lins
            order_amount = {
                'amount_untaxed': order.amount_untaxed - sum(line.price_subtotal for line in no_effect_lines),
                'amount_tax': order.amount_tax - sum(line.price_tax for line in no_effect_lines)
            }
            if program.reward_type != 'discount':
                # avoid the filtered
                lines = self.env['sale.order.line']
            else:
                lines = order.order_line.filtered(lambda line:
                                                  line.product_id == program.discount_line_product_id or
                                                  line.product_id == program.reward_id.discount_line_product_id or
                                                  (
                                                          program.program_type == 'promotion_program' and line.is_reward_line)
                                                  )
            untaxed_amount = order_amount['amount_untaxed'] - sum(line.price_subtotal for line in lines)
            tax_amount = order_amount['amount_tax'] - sum(line.price_tax for line in lines)
            maximum_purchase_of = program._compute_program_amount('maximum_purchase_of', order.currency_id)
            program_amount = program._compute_program_amount('rule_minimum_amount', order.currency_id)
            if program.rule_minimum_amount_tax_inclusion == 'tax_included' and program_amount <= (
                    untaxed_amount + tax_amount) or program.rule_minimum_amount_tax_inclusion != 'tax_included' \
                    and program_amount <= untaxed_amount:
                last_orders = self.env['sale.order'].search([('partner_id', '=', order.partner_id.id), (
                    'date_order', ">=", date.today() - timedelta(days=program.limit_promotion - 1))])
                last_orders_line = self.env['sale.order.line'].search(
                    [('order_id', 'in', last_orders.ids),
                     (
                     'product_id', "in", self.env['coupon.program'].search([]).mapped('discount_line_product_id').ids)])
                if not last_orders_line or not program.limit_promotion:
                    if maximum_purchase_of:
                        if program.rule_maximum_amount_tax_inclusion == 'tax_included' and maximum_purchase_of >= (
                                untaxed_amount + tax_amount) or program.rule_maximum_amount_tax_inclusion != 'tax_included' and maximum_purchase_of >= untaxed_amount:
                            program_ids.append(program.id)
                    else:
                        program_ids.append(program.id)

        return self.browse(program_ids)

class sale_order(models.Model):
    _inherit = 'sale.order'

    order_line_ids = fields.Many2many('sale.order.line',string='Order Lines',copy=False,readonly=True)


class SaleReport(models.Model):
    _inherit = "sale.report"

    area_id = fields.Many2one(comodel_name="area.area", string="Area", required=False, )

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['area_id'] = ", s.area_id as area_id"
        groupby += ', s.area_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
