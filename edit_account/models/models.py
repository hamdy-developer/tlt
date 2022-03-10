# -*- coding: utf-8 -*-

from odoo import models, fields, api


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    acoucnt_code = fields.Char(string="", required=False,comute="get_account_data" )
    acoucnt_name = fields.Char(string="", required=False,comute="get_account_data" )

    @api.depends('account_id')
    def get_account_data(self):
        for rec in self:
            if rec.account_id:
                rec.acoucnt_code=rec.account_id.code
                rec.acoucnt_name=rec.account_id.name
            else:
                rec.acoucnt_code = rec.acoucnt_code
                rec.acoucnt_name = rec.acoucnt_name


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _get_default_journal(self):
        ''' Get the default journal.
        It could either be passed through the context using the 'default_journal_id' key containing its id,
        either be determined by the default type.
        '''
        move_type = self._context.get('default_move_type', 'entry')
        if move_type in self.get_sale_types(include_receipts=True):
            journal_types = ['sale']
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_types = ['purchase']
        else:
            journal_types = self._context.get('default_move_journal_types', ['general'])

        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self._context['default_journal_id'])

            if move_type != 'entry' and journal.type not in journal_types:
                raise UserError(_(
                    "Cannot create an invoice of type %(move_type)s with a journal having %(journal_type)s as type.",
                    move_type=move_type,
                    journal_type=journal.type,
                ))
        else:
            journal = self._search_default_journal(journal_types)

        return journal

    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 check_company=True, domain="[]",
                                 default=_get_default_journal)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals_list):
        res =super(AccountMove, self).create(vals_list)
        res._set_next_sequence()
        return res