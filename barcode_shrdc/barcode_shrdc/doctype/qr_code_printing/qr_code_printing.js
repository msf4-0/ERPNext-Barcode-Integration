frappe.ui.form.on('QR Code Printing', {
	refresh: function(frm) {
		frm.add_custom_button(__('Purchase Receipt'), function() {
			erpnext.utils.map_current_doc({
				method: "barcode_shrdc.barcode_shrdc.doctype.barcode_printing.barcode_printing.pr_make_barcode",
				source_doctype: "Purchase Receipt",
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

		frm.add_custom_button(__('Stock Entry'), function() {
			erpnext.utils.map_current_doc({
				method: "barcode_shrdc.barcode_shrdc.doctype.barcode_printing.barcode_printing.se_make_barcode",
				source_doctype: "Stock Entry",
				target: frm,
				date_field: "posting_date",
				setters: {
					stock_entry_type: frm.doc.stock_entry_type,
				},
				get_query_filters: {
					docstatus: 1
				}
			})

		}, __("Get items from"));
	}
});