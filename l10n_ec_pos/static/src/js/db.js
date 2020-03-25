odoo.define('l10n_ec_pos.db', function (require) {
    "use strict";

    var PosDB = require('point_of_sale.DB');

    PosDB.include({
        _partner_search_string: function (partner) {
            var str = partner.name;
            if (partner.identifier) {
                str += '|' + partner.identifier;
            }
            if (partner.ean13) {
                str += '|' + partner.ean13;
            }
            if (partner.address) {
                str += '|' + partner.address;
            }
            if (partner.phone) {
                str += '|' + partner.phone.split(' ').join('');
            }
            if (partner.mobile) {
                str += '|' + partner.mobile.split(' ').join('');
            }
            if (partner.email) {
                str += '|' + partner.email;
            }
            str = '' + partner.id + ':' + str.replace(':', '') + '\n';
            return str;
        }
    });
});
