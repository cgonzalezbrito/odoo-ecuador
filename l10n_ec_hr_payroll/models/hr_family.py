#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date, datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from stdnum.ec import vat


class HrFamily(models.Model):
    """
    Management of employees' family responsibilities
    """
    _name = 'hr.family'

    @api.multi
    @api.depends('birthday', 'date_marriage')
    def _compute_age(self):
        for row in self:
            if row.birthday:
                date_birthday = datetime.strptime(row.birthday, "%Y-%m-%d")
                if date_birthday <= datetime.today():
                    today = datetime.today().strftime("%Y-%m-%d")
                    now = today.split('-')
                    birth = row.birthday.split('-')
                    date_now = date(int(now[0]), int(now[1]), int(now[2]))
                    date_birth = date(int(birth[0]), int(birth[1]), int(birth[2]))
                    delta = date_now - date_birth
                    age = delta.days / 365
                    row.age = age
            if row.date_marriage:
                date_marriage = datetime.strptime(row.date_marriage, "%Y-%m-%d")
                if date_marriage <= datetime.today():
                    today = datetime.today().strftime("%Y-%m-%d")
                    now = today.split('-')
                    marriage = row.date_marriage.split('-')
                    date_now = date(int(now[0]), int(now[1]), int(now[2]))
                    date_marriage = date(int(marriage[0]), int(marriage[1]), int(marriage[2]))
                    delta = date_now - date_marriage
                    age = delta.days / 365
                    row.years_marriage = age

    employee_id = fields.Many2one('hr.employee', string=_('Employee'))
    name = fields.Char(_('Name'), required=True)
    birthday = fields.Date(_('Fecha de Nacimiento'), required=True)
    age = fields.Integer(compute=_compute_age, string=_('Edad'), store=True)
    relation = fields.Selection([('spouse', _('Conyugue')),
                                 ('child', _('Hijo/a')),
                                 ('father', _('Padre')),
                                 ('mother', _('Madre')),
                                 ('uncle', _('Tío/a')),
                                 ('brother', _('Hermano/a')),
                                 ('nephew', _('Sobrino/a')),
                                 ('other', 'Otro')], string=_('Relación'), required=True)
    other = fields.Char(_('Otro'))
    date_marriage = fields.Date(_('Fecha de Matrimonio'))
    years_marriage = fields.Integer(compute=_compute_age, string=_('Años de casdo'), store=True)
    gender = fields.Selection([('male', _('Masculino')),
                               ('female', _('Femenino')),
                               ('other', _('Otro'))], string=_('Género'))
    identification_id = fields.Char(_('Identificación No'))
    passport_id = fields.Char(_('Pasaporte No'))
    disability = fields.Boolean(_('Discapacidad'))
    conadis_id = fields.Char(_('CONADIS No'))
    disability_type = fields.Char(_('Tipo de Discapacidad'))
    disability_percent = fields.Float(_('Porcentaje'))
    guardianship = fields.Boolean(_('Custodia'))
    phone = fields.Char(_('Número de contacto'))

    @api.constrains('identification_id', 'passport_id')
    def _check_identification_number(self):
        for row in self:
            if row.identification_id is False and row.passport_id is False:
                raise ValidationError(
                    _('The employee must have an identification number or passport number'))

            identification_ids = [i.id for i in self.search([('identification_id', '=', row.identification_id),
                                                             ('identification_id', '!=', False)])]
            if identification_ids and row.id not in identification_ids:
                raise ValidationError(_('The identification number must be unique per employee'))
            passport_ids = [i.id for i in self.search([('passport_id', '=', row.passport_id),
                                                       ('passport_id', '!=', False)])]
            if passport_ids and row.id not in passport_ids:
                raise ValidationError(_('The identification number must be unique per employee'))
            if row.identification_id and not vat.ci.is_valid(row.identification_id):
                raise ValidationError(_('The identification number is wrong'))
