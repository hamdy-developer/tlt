from odoo import models, fields, api, _

class stock_picking(models.Model):
    _inherit = "stock.picking"

    account_invoice_ids = fields.Many2many('account.move', string="Account Invoice", copy=False)
    
    def prepare_supplier_invoice_data(self):
        """
        Prepare Supplier Invoice Data
        :return:
        """
        self.ensure_one()
        return {
            'move_type': 'in_invoice',
            'ref': self.name,
            'partner_id': self.purchase_id.partner_id.id,
            'invoice_date': self.scheduled_date.date(),
            'invoice_origin': self.purchase_id.name,
            'currency_id': self.purchase_id.currency_id.id,
            'company_id': self.purchase_id.company_id.id
        }
    
    def prepare_invoice_line_data(self, line):
        """
        Prepare Invoice Line For Vendor Bill
        :param line:
        :return:
        """
        stock=self.env['stock.move'].sudo().search([('product_id','=',line.product_id.id),('picking_id','=',self.id)],limit=1)
        self.ensure_one()
        prod_accounts = line.product_id.product_tmpl_id._get_product_accounts()
        return {
            'display_type': line.display_type,
            'sequence': line.sequence,
            'name': line.name,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom.id,
            'quantity': stock.quantity_done,
            'price_unit': line.price_subtotal/line.product_qty,
            'tax_ids': [(6,0,line.taxes_id.ids)],
            'account_id':prod_accounts['stock_input'].id,
            'purchase_line_id':line.id
        }

    def generate_account_payment(self, invoice_obj):
        """
        Create Register Payment Wizard And Generate Payment For Bill and Invoice..Invoice mark as paid.
        :param invoice_obj:
        :return:
        """
        register_payment_obj = self.env['account.payment.register']
        payment_fields = ['payment_date', 'amount', 'communication', 'group_payment', 'currency_id', 'journal_id',
                          'partner_bank_id', 'company_currency_id', 'line_ids', 'payment_type', 'partner_type',
                          'source_amount', 'source_amount_currency', 'source_currency_id', 'can_edit_wizard',
                          'can_group_payments', 'company_id', 'partner_id', 'payment_method_id',
                          'available_payment_method_ids', 'hide_payment_method', 'payment_difference',
                          'payment_difference_handling', 'writeoff_account_id', 'writeoff_label',
                          'show_partner_bank_account', 'require_partner_bank_account', 'country_code']
        vals = register_payment_obj.with_context(
            {'active_model': 'account.move', 'active_ids': invoice_obj.ids}).default_get(payment_fields)
        register_payment_wizard = register_payment_obj.create(vals)
        register_payment_wizard.action_create_payments()

    def _action_done(self):
        """
        Generate Invoice/Vendor Bill While Validate Picking..Mark as Draft,open or paid based on configuration in company.
        :return:
        """
        result = super(stock_picking, self)._action_done()
        for picking in self:
            if picking and picking.sale_id:
                if picking.sale_id.company_id.auto_generate_invoice:
                    partner_location = self.env.ref('stock.stock_location_customers').id
                    if picking.location_dest_id.id == partner_location:
                        inv_id = picking.sale_id._create_invoices()
                        self.account_invoice_ids = [(4, inv_id.id)]
                        if picking.sale_id.company_id.invoice_generated_on in ['open','paid']:
                            inv_id.action_post()
                        if picking.sale_id.company_id.invoice_generated_on == 'paid':
                            self.generate_account_payment(inv_id)
            if picking and picking.purchase_id:
                bill_obj = self.env['account.move']
                if picking.purchase_id.company_id.auto_generate_bill:
                    vendor_location = self.env.ref('stock.stock_location_suppliers').id
                    if picking.location_id.id == vendor_location:
                        invoice_vals = picking.prepare_supplier_invoice_data()
                        invoice_vals['invoice_line_ids'] = []
                        for line in picking.purchase_id.order_line:
                            invoice_vals['invoice_line_ids'].append((0, 0, self.prepare_invoice_line_data(line)))
                        invoice_vals['invoice_payment_term_id'] = picking.purchase_id.payment_term_id.id
                        inv_id = bill_obj.create(invoice_vals)
                        self.account_invoice_ids = [(4, inv_id.id)]
                        picking.purchase_id.invoice_ids = [(6,0,inv_id.ids + (picking.purchase_id.invoice_ids.ids or []))]
                        if picking.purchase_id.company_id.bill_generated_on in ['open','paid']:
                            inv_id.action_post()
                        if picking.purchase_id.company_id.bill_generated_on == 'paid':
                            self.generate_account_payment(inv_id)
        return result

    def action_view_account_invoice(self):
        if self.sale_id:
            invoices = self.mapped('account_invoice_ids')
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
                action['res_id'] = invoices.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        elif self.purchase_id:
            action = self.env.ref('account.action_move_in_invoice_type')
            result = action.read()[0]
            if self.purchase_id:
                result['context'] = {'type': 'in_invoice', 'default_purchase_id': self.purchase_id.id}
            if self.sale_id:
                result['context'] = {'type': 'out_invoice', 'default_sale_id': self.sale_id.id}

            if not self.account_invoice_ids:
                journal_domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', self.company_id.id),
                    ('currency_id', '=', self.purchase_id.currency_id.id),
                ]
                default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                if default_journal_id:
                    result['context']['default_journal_id'] = default_journal_id.id
            else:
                # Use the same account journal than a previous invoice
                result['context']['default_journal_id'] = self.account_invoice_ids.journal_id.id

            if len(self.account_invoice_ids) != 1:
                result['domain'] = "[('id', 'in', " + str(self.account_invoice_ids) + ")]"
            elif len(self.account_invoice_ids) == 1:
                res = self.env.ref('account.view_move_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = self.account_invoice_ids.id
            return result
