# -*- coding: utf-8 -*-
# Copyright (c) 2022, lxy and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import msgprint, _
from six import string_types, iteritems

class QRCodePrinting(Document):
	def pr_make_barcode(source_name, target_doc=None):
		doc = get_mapped_doc("Purchase Receipt", source_name, {
			"Purchase Receipt": {
				"doctype": "QR Code Printing",
				"validation": {
					"docstatus": ["=", 1]
				}
			},
			"Purchase Receipt Item": {
				"doctype": "QR Code Printing Items",
				"field_map": {
					"stock_qty": "qty",
					"batch_no": "batch_no",
					"parent": "ref_pr",
					"price_list_rate":"basic_rate",
					"serial_no":"serial_no",
					"batch_no":"batch_no"
				},
			}
		}, target_doc)

		return doc