odoo.define('l10n_ec_pos', function(require) {
"use strict";

    var PosDB = require('point_of_sale.DB');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var clave_acceso;
    var inv_number;
    var sequence;

    PosDB.include({

        _partner_search_string: function(partner){
            var str =  partner.name;
            if(partner.identifier){
	        str += '|' + partner.identifier;
            }
            if(partner.ean13){
                str += '|' + partner.ean13;
            }
            if(partner.address){
                str += '|' + partner.address;
            }
            if(partner.phone){
                str += '|' + partner.phone.split(' ').join('');
            }
            if(partner.mobile){
                str += '|' + partner.mobile.split(' ').join('');
            }
            if(partner.email){
                str += '|' + partner.email;
            }
            str = '' + partner.id + ':' + str.replace(':','') + '\n';
            return str;
        }

    });

    var pos_models = models.PosModel.prototype.models;
    var _super_order_model = models.Order.prototype;

    var _super_pos_model = models.PosModel.prototype;

    var rpc = require('web.rpc');
    var core = require('web.core');

    var first_receipt = true;

    var sequence_array = new Array();

    models.Order = models.Order.extend({

	    initialize: function(attributes,options){
            _super_order_model.initialize.call(this, attributes, options);
            var customer = this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]);
            if (!customer){
                console.log('WARNING: no default partner in POS');
            }else{
                this.set({ client: customer });
            }
        },
    });

    screens.ReceiptScreenWidget.include({
        render_receipt: function(){

            var self = this;
            
            var order = this.pos.get_order();
            var date = moment().format('DDMMYYYY');
            var tcomp = '01';
            var ruc = this.pos.company.vat;
            var env = this.pos.company.env_service;
            var journal = this.pos.config.invoice_journal_id[0];
            var electronic_jornal = this.pos.config.electronic_journal;
            var seq = this.pos.config.seq_access_key[0];
            var mod;

            var QWeb = core.qweb;

            if (electronic_jornal){

                if (first_receipt) {
                    first_receipt = false;
                    rpc.query({
                        model: 'pos.order',
                        method: 'get_inv_number',
                        args:[
                            [''],
                            [journal],
                        ],
                    }).then(function(res_inv_number){
                        inv_number = res_inv_number;
                        rpc.query({
                            model: 'pos.order',
                            method: 'get_pos_code',
                            args:[
                                [''],
                                [seq],
                            ],
                        }).then(function (res_sequence){
                            sequence = res_sequence;
                            clave_acceso = date + tcomp + ruc + env + inv_number + sequence + '1';
                            mod = self.compute_mod11(clave_acceso);
                            clave_acceso += mod;
                            self.$('.pos-receipt-container').html(QWeb.render('PosTicket', self.get_receipt_render_env()));    
                            console.log(clave_acceso);
                            // alert('ALERTA')
                        });
                    });
                    sequence_array[sequence_array.length] = order.sequence_number;
                } else {
                    self.$('.pos-receipt-container').html(QWeb.render('PosTicket', self.get_receipt_render_env()));    
                }
            } else {
                self.$('.pos-receipt-container').html(QWeb.render('PosTicketComprobante', self.get_receipt_render_env()));    
            }
        },
        render_change: function(){
            var self = this;
            this.$('.change-value').html(this.format_currency(this.pos.get_order().get_change()));
            var order = this.pos.get_order();
            var order_screen_params = order.get_screen_data('params');
            var button_print_invoice = this.$('.button.print_invoice');
            if (order_screen_params && order_screen_params.button_print_invoice) {
                button_print_invoice.show();
            } else {
                button_print_invoice.hide();
            }
            
            if (!first_receipt && !sequence_array.includes(order.sequence_number) && electronic_jornal) {
                var date = moment().format('DDMMYYYY');
                var tcomp = '01';
                var ruc = this.pos.company.vat;
                var env = this.pos.company.env_service;
                //var journal = this.pos.config.invoice_journal_id[0];
                var mod;
                inv_number = Number(inv_number) + 1;
                sequence = Number(sequence) + 1;
                sequence = ('00000000' + sequence).slice(-8);
                clave_acceso = date + tcomp + ruc + env + '00' + inv_number + sequence + '1';
                mod = self.compute_mod11(clave_acceso);
                clave_acceso += mod;
                console.log(clave_acceso);
                sequence_array[sequence_array.length] = order.sequence_number;
            }
        },
        compute_mod11: function(value){
            var total = 0;
            var weight = 2;

            for (var i = value.length - 1; i >= 0; i--) {
                total += parseInt(value[i])*weight;
                weight += 1;
                if (weight > 7){
                    weight = 2;
                }
            }
            var mod = 11 - total%11;
            if (mod === 11){return 0;} else if (mod === 10 ) {return 1;} else {return mod;}
        },
        get_clave_start: function(){
            return clave_acceso.substr(0,24)
        },
        get_clave_end: function(){
            return clave_acceso.substr(24,25);
        },
        get_invoice_number: function(){
            inv_number = ('000000000000000' + inv_number).slice(-15);
            return inv_number;
        },
        get_env_service: function(){
            if (this.pos.company.env_service === '2') {return 'PRODUCCIÓN';} else {return 'PRUEBAS';}

        },
    });

    screens.PaymentScreenWidget.include({

        order_is_valid: function(force_validation) {
            var self = this;
            var order = this.pos.get_order();
            
            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Order'),
                    'body':  _t('There must be at least one product in your order before it can be validated'),
                });
                return false;
            }

            if (!order.get_client()){
                alert('No ha seleccionado Cliente')
                return false;
            }

            if (!order.is_paid() || this.invoicing) {
                return false;
            }

            if (order.get_total_paid() <= 0){
                alert('No se pueden crear facturas con base imponible igual a $0.00');
                return false;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error',{
                        title: _t('Cannot return change without a cash payment method'),
                        body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return false;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && order.get_total_with_tax() > 0 && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm',{
                    title: _t('Please Confirm Large Amount'),
                    body:  _t('Are you sure that the customer wants to  pay') + 
                           ' ' + 
                           this.format_currency(order.get_total_paid()) +
                           ' ' +
                           _t('for an order of') +
                           ' ' +
                           this.format_currency(order.get_total_with_tax()) +
                           ' ' +
                           _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function() {
                        self.validate_order('confirm');
                    },
                });
                return false;
            }

            return true;
        },
    });

    for (var i=0; i<pos_models.length; i++){
        var model = pos_models[i];
        if (model.model === 'res.partner') {
            model.fields.push('identifier', 'type_id', 'tipo_persona','refund_credit');
        }
        if (model.model === 'res.company') {
	        model.fields.push('street', 'env_service', 'namerl');
        }
    }
});
