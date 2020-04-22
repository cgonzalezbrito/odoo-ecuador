# -*- coding: utf-8 -*-
# © <2016> <Cristian Salamea>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from datetime import datetime, timedelta

import psycopg2

_logger = logging.getLogger(__name__)

class AccountBankStatementLine(models.Model):
    """docstring for Bankstatementepayment"""
    _inherit = 'account.bank.statement.line'

    epayment_pos = fields.Many2one('account.epayment', 'Forma de Pago')
