// Copyright (c) 2018, Crisco Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on('Parameters', {
	refresh: function (frm) {
		cur_frm.fields_dict['item'].get_query = function (doc, cdt, cdn) {
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
	},

});



