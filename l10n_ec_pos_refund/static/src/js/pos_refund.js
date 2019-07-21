odoo.define('l10n_ec_pos_refund', function(require){
"use strict";

    var PosDB = require('point_of_sale.DB');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    screens.PaymentScreenWidget.include({
        
        customer_changed: function() {
            var client = this.pos.get_client();
            this.$('.js_customer_name').text( client ? client.name : _t('Customer') ); 
            console.log(client.refund_credit);
            this.$('.js_customer_credit').text(client.refund_credit)
        },
    });

});
