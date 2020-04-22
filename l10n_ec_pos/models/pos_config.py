# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one('res.partner', 'Default Partner', default=lambda self:self.env['res.partner'].search([('identifier','=','9999999999999'),('name','=','CONSUMIDOR FINAL'),]))
    sucursal = fields.Char(string="Dirección Sucursal")
    seq_access_key = fields.Many2one('ir.sequence', default=lambda self:self.env['ir.sequence'].search([('code','=','pos.edocuments.code')]))
    electronic_journal = fields.Boolean(string='Diario documentos electrónicos', default=lambda self:self.invoice_journal_id.auth_out_invoice_id.is_electronic)

    @api.onchange('invoice_journal_id')
    def _onchange_invoice_journal_id(self):
        self.electronic_journal = self.invoice_journal_id.auth_out_invoice_id.is_electronic