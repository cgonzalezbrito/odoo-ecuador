# -*- coding: utf-8 -*-
# © <2016> <Cristian Salamea>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from odoo import api, fields, models 
from odoo.exceptions import (
    Warning as UserError,
    ValidationError
)
from . import utils


class AccountWithdrawing(models.Model):
    """ Implementacion de documento de retencion """

    _name = 'account.retention'
    _description = 'Withdrawing Documents'
    _order = 'date DESC'
    _logger = logging.getLogger(_name)

    @api.multi
    @api.depends('tax_ids.amount')
    def _compute_total(self):
        """
        TODO
        """
        self.amount_total = sum(tax.amount for tax in self.tax_ids)

    @api.multi
    def _get_period(self):
        result = {}
        for obj in self:
            result[obj.id] = self.env['account.period'].find(obj.date)[0]
        return result

    @api.multi
    def _get_in_type(self):
        context = self._context
        return context.get('in_type', 'ret_out_invoice')

    @api.multi
    def _default_type(self):
        context = self._context
        return context.get('type', 'out_invoice')

    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get('account.invoice')  # noqa
        return company.currency_id

    @api.model
    def _default_authorisation(self):
        if self.env.context.get('in_type') == 'ret_in_invoice':
            company = self.env['res.company']._company_default_get('account.invoice')  # noqa
            auth_ret = company.partner_id.get_authorisation('ret_in_invoice')
            return auth_ret
    @api.one
    @api.depends('state','name')
    def _compute_withholidng_number(self):
        if self.name:
            self.withholding_number = '{0}{1}{2}'.format(
                self.auth_inv_id.serie_entidad,
                self.auth_inv_id.serie_emision,
                self.name
            )
        else:
            self.withholding_number = '*'
        self._logger.info(self.withholding_number)

    STATES_VALUE = {'draft': [('readonly', False)]}

    withholding_number = fields.Char(
        compute = '_compute_withholidng_number',
        string = 'Numero Documento',
        store = True,
        readonly = True,
        copy = False
        )
    name = fields.Char(
        'Número',
        size=64,
        readonly=True,
        states=STATES_VALUE,
        copy=False
        )
    internal_number = fields.Char(
        'Número Interno',
        size=64,
        readonly=True,
        copy=False
        )
    manual = fields.Boolean(
        'Numeración Manual',
        readonly=True,
        states=STATES_VALUE,
        default=True
        )
    auth_inv_id = fields.Many2one(
        'account.authorisation',
        'Autorizacion',
        readonly=True,
        states=STATES_VALUE,
        domain=[('in_type', '=', 'interno')],
        default=_default_authorisation
        )
    type = fields.Selection(
        related='invoice_id.type',
        string='Tipo Comprobante',
        readonly=True,
        store=True,
        default=_default_type
        )
    in_type = fields.Selection(
        [
            ('ret_in_invoice', u'Retención a Proveedor'),
            ('ret_out_invoice', u'Retención de Cliente')
        ],
        string='Tipo',
        readonly=True,
        default=_get_in_type
        )
    date = fields.Date(
        'Fecha Emision',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True
    )
    tax_ids = fields.One2many(
        'account.invoice.tax',
        'retention_id',
        'Detalle de Impuestos',
        readonly=True,
        states=STATES_VALUE,
        copy=False
        )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Documento',
        required=False,
        readonly=True,
        states=STATES_VALUE,
        domain=[('state', '=', 'open')],
        copy=False
        )
    partner_id = fields.Many2one(
        'res.partner',
        string='Empresa',
        required=True,
        readonly=True,
        states=STATES_VALUE
        )
    move_id = fields.Many2one(
        related='invoice_id.move_id',
        string='Asiento Contable',
        readonly=True,
        store=True,
        copy=False
        )
    move_ret_id = fields.Many2one(
        'account.move',
        string='Asiento Retención',
        readonly=True,
        copy=False
        )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('done', 'Validado'),
            ('cancel', 'Anulado')
        ],
        readonly=True,
        string='Estado',
        default='draft'
        )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_currency
    )
    amount_total = fields.Monetary(
        compute='_compute_total',
        string='Total',
        store=True,
        readonly=True
        )
    to_cancel = fields.Boolean(
        string='Para anulación',
        readonly=True,
        states=STATES_VALUE
        )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        change_default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.invoice')  # noqa
        )
    auth_number = fields.Char(
        'Autorización',
        readonly=True,
        states=STATES_VALUE,
        )

    _sql_constraints = [
        (
            'unique_number_type',
            'unique(withholding_number,type)',
            u'El número de retención es único.'
        )
    ]

    @api.onchange('tax_ids')
    def _onchange_taxids(self):
        for tax_id in self.tax_ids:
            if tax_id.name:
                tax_id.code = tax_id.name

    # @api.onchange('date')
    # @api.constrains('date')
    # def _check_date(self):
    #     if self.date and self.invoice_id:
    #         if self.fisical_document:
    #             return
    #         inv_date = datetime.strptime(self.invoice_id.date_invoice, '%Y-%m-%d')  # noqa            
    #         ret_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d') # noqa
    #         days = ret_date - inv_date
    #         if days.days not in list(range(0,6)):
    #             raise ValidationError(utils.CODE701)  # noqa

    @api.constrains('auth_number')
    def check_reference(self):
        """
        Metodo que verifica la longitud de la autorizacion
        10: documento fisico
        35: factura electronica modo online
        49: factura electronica modo offline
        """
        if self.type not in ['in_invoice', 'liq_purchase']:
            return
        if self.auth_number and len(self.auth_number) not in [10, 35, 37, 49]:
            raise UserError(
                u'Debe ingresar 10, 37 o 49 dígitos según el documento.'
            )
            
    @api.onchange('name')
    @api.constrains('name')
    def _onchange_name(self):
        length = {
            'in_invoice': 9,
            'liq_purchase': 9,
            'out_invoice': 15
        }
        if not self.name or not self.type:
            return
        if not len(self.name) == length[self.type] or not self.name.isdigit():
            raise UserError(u'Nro incorrecto. Debe ser de 15 dígitos.')
        if self.in_type == 'ret_in_invoice':
            if not self.auth_inv_id.is_valid_number(int(self.name)):
                raise UserError('Nro no pertenece a la secuencia.')

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state in ['done']:
                raise UserError('No se permite borrar retenciones validadas.')
        res = super(AccountWithdrawing, self).unlink()
        return res

    @api.onchange('to_cancel')
    def onchange_tocancel(self):
        if self.to_cancel:
            company = self.env['res.company']._company_default_get('account.invoice')  # noqa
            self.partner_id = company.partner_id.id

    @api.onchange('invoice_id')
    def onchange_invoice(self):
        if not self.invoice_id:
            return
        self.type = self.invoice_id.type

    @api.multi
    def action_number(self, number):
        for wd in self:
            if wd.to_cancel:
                raise UserError('El documento fue marcado para anular.')

            sequence = wd.auth_inv_id.sequence_id
            if self.type != 'out_invoice' and not number:
                number = sequence.next_by_id()
            wd.write({'name': number})
        return True

    @api.multi
    def action_validate(self, number=None):
        """
        @number: Número para usar en el documento
        """
        self.action_number(number)
        return self.write({'state': 'done'})

    @api.multi
    def button_validate(self):
        """
        Botón de validación de Retención que se usa cuando
        se creó una retención manual, esta se relacionará
        con la factura seleccionada.
        """
        for ret in self:
            if not ret.tax_ids:
                raise UserError('No ha aplicado impuestos.')
            self.action_validate(self.name)
            if ret.manual:
                ret.invoice_id.write({'retention_id': ret.id})
                self.create_move()
        return True

    @api.multi
    def create_move(self):
        """
        Generacion de asiento contable para aplicar como
        pago a factura relacionada
        """
        for ret in self:
            inv = ret.invoice_id
            move_data = {
                'journal_id': inv.journal_id.id,
                'ref': ret.name,
                'date': ret.date
            }
            total_counter = 0
            lines = []
            for line in ret.tax_ids:
                if not line.manual:
                    continue
                lines.append((0, 0, {
                    'partner_id': ret.partner_id.id,
                    'account_id': line.account_id.id,
                    'name': ret.name,
                    'debit': abs(line.amount),
                    'credit': 0.00
                }))

                total_counter += abs(line.amount)

            lines.append((0, 0, {
                'partner_id': ret.partner_id.id,
                'account_id': inv.account_id.id,
                'name': ret.name,
                'debit': 0.00,
                'credit': total_counter
            }))
            move_data.update({'line_ids': lines})
            move = self.env['account.move'].create(move_data)
            acctype = self.type == 'in_invoice' and 'payable' or 'receivable'
            inv_lines = inv.move_id.line_ids
            acc2rec = inv_lines.filtered(lambda l: l.account_id.internal_type == acctype)  # noqa
            acc2rec += move.line_ids.filtered(lambda l: l.account_id.internal_type == acctype)  # noqa
            acc2rec.auto_reconcile_lines()
            ret.write({'move_ret_id': move.id})
            move.post()
        return True

    @api.multi
    def action_cancel(self):
        """
        Método para cambiar de estado a cancelado el documento
        """
        for ret in self:
            if ret.move_ret_id:
                raise UserError(utils.CODE703)
            elif ret.auth_inv_id.is_electronic:
                raise UserError(u'No puede anular un documento electrónico.')
            data = {'state': 'cancel'}
            if ret.to_cancel:
                # FIXME
                if len(ret.name) == 9 and ret.auth_inv_id.is_valid_number(int(ret.name)):  # noqa
                    number = ret.auth_inv_id.serie_entidad + ret.auth_inv_id.serie_emision + ret.name  # noqa
                    data.update({'name': number})
                else:
                    raise UserError(utils.CODE702)
            self.tax_ids.write({'invoice_id': False})
            self.write({'state': 'cancel'})
        return True

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_print(self,data):
        # Método para imprimir comprobante contable
        return self.env.ref('l10n_ec_withholding.account_withholding').report_action(self, data=data)
