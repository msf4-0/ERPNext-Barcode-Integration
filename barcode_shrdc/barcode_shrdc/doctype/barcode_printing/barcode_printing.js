// Copyright (c) 2021, lxy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Barcode Printing', {
	setup: function(frm){
		frm.set_value("show_sku",0);
		frm.set_value("show_serial_no",0);
		frm.set_value("show_batch_no",0);
	},
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
	},
	validate: function(frm)
	{
		for(let item of frm.doc.items)
		{
			if (item.serial_no)
			{
				var serial_numbers = item.serial_no.split("\n");
					if (serial_numbers[serial_numbers.length-1]=='')
					{
						serial_numbers.pop();
					}
				console.log(serial_numbers);
				var qty = item.qty;
				if (serial_numbers.length != qty || qty ==0)
				{
					frappe.validated = false;
					frappe.msgprint({
						title: __('Warning'),
						indicator: 'red',
						message: __('{0}: serial no. does not match the number of qty.',[item.item_code]),
					});
				}
			}


		
		}


	},
	get_barcode: function(frm)
	{
		frm.doc.items.forEach(d =>			
			{
				if (d.item_code)
				{
					console.log("HELLO");
					frappe.call({
						method: "barcode_shrdc.barcode_shrdc.doctype.barcode_printing.barcode_printing.search_item_serial_or_batch_or_barcode_number",
						args: {
							search_value:1,
							item:d
						},
						callback: function(r) {
							console.log(r);
							var barcode_val = r.message.barcode;
							var barcode_type = r.message.barcode_type;
							frappe.model.set_value(d.doctype,d.name,"barcode",barcode_val);
							frappe.model.set_value(d.doctype,d.name,"barcode_type",barcode_type);		
						}
					})
				}
	
			})
	},
	show_sku: function(frm) {
		frm.trigger("show_sku_barcode");
	},
	show_batch_no: function(frm) {
		frm.trigger("show_batch_no_barcode");
	},
	batch_barcode_type: function(frm) {
		frm.trigger("show_batch_no_barcode");
	},
	show_serial_no: function(frm) {
		frm.trigger("show_serial_no_barcode");
	},
	serial_barcode_type: function(frm) {
		frm.trigger("show_serial_no_barcode");
	},
	create_qr: function(frm)
	{
		frappe.call({
			method: "barcode_shrdc.barcode_shrdc.doctype.barcode_printing.barcode_printing.make_qrcode",
			args: {
				doc:frm.doc,
				route: frappe.urllib.get_base_url()

			},
			callback: function(r) {
				console.log(r.message);
				frm.set_value("qrcodes",r.message);
				frm.set_value("qr_created",1);
				$(frm.fields_dict['qrcodes'].$wrapper).html(r.message)
			}
		})

	},
	show_sku_barcode: function(frm) {
		if(frm.doc.show_sku) 
		{
			// var barcodes_html = document.querySelectorAll(`[data-fieldname='${"barcodes"}']`)[0];
			// var sku_html = barcodes_html.getElementsByClassName("dashboard-section");
			// if (!sku_html.length)
			// {
				$.getScript("https://cdn.jsdelivr.net/npm/jsbarcode@3.11.0/dist/JsBarcode.all.min.js", function( data, textStatus, jqxhr ) {
					var sku_content = '<div class="dashboard-section">';
				var items = frm.doc.items;
				var i = 1;
				for (const item of items)
				{
					
					var barcode_format = item.barcode_type;
					var barcode = item.barcode;
					var item_code = item.item_code;
					var item_name = item.item_name;
					var item_price = item.rate;
					var qty = item.qty
					sku_content += '<div class="row">';


					sku_content += '<div class="barcode-label-container"><div class="barcode-label" id="barcode-label">';
					if (barcode && barcode_format)
						  {
								sku_content += '<div class="label-item-barcode label-field">';
								sku_content+= '<div class="barcode-container"><svg class="barcode'+i+'"></svg></div></div>';
								sku_content += '<div class="label-item-code label-field">';
								sku_content +=item_code +': ' +item_name + '</div>';
								sku_content+=	  '<div class="label-item-price label-field2">RM '+item_price.toFixed(2);
								sku_content += '</div><div style= "font-weight:bold; font-family:Sans-serif	;"> 	x'+ qty+'</div> </div> <hr>';
						  }

						  else
						  {
							// sku_content+='<div class="label-item-code-alone label-field">'+item_code + '</div><hr>';
						  }


					sku_content +='</div></div></div>';
					i++;
				}	
				sku_content +='</div>';	
				$(frm.fields_dict['barcodes'].$wrapper).html(sku_content)
				.css({"margin-left": "20px", "margin-top": "10px", "font-family":"monospace"});
				i=1;
				for (const item of items)
				{
					var barcode_format = item.barcode_type;
					var barcode = item.barcode;
					if (barcode && barcode_format)
					{
						JsBarcode(".barcode"+i,barcode, {
							background: "#FFFFFF",
							format: barcode_format,
							width:2,
							height:40,
						});
					}
					i++;
				}
			});
			// }
		}
	},
	show_serial_no_barcode: function(frm) {
		if(frm.doc.show_serial_no) 
		{
			// var barcodes_html = document.querySelectorAll(`[data-fieldname='${"serials"}']`)[0];
			// var sku_html = barcodes_html.getElementsByClassName("dashboard-section");
			// if (!sku_html.length)
			// {
			$.getScript("https://cdn.jsdelivr.net/npm/jsbarcode@3.11.0/dist/JsBarcode.all.min.js", function( data, textStatus, jqxhr ) {
				var sku_content = '<div class="dashboard-section">';
				var items = frm.doc.items;
				var i = 1;
				var barcode_format = frm.doc.serial_barcode_type;
				var serial;

				for (const item of items)
				{
					
					var serials = item.serial_no;
					var item_code = item.item_code;
					var item_name = item.item_name;
					var item_price = item.rate;
					sku_content += '<div class="row">';

					sku_content += '<div class="barcode-label-container"><div class="barcode-label" id="barcode-label">';
					if (serials && barcode_format)
					{
						serials = serials.split("\n");
						if (serials[serials.length-1]=='')
						{
							serials.pop();
						}
						for(const serial of serials)
						{
							sku_content += '<div class="label-item-barcode label-field">';
							sku_content+= '<div class="barcode-container"><svg class="serial'+i+'"></svg></div></div>';
							sku_content += '<div class="label-item-code label-field">';
							sku_content +=item_code +': ' +item_name + '</div>';
							// sku_content+=	  '<div class="label-item-price label-field2">RM '+item_price.toFixed(2);
							// sku_content += '</div> </div> <hr>';
							sku_content += "<hr></hr>";
						}

					}
					sku_content +='</div></div></div>';
					i++;
				}	
				sku_content +='</div>';	
				$(frm.fields_dict['serials'].$wrapper).html(sku_content)
				.css({"margin-left": "20px", "margin-top": "10px", "font-family":"monospace"});
				i=1;
				for (const item of items)
				{
					var serials = item.serial_no;
					if (serials && barcode_format)
					{
						serials = serials.split("\n");
						if (serials[serials.length-1]=='')
						{
							serials.pop();
						}
						for(const serial of serials)
						{
							JsBarcode(".serial"+i,serial, {
								background: "#FFFFFF",
								format: barcode_format,
								width:2,
								height:40,
							});
						}
					}
					i++;
				}
			});
			// }
		}
	},
	show_batch_no_barcode: function(frm) {
		if(frm.doc.show_batch_no) 
		{
			$.getScript("https://cdn.jsdelivr.net/npm/jsbarcode@3.11.0/dist/JsBarcode.all.min.js", function( data, textStatus, jqxhr ) {
				var sku_content = '<div class="dashboard-section">';
				var items = frm.doc.items;
				var i = 1;
				var barcode_format = frm.doc.batch_barcode_type;

				for (const item of items)
				{
					
					var batch = item.batch_no;
					var item_code = item.item_code;
					var item_name = item.item_name;
					var item_price = item.rate;
					var qty = item.qty;
					sku_content += '<div class="row">';

					sku_content += '<div class="barcode-label-container"><div class="barcode-label" id="barcode-label">';
					if (batch && barcode_format)
					{
						sku_content += '<div class="label-item-barcode label-field">';
						sku_content+= '<div class="barcode-container"><svg class="batch'+i+'"></svg></div></div>';
						sku_content += '<div class="label-item-code label-field">';
						sku_content += item_code +': ' +item_name + '</div>';
						// sku_content+=	  '<div class="label-item-price label-field2">RM '+item_price.toFixed(2);
						// sku_content += '</div> </div> <hr>';
						sku_content += '<div style= "font-weight:bold; font-family:Sans-serif	;"> 	x'+ qty+'</div><hr></hr>';
					}
					sku_content +='</div></div></div>';
					i++;
				}	
				sku_content +='</div>';	
				$(frm.fields_dict['batchs'].$wrapper).html(sku_content)
				.css({"margin-left": "20px", "margin-top": "10px", "font-family":"monospace"});
				i=1;
				for (const item of items)
				{
					var batch = item.batch_no;
					if (batch && barcode_format)
					{
						JsBarcode(".batch"+i,batch, {
							background: "#FFFFFF",
							format: barcode_format,
							width:2,
							height:40,
						});
						
					}
					i++;
				}
			});
		}
	},
	set_serial_no: function(frm, cdt, cdn, callback) {
		var d = frappe.model.get_doc(cdt, cdn);
		if(!d.item_code && !d.s_warehouse && !d.qty) return;
		var	args = {
			'item_code'	: d.item_code,
			'warehouse'	: cstr(d.s_warehouse),
			'stock_qty'		: d.transfer_qty
		};
		frappe.call({
			method: "erpnext.stock.get_item_details.get_serial_no",
			args: {"args": args},
			callback: function(r) {
				if (!r.exe && r.message) {
					frappe.model.set_value(cdt, cdn, "serial_no", r.message);

					if (callback) {
						callback();
					}
				}
			}
		});
	},
	set_basic_rate: function(frm, cdt, cdn) {
		const item = locals[cdt][cdn];
		item.transfer_qty = flt(item.qty) * flt(item.conversion_factor);

		const args = {
			'item_code'			: item.item_code,
			'posting_date'		: frm.doc.posting_date,
			'posting_time'		: frm.doc.posting_time,
			'warehouse'			: cstr(item.s_warehouse) || cstr(item.t_warehouse),
			'serial_no'			: item.serial_no,
			'company'			: frm.doc.company,
			'qty'				: item.s_warehouse ? -1*flt(item.transfer_qty) : flt(item.transfer_qty),
			'voucher_type'		: frm.doc.doctype,
			'voucher_no'		: item.name,
			'allow_zero_valuation': 1,
		};

		if (item.item_code || item.serial_no) {
			frappe.call({
				method: "erpnext.stock.utils.get_incoming_rate",
				args: {
					args: args
				},
				callback: function(r) {
					frappe.model.set_value(cdt, cdn, 'basic_rate', (r.message || 0.0));
				}
			});
		}
	},
	items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no();
	},

});

