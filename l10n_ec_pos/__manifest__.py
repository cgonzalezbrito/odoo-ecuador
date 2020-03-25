# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "l10n_ec_pos",
    'version': '11.0.0.1',
    'description': """
        Add required partner fields in POS. Create invoices when sales are validate. Credit Notes.
    """,
    'summary': """
        Generate access keys.
        Create invoices when sales are validate. Credit Notes.
        New credit journal. Code = NCRD.
    """,
    'author': "Cristian Salamea",
    'website': "http://www.ayni.com.ec",
    'license': 'AGPL-3',
    'category': 'POS',
    'depends': [
        'point_of_sale',
        'l10n_ec_authorisation',
        'account_invoice_refund_link',
    ],
    'data': [
        'data/pos_data.xml',
        'data/pos_refund_credit_data.xml',
        'views/pos_refund_credit_view.xml',
        'views/pos_templates.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/ticket_layout.xml',
        'report/close_control_report.xml',
        'report/report_closing_control.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/ticket.xml',
    ],
    'images': ['static/description/thumbnail.png'],
    'installable': True,
    'auto_install': False,
}
