// Copyright (c) 2018, Crisco Consulting and contributors
// For license information, please see license.txt


cur_frm.add_fetch("model", "buying_rate", "buying_rate")
frappe.ui.form.on('Model Wise Parameter', {
	refresh: function(frm) {
		cur_frm.fields_dict['model'].get_query = function (doc, cdt, cdn) {
			return {
				filters: {
					'is_purchase_item': 1,
					'is_fixed_asset': 0,
					'disabled': 0,
					'has_variants': 0,
					"show_in_website": 1
				}
			}
		}

	}
});
