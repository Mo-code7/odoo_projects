/** @odoo-module **/

import publicWidget from 'web.public.widget';

publicWidget.registry.PortalSmartContractSignature = publicWidget.Widget.extend({
    selector: '#signatureModal',
    events: {
        'submit form': '_onSubmitSignature',
    },

    start: function () {
        return this._super.apply(this, arguments);
    },

    _onSubmitSignature: function (ev) {
        const signerName = this.$('#signer_name').val().trim();
        if (!signerName) {
            ev.preventDefault();
            alert("Signer Name is required to sign the contract digitally.");
        }
    }
});