frappe.ui.form.on('Barcode Generator Items', {
	qty: function(frm, cdt, cdn) {
		frm.events.set_serial_no(frm, cdt, cdn, () => {
			frm.events.set_basic_rate(frm, cdt, cdn);
		});
	},

	conversion_factor: function(frm, cdt, cdn) {
		frm.events.set_basic_rate(frm, cdt, cdn);
	},

	s_warehouse: function(frm, cdt, cdn) {
		frm.events.set_serial_no(frm, cdt, cdn, () => {
			frm.events.get_warehouse_details(frm, cdt, cdn);
		});
	},

	t_warehouse: function(frm, cdt, cdn) {
		frm.events.get_warehouse_details(frm, cdt, cdn);
	},

	barcode: function(doc, cdt, cdn) {
		frm.set_value("qr_created",0);
		frm.set_value("show_sku",0);

		var d = locals[cdt][cdn];
		if (d.barcode) {
			frappe.call({
				method: "erpnext.stock.get_item_details.get_item_code",
				args: {"barcode": d.barcode },
				callback: function(r) {
					if (!r.exe){
						frappe.model.set_value(cdt, cdn, "item_code", r.message);
					}
				}
			});
		}
	},

	uom: function(doc, cdt, cdn) {
		var d = locals[cdt][cdn];
		if(d.uom && d.item_code){
			return frappe.call({
				method: "erpnext.stock.doctype.stock_entry.stock_entry.get_uom_details",
				args: {
					item_code: d.item_code,
					uom: d.uom,
					qty: d.qty
				},
				callback: function(r) {
					if(r.message) {
						frappe.model.set_value(cdt, cdn, r.message);
					}
				}
			});
		}
	},
	serial_no(frm){
		frm.set_value("qr_created",0);
		frm.set_value("show_serial_no",0);
	},
	batch_no(frm){
		frm.set_value("qr_created",0);
		frm.set_value("show_batch_no",0);
	},
	items_add: function(frm){
		frm.set_value("qr_created",0);
		frm.set_value("show_sku",0);
		frm.set_value("show_serial_no",0);
		frm.set_value("show_batch_no",0);

	},
	items_remove:function(frm){
		frm.set_value("qr_created",0);
		frm.set_value("show_sku",0);
		frm.set_value("show_serial_no",0);
		frm.set_value("show_batch_no",0);

	},
	item_code: function(frm, cdt, cdn) {
		frm.set_value("qr_created",0);
		frm.set_value("show_sku",0);
		frm.set_value("show_serial_no",0);
		frm.set_value("show_batch_no",0);
		var d = locals[cdt][cdn];
		if(d.item_code) {
			var args = {
				'item_code'			: d.item_code,
				'warehouse'			: cstr(d.s_warehouse) || cstr(d.t_warehouse),
				'serial_no'		: d.serial_no,
				'bom_no'		: d.bom_no,
				'expense_account'	: d.expense_account,
				'cost_center'		: d.cost_center,
				'company'		: frm.doc.company,
				'qty'			: d.qty,
				'voucher_type'		: frm.doc.doctype,
				'voucher_no'		: d.name,
				'allow_zero_valuation': 1,
			};

			return frappe.call({
				doc: frm.doc,
				method: "get_item_details",
				args: args,
				callback: function(r) {
					if(r.message) {
						var d = locals[cdt][cdn];
						$.each(r.message, function(k, v) {
							if (v) {
								frappe.model.set_value(cdt, cdn, k, v); // qty and it's subsequent fields weren't triggered
							}
						});
						frm.refresh_field("items");

						if (!d.serial_no) {
							erpnext.stock.select_batch_and_serial_no(frm, d);
						}
					}
				}
			});
		}
	}
});

$.extend(cur_frm.cscript, new erpnext.stock.StockController({frm: cur_frm}));

erpnext.stock.select_batch_and_serial_no = (frm, item) => {
	let get_warehouse_type_and_name = (item) => {
		let value = '';
		if(frm.fields_dict.from_warehouse.disp_status === "Write") {
			value = cstr(item.s_warehouse) || '';
			return {
				type: 'Source Warehouse',
				name: value
			};
		} else {
			value = cstr(item.t_warehouse) || '';
			return {
				type: 'Target Warehouse',
				name: value
			};
		}
	}

	if(item && !item.has_serial_no && !item.has_batch_no) return;
	if (frm.doc.purpose === 'Material Receipt') return;

	frappe.require("assets/erpnext/js/utils/serial_no_batch_selector.js", function() {
		new erpnext.SerialNoBatchSelector({
			frm: frm,
			item: item,
			warehouse_details: get_warehouse_type_and_name(item),
		});
	});

}