/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.portalDetails = publicWidget.Widget.extend({
    selector: '.jt_country_state_details',
	    events: {
	        'change select[name="country"]': '_onCountryChange',
	    },
	    /**
	     * @override
	     */
	    start: function () {
	    	var def = this._super.apply(this, arguments);
	        this.$state = this.$('select[name="state_id"]');
	        this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
	        this._adaptAddressForm();
	        return def;
	    },
	    //--------------------------------------------------------------------------
	    // Private
	    //--------------------------------------------------------------------------
	    /**
	     * @private
	     */
	    _adaptAddressForm: function () {
	        var $country = this.$('select[name="country"]');
	        var countryID = ($country.val() || 0);
	        this.$stateOptions.detach();
	        var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
	        var nb = $displayedState.appendTo(this.$state).show().length;
	        this.$state.parent().toggle(nb >= 1);
	    },
	    //--------------------------------------------------------------------------
	    // Handlers
	    //--------------------------------------------------------------------------
	    /**
	     * @private
	     */
	    _onCountryChange: function () {
	        this._adaptAddressForm();
	    },
});