// Copyright (c) 2018, Crisco Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on('Price Calculator', {
	refresh: function (frm) {

	}
});

cur_frm.add_fetch("device", "buying_rate", "buying_rate")
cur_frm.add_fetch("device", "parameters", "parameters")


frappe.ui.form.on("Price Calculator", {
	"parameters": function (cur_frm) {
		cur_frm.clear_table("price_attributes");
		cur_frm.refresh_field("price_attributes");
		if (cur_frm.doc.parameters) {
			frappe.model.with_doc("Parameters", cur_frm.doc.parameters, function () {
				var tabletransfer = frappe.model.get_doc("Parameters", cur_frm.doc.parameters)
				console.log(tabletransfer)
				$.each(tabletransfer.price_attributes, function (index, row) {
					var d = cur_frm.add_child("price_attributes");
					d.parameter = row.parameter;
					d.type = row.type;
					d.image = row.image;
					d.rate = flt(cur_frm.doc.buying_rate * (row.percent * 0.01));
					if (row.type == "Substract") {
						d.rate = -1 * d.rate
					}
					d.percent = row.percent;
					cur_frm.refresh_field("price_attributes");
				});

			});
		}
		else {
			frappe.msgprint(__("Please set Parameters in  {0} ", [cur_frm.doc.device]));
		}

	},
	
	"refresh": function (cur_frm) {
		cur_frm.fields_dict['device'].get_query = function (doc, cdt, cdn) {
			return {
				filters: {
					'is_purchase_item': 1,
					'is_fixed_asset': 0,
					'disabled': 0,
					'has_variants': 0,
				}
			}
		}
	}

});





// frappe.ui.form.on("[TARGETDOCTYPE]", {
//     "[TRIGGER]": function(frm) {
//         frappe.model.with_doc("[SOURCEDOCTYPE]", frm.doc.[TRIGGER], function() {
//             var tabletransfer= frappe.model.get_doc("[SOURCEDOCTYPE]", frm.doc.[TRIGGER])
//             $.each(tabletransfer.[SOURCECHILDTABLE], function(index, row){
//                 d = frm.add_child("[TARGETCHILDTABLE]");
//                 d.[TARGETFIELD1] = row.[SOURCEFIELD1];
//                 d.[TARGETFIELD2] = row.[SOURCEFIELD2];
//                 frm.refresh_field("[TARGETCHILDTABLE]");
//             });
//         });
//     }
// });