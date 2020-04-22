odoo.define('l10n_ec_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    var _super_order_model = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order_model.initialize.call(this, attributes, options);
            var customer = this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]);
            if (!customer) {
                console.log('WARNING: no default partner in POS');
            } else {
                this.set({ client: customer });
            }
        },
    });

    var pos_models = models.PosModel.prototype.models;
    for (var i = 0; i < pos_models.length; i++) {
        var model = pos_models[i];
        if (model.model === 'res.partner') {
            model.fields.push('identifier', 'type_id', 'tipo_persona', 'refund_credit');
        }
        if (model.model === 'res.company') {
            model.fields.push('street', 'env_service', 'namerl');
        }
    }
});
