# -*- coding: utf-8 -*-
# Copyright (c) 2021, lxy and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json, urllib
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import msgprint, _ 
from six import string_types, iteritems
import qrcode, io, os
from io import BytesIO	
import base64
from frappe.integrations.utils import make_get_request, make_post_request, create_request_log
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, get_url
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
import requests
from PIL import Image




class BarcodePrinting(Document):
	def get_open_purchase_receipt(self):
		""" Pull Purchase Receipt based on criteria selected"""
		open_pr = get_purchase_receipts(self)

		if open_pr:
			self.add_pr_in_table(open_pr)
		else:
			frappe.msgprint(_("Purchase Order not available"))

	def add_pr_in_table(self, open_pr):
		""" Add sales orders in the table"""
		self.set('purchase_receipt', [])

		for data in open_pr:
			self.append('purchase_receipts', {
				'purchase_receipt': data.name,
				'pr_date': data.posting_date,
				'supplier': data.supplier,
				'grand_total': data.total
			})

	def get_items(self):
		if self.get_items_from == "Purchase Receipt":
			self.get_pr_items()
		elif self.get_items_from == "Stock Entry":
			self.get_se_items()
	
	def get_pr_se_list(self, field, table):
		"""Returns a list of Purchase Orders or Stock Entries from the respective tables"""
		pr_se_list = [d.get(field) for d in self.get(table) if d.get(field)]
		return pr_se_list

	def get_pr_items(self):
		# Check for empty table or empty rows
		if not self.get("purchase_receipts") or not self.get_pr_se_list("purchase_receipt", "purchase_receipts"):
			frappe.throw(_("Please fill the Purchase Receipt table"), title=_("Purchase Receipt Required"))

		pr_list = self.get_pr_se_list("purchase_receipt", "purchase_receipts")
		
		item_condition = ""
		if self.item_code:
			item_condition = ' and pr_item.item_code = {0}'.format(frappe.db.escape(self.item_code))
		items = frappe.db.sql("""select distinct pr_item.parent, pr_item.item_code, pr_item.warehouse,
			pr_item.qty, pr_item.description, pr_item.name, pr_item.uom, pr.supplier, pr_item.barcode, 
			pr_item.serial_no, pr_item.batch_no, 
			item.barcode
			from `tabPurchase Receipt Item` pr_item , `tabPurchase Receipt` pr, `tabItem Barcode` item
			where pr_item.parent in (%s) and pr_item.docstatus = 1  and item.parent = %s""" % \
			(", ".join(["%s"] * len(pr_list))),self.item_code, tuple(pr_list), as_dict=1)

		if self.item_code:
			item_condition = ' and so_item.item_code = {0}'.format(frappe.db.escape(self.item_code))

		self.add_items(items)
	
	def add_items(self, items):
		self.set('items', [])
		for data in items:
			pi = self.append('items', {
				'warehouse': data.warehouse,
				'item_code': data.item_code,
				
				'description': data.description,
				'qty': data.qty,
				'supplier': data.supplier,
				'uom': data.uom,
				'barcode': data.barcode,
				'serial_no': data.serial_no,
				'batch_no': data.batch_no
			})

			if self.get_items_from == "Purchase Receipt":
				pi.ref_pr = data.parent
				pi.description = data.description

			elif self.get_items_from == "Stock Entry":
				pi.ref_se = data.parent
				pi.description = data.description
	
	def get_item_barcode(self):
		print(self.items)
		item = frappe.db.sql("""select barcode, barcode_type
			from `tabItem Barcode` 
			where parent=%s""",
			"ITM-001", as_dict = 1)

		if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached"))

		item = item[0]
		
		return item

	def get_item_details(self, args=None, for_update=False):
		item = frappe.db.sql("""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
				i.has_batch_no, i.sample_quantity, i.has_serial_no, i.allow_alternative_item,
				id.expense_account, id.buying_cost_center
			from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
			where i.name=%s
				and i.disabled=0
				and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
			(self.company, args.get('item_code'), nowdate()), as_dict = 1)

		if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

		item = item[0]

		ret = frappe._dict({
			'uom'			      	: item.stock_uom,
			'stock_uom'				: item.stock_uom,
			'description'		  	: item.description,
			'image'					: item.image,
			'item_name' 		  	: item.item_name,
			'qty'					: args.get("qty"),
			'conversion_factor'		: 1,
			'batch_no'				: '',
			'actual_qty'			: 0,
			'basic_rate'			: 0,
			'serial_no'				: '',
			'has_serial_no'			: item.has_serial_no,
			'has_batch_no'			: item.has_batch_no,
			'sample_quantity'		: item.sample_quantity
		})

		return ret
	

	

def get_purchase_receipts(self):
	pr_filter = item_filter = ""
	if self.from_date:
		pr_filter += " and pr.posting_date >= %(from_date)s"
	if self.to_date:
		pr_filter += " and pr.posting_date <= %(to_date)s"
	if self.warehouse:
		pr_filter += " and pr.set_warehouse = %(warehouse)s"
	if self.supplier:
		pr_filter += " and pr.supplier = %(supplier)s"

	if self.item_code:
		item_filter += " and pr_item.item_code = %(item)s"

	open_pr = frappe.db.sql("""
		select distinct pr.name, pr.posting_date, pr.supplier, pr.base_grand_total
		from `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pr_item
		where pr_item.parent = pr.name
			and pr.docstatus = 1 and pr.status not in ("Stopped", "Closed")
			and pr.company = %(company)s
		""".format(pr_filter, item_filter), {
			"from_date": self.from_date,
			"to_date": self.to_date,
			"supplier": self.supplier,
			"set_warehouse": self.warehouse,
			"item": self.item_code,
			"company": self.company
		}, as_dict=1)
	return open_pr




@frappe.whitelist()
def pr_make_barcode(source_name, target_doc=None):
	doc = get_mapped_doc("Purchase Receipt", source_name, {
		"Purchase Receipt": {
			"doctype": "Barcode Printing",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Purchase Receipt Item": {
			"doctype": "Barcode Generator Items",
			"field_map": {
				"stock_qty": "qty",
				"batch_no": "batch_no",
				"parent": "ref_pr",
				"price_list_rate":"basic_rate",
				"serial_no":"serial_no",
				"batch_no":"batch_no",
				"set_warehouse":"warehouse"
			},
		}
	}, target_doc)

	return doc

@frappe.whitelist()
def se_make_barcode(source_name, target_doc=None):
	# print(json.loads(target_doc)["name"])

	def check_manufacturing(d):
		# print(frappe.get_doc("Stock Entry",d.parent).stock_entry_type)
		if frappe.get_doc("Stock Entry",d.parent).stock_entry_type == "Manufacture":
			return  (d.t_warehouse != None)
		return 1

	doclist = get_mapped_doc("Stock Entry", source_name, {
		"Stock Entry": {
			"doctype": "Barcode Printing",
			"validation": {
				"docstatus": ["=", 1],
			},
			"field_map": {
				"get_items_from" :"doctype"
			}
		},
		"Stock Entry Detail": {
			"doctype": "Barcode Generator Items",
			"field_map": {
				"valuation_rate":"rate",
				"qty": "qty",
				"uom": "uom",
				"parent": "ref_se",
				"serial_no":"serial_no",
				"batch_no":"batch_no",
				"additional_cost":"additional_cost"	,
				"t_warehouse":"warehouse"
			},
			"condition":check_manufacturing
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def search_item_serial_or_batch_or_barcode_number(search_value,item):
	# search barcode no
	item = json.loads(item)
	barcode_data = frappe.db.get_value('Item Barcode', {'parent': item["item_code"]}, ['barcode', 'barcode_type', 'parent as item_code'], as_dict=True)
	if barcode_data:
		if barcode_data.barcode_type == "EAN":
			barcode_data.barcode_type = "EAN13"
		elif barcode_data.barcode_type == "UPC-A":
			barcode_data.barcode_type = "UPC"
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}

@frappe.whitelist()
def get_item_details(frm):
	items = frm.doc.items
	item_code_list = [d.get("item_code") for d in items if d.get("item_code")]
	print(item_code_list)
	item = frappe.db.sql("""select barcode, barcode_type
		from `tabItem Barcode` 
		where i.parent=%s""",
		format(frappe.db.escape(frm.item_code)), as_dict = 1)

	if not item:
		frappe.throw(_("Item {0} is not active or end of life has been reached"))

	item = item[0]
	
	return item

@frappe.whitelist()
def create_barcode_printing(throw_if_missing, se_id,pr_id):	
	# se = frappe.get_doc("Stock Entry", se_id)
	# pr = frappe.get_doc("Purchase Receipt",pr_id)
	bp = frappe.new_doc('Barcode Printing')

	if(se_id):
		se = frappe.get_doc("Stock Entry", se_id)
		for item in se.items:
			if 	item.t_warehouse != None:
				row = bp.append('items', {})
				row.item_code = item.item_code
				row.qty = item.qty
				row.basic_rate = item.basic_rate
				row.rate = item.valuation_rate
				row.uom = item.uom
				row.additional_cost = item.additional_cost
				row.conversion_factor = item.conversion_factor
				row.serial_no = item.serial_no
				row.batch_no = item.batch_no
				row.ref_se = se_id
	
	if(pr_id):
		pr = frappe.get_doc("Purchase Receipt",pr_id)
		for item in pr.items:
			row = bp.append('items', {})
			row.item_code = item.item_code
			row.qty = item.qty
			row.basic_rate = item.price_list_rate
			row.rate = item.rate
			row.uom = item.uom
			row.serial_no = item.serial_no
			row.batch_no = item.batch_no
			row.ref_pr = pr_id
			row.warehouse = pr.set_warehouse

	bp.insert(
		ignore_mandatory=True
		)

	if not frappe.db.exists(bp.doctype, bp.name):
		if throw_if_missing:
			frappe.throw('Linked document (Stock Entry / Purchase Receipt) not found')
	return frappe.get_doc(bp.doctype, bp.name)

@frappe.whitelist()
def make_qrcode(doc, route):
	qr_html = ''
	barcode_doc = frappe.get_doc("Barcode Printing", json.loads(doc)["name"])
	items = barcode_doc.items
	for item in items:
		if item.get("qty")!= 0:
			if item.get("serial_no"):
				serials = item.get("serial_no").split("\n")
				if serials[-1] == '':
					serials.pop()
				for serial in serials:
					uri  = "item_qr?"
					if item.get("item_code"): uri += "item_code=" + urllib.parse.quote(item.get_formatted("item_code")) 
					if item.get("barcode"): uri += "&barcode=" + urllib.parse.quote(item.get_formatted("barcode")) 
					if serial: uri += "&serial_no=" + urllib.parse.quote(serial) 
					if item.get("batch_no"): uri += "&batch_no=" + urllib.parse.quote(item.get_formatted("batch_no")) 
					# if item.get("rate"): uri += "&rate=" + urllib.parse.quote(item.get_formatted("rate")) 
					img_str = qr_code_img(uri)
					qr_html += '<img src="' + "data:image/png;base64,{0}".format(img_str.decode("utf-8")) + '" width="240px"/><br>'
			else:
				uri  = "item_qr?"
				if item.get("item_code"): uri += "item_code=" + urllib.parse.quote(item.get_formatted("item_code")) 
				if item.get("barcode"): uri += "&barcode=" + urllib.parse.quote(item.get_formatted("barcode")) 
				if item.get("batch_no"): uri += "&batch_no=" + urllib.parse.quote(item.get_formatted("batch_no")) 
				# if item.get("rate"): uri += "&rate=" + urllib.parse.quote(item.get_formatted("rate")) 
				img_str = qr_code_img(uri)
				qr_html += '<img src="' + "data:image/png;base64,{0}".format(img_str.decode("utf-8")) + '" width="240px"/><br>'
	return qr_html

def qr_code_img(uri):
	qr_config = frappe.get_doc("QR Code Configuration")
	qr = qrcode.QRCode(
		border=qr_config.border,
		error_correction=qrcode.constants.ERROR_CORRECT_H,
	)
	url = get_url(uri,None)
	qr.add_data(url)
	qr.make(fit=True)
	logo = qr_config.logo

	print(get_url(logo,None))
	img = qr.make_image(fill_color = qr_config.fill, back_color = qr_config.background)
	w,h = img.size
	if logo:
		logo = Image.open(requests.get(get_url(logo,None), stream=True).raw).resize((w//4, h//4))
		pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
		img.paste(logo, pos)

	buffered = BytesIO()
	img.save(buffered, format="PNG")
	buffered.seek(0)
	img_str = base64.b64encode(buffered.read())
	return img_str


