# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "l10n_ec_pos",
    'version': '11.0.0.1',
    'description': """
        Add required partner fields in POS. Create invoices when sales are validate. Credit Notes.
    """,
    'summary': """
        epayment is an auxiliar field used for einvoces to be authorized even if pos session stills open. Generate access keys.
        Create invoices whyn sales are validate. Credit Notes.
        New credit journal. Code = NCRD.
        Modified by cgonzalezbrito.
    """,
    'author': "Cristian Salamea",
    'website': "http://www.ayni.com.ec",
    'license': 'AGPL-3',
    'category': 'POS',
    'depends': [
        'point_of_sale',
        'l10n_ec_authorisation',
        'l10n_ec_pos_refund',
        'account_invoice_refund_link',
    ],
    'data': [
        'data/pos.xml',
        'data/credit.xml',
        'views/pos_view.xml',
        'views/pos_refund_view.xml',
        'ticket_layout.xml',
        'close_control_report.xml',
        'report_closing_control.xml',
    ],
    'qweb': [
        'static/src/xml/l10n_ec_pos.xml',
        'static/src/xml/pos.xml'
    ]
}
