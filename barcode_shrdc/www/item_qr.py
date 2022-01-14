from __future__ import unicode_literals
import frappe, json, urllib

def get_context(context):
    barcode = frappe.form_dict.barcode
    item_code = frappe.form_dict.item_code
    item = frappe.get_doc("Item",item_code)
    item_name = item.item_name
    image = item.image if item.image else "/files/No-Image-Placeholder.png"
    item_price = frappe.form_dict.rate
    serial_no = frappe.form_dict.serial_no
    batch_no = frappe.form_dict.batch_no
    if batch_no:
      batch_doc = frappe.get_doc("Batch",batch_no)
      mfg_date = batch_doc.manufacturing_date
      exp_date = batch_doc.exp_date
    else:
      mfg_date = None
      exp_date = None

    if serial_no:
      serial_doc = frappe.get_doc("Serial No",serial_no)
      warranty_exp_date = serial_doc.warranty_expiry_date
      amc_exp_date = serial_doc.amc_expiry_date
      serial_purchase_doc=  serial_doc.purchase_document_no
      serial_purchase_date=  serial_doc.purchase_date
      delivery_doc=  serial_doc.delivery_document_no
      delivery_date= serial_doc.delivery_date
    else:
      warranty_exp_date = None
      amc_exp_date = None
      serial_purchase_doc=  None
      serial_purchase_date=  None
      delivery_doc=  None
      delivery_date=  None
    route = frappe.utils.get_url( "/desk#Form/Item/"+urllib.parse.quote(item_code),None)
    
    return {
      "item_name": item_name,
      "item_code": item_code,
      "rate": item_price,
      "serial_no": serial_no,
      "batch_no": batch_no,
      "image": image,
      "mfg_date": mfg_date,
      "exp_date": exp_date,
      "warranty_exp_date": warranty_exp_date,
      "amc_exp_date": amc_exp_date,
      "creation_doc": serial_purchase_doc,
      "creation_date": serial_purchase_date,
      "delivery_doc": delivery_doc,
      "delivery_doc": delivery_date,
      "route": route
	}