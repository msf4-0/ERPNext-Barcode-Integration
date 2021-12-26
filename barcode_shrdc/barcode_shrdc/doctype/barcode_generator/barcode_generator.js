// Copyright (c) 2021, lxy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Barcode Generator', {
	refresh: function(frm) {
		frm.add_custom_button(__('Purchase Invoice'), function() {
			erpnext.utils.map_current_doc({
				method: "erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_stock_entry",
				source_doctype: "Purchase Invoice",
				target: frm,
				date_field: "posting_date",
				setters: {
					supplier: frm.doc.supplier || undefined,
				},
				get_query_filters: {
					docstatus: 1
				}
			})
		}, __("Get items from"));

		frm.add_custom_button(__('Material Request'), function() {
			erpnext.utils.map_current_doc({
				method: "erpnext.stock.doctype.material_request.material_request.make_stock_entry",
				source_doctype: "Material Request",
				target: frm,
				date_field: "schedule_date",
				setters: {
					company: frm.doc.company,
				},
				get_query_filters: {
					docstatus: 1,
					material_request_type: ["in", ["Material Transfer", "Material Issue"]],
					status: ["not in", ["Transferred", "Issued"]]
				}
			})
		}, __("Get items from"));
		console.log("HI");
	}
	
});
