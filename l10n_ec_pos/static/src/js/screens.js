odoo.define('l10n_ec_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var first_receipt = true;
    var sequence_array = new Array();
    var clave_acceso;
    var inv_number;
    var sequence;
    var QWeb = core.qweb;
    var _t = core._t

    /*--------------------------------------*\
     |         THE RECEIPT SCREEN           |
    \*======================================*/

    // The receipt screen displays the order's
    // receipt and allows it to be printed in a web browser.
    // The receipt screen is not shown if the point of sale
    // is set up to print with the proxy. Altough it could
    // be useful to do so...

    screens.ReceiptScreenWidget.include({
        render_receipt: function () {
            var self = this;

            var order = this.pos.get_order();
            var date = moment().format('DDMMYYYY');
            var tcomp = '01';
            var ruc = this.pos.company.vat;
            var env = this.pos.company.env_service;
            var journal = this.pos.config.invoice_journal_id[0];
            var electronic_journal = this.pos.config.electronic_journal;
            var seq = this.pos.config.seq_access_key[0];
            var mod;

            if (electronic_journal) {
                if (first_receipt) {
                    first_receipt = false;
                    rpc.query({
                        model: 'pos.order',
                        method: 'get_inv_number',
                        args: [
                            [''],
                            [journal],
                        ],
                    }).then(function (res_inv_number) {
                        inv_number = res_inv_number;
                        rpc.query({
                            model: 'pos.order',
                            method: 'get_pos_code',
                            args: [
                                [''],
                                [seq],
                            ],
                        }).then(function (res_sequence) {
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
        render_change: function () {
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

            if (!first_receipt && !sequence_array.includes(order.sequence_number) && electronic_journal) {
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
        compute_mod11: function (value) {
            var total = 0;
            var weight = 2;

            for (var i = value.length - 1; i >= 0; i--) {
                total += parseInt(value[i]) * weight;
                weight += 1;
                if (weight > 7) {
                    weight = 2;
                }
            }
            var mod = 11 - total % 11;
            if (mod === 11) { return 0; } else if (mod === 10) { return 1; } else { return mod; }
        },
        get_clave_start: function () {
            return clave_acceso.substr(0, 24)
        },
        get_clave_end: function () {
            return clave_acceso.substr(24, 25);
        },
        get_invoice_number: function () {
            inv_number = ('000000000000000' + inv_number).slice(-15);
            return inv_number;
        },
        get_env_service: function () {
            if (this.pos.company.env_service === '2') { return 'PRODUCCIÓN'; } else { return 'PRUEBAS'; }

        },
    });

    /*--------------------------------------*\
     |         THE PAYMENT SCREEN           |
    \*======================================*/

    // The Payment Screen handles the payments, and
    // it is unfortunately quite complicated.

    screens.PaymentScreenWidget.include({
        order_is_valid: function (force_validation) {
            var self = this;
            var order = this.pos.get_order();
            var qtyNull = false;
            var priceNull = false;

            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('alert', {
                    'title': _t('Orden Vacia'),
                    'body': _t('Debe haber al menos un producto en su orden antes de que pueda ser validado'),
                });
                return false;
            }

            order.orderlines.forEach(function (line) {
                if (line.quantity <= 0) {
                    qtyNull = true;
                }
                if (line.price <= 0){
                    priceNull = true;
                }
            });

            if (qtyNull) {
                this.pos.gui.show_popup('alert', {
                    'title': _t('Item vacio'),
                    'body': _t('La cantidad de uno o más de los items ingresados es 0, ingrese una cantidad o elimine el item'),
                });
                return false;
            }

            if (priceNull) {
                this.pos.gui.show_popup('alert', {
                    'title': _t('Precio unitario cero'),
                    'body': _t('El precio unitario de uno o más de los items ingresados es 0, ingrese el precio correcto o elimine el item'),
                });
                return false;
            }

            if (!order.get_client()) {
                this.pos.gui.show_popup('alert', {
                    'title': _t('Aviso'),
                    'body': _t('No ha seleccionado Cliente'),
                });
                return false;
            }

            if (!order.is_paid() || this.invoicing) {
                return false;
            }

            if (order.get_total_paid() <= 0) {
                this.pos.gui.show_popup('alert', {
                    'title': _t('Aviso'),
                    'body': _t('No se pueden crear facturas con base imponible igual a $0.00'),
                });
                return false;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('alert', {
                        title: _t('No se puede dar cambio sin un método de pago'),
                        body: _t('No hay un método de pago disponible en este punto de venta para manejar el cambio.\n\n Por favor pague la cantidad exacta o agregue un método de pago en la configuración del punto de venta'),
                    });
                    return false;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && order.get_total_with_tax() > 0 && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm', {
                    title: _t('Please Confirm Large Amount'),
                    body: _t('Are you sure that the customer wants to  pay') +
                        ' ' +
                        this.format_currency(order.get_total_paid()) +
                        ' ' +
                        _t('for an order of') +
                        ' ' +
                        this.format_currency(order.get_total_with_tax()) +
                        ' ' +
                        _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function () {
                        self.validate_order('confirm');
                    },
                });
                return false;
            }

            return true;
        },
    });
});
