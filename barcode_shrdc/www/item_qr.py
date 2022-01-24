from __future__ import unicode_literals
from dataclasses import asdict
from locale import currency
import frappe, json, urllib
from erpnext.stock.report.stock_projected_qty.stock_projected_qty import get_bin_list
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, get_url
no_cache = 1

def get_context(context):
    barcode = frappe.form_dict.barcode
    item_code = frappe.form_dict.item_code
    item = frappe.get_doc("Item",item_code)
    item_name = item.item_name
    image = item.image if item.image else "/files/No-Image-Placeholder.png"
    serial_no = frappe.form_dict.serial_no
    batch_no = frappe.form_dict.batch_no
    # rate = rate_doc[0]#.get_formatted("price_list_rate")
    
    if batch_no:
      batch_doc = frappe.get_doc("Batch",batch_no)
      mfg_date = batch_doc.manufacturing_date
      exp_date = batch_doc.expiry_date
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
      serial_tracking_table = get_serial_tracking_table(item_code, serial_no)

    else:
      warranty_exp_date = None
      amc_exp_date = None
      serial_purchase_doc=  None
      serial_purchase_date=  None
      delivery_doc=  None
      delivery_date=  None
      serial_tracking_table = ""
    
    warehouse_table = get_warehouse_table(item_code)
    route = frappe.utils.get_url( "/desk#Form/Item/"+urllib.parse.quote(item_code),None)
    return {
      "item_name": item_name,
      "item_code": item_code,
      "barcode": barcode,
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
      "delivery_date": delivery_date,
      "warehouse_table": warehouse_table,
      "serial_tracking_table": serial_tracking_table,
      "route": route
	}

def get_warehouse_table(item_code):
  filters = frappe._dict({"item_code":item_code})
  bin_list = get_bin_list(filters)
  warehouse_table = ""
  for bin in bin_list:
    warehouse_table += "<tr><td>"+bin.warehouse+"</td><td>"+str(bin.actual_qty)+"</td>"
  return warehouse_table

def get_serial_tracking_table(item_code, serial_no):
  sle_list = frappe.db.sql("""select timestamp(posting_date, posting_time) as "timestamp",
    warehouse, actual_qty, incoming_rate, voucher_type, voucher_no 
    from `tabStock Ledger Entry`
		where item_code = %s and ifnull(is_cancelled, 'No')='No'
		and (serial_no = %s
						or serial_no like %s
						or serial_no like %s
						or serial_no like %s
					)
    and warehouse not like "In Transit%%"
    order by timestamp(posting_date, posting_time) """, 
    (item_code, serial_no, serial_no+'\n%', '%\n'+serial_no, '%\n'+serial_no+'\n%'), as_dict = 1)
  serial_tracking_table = ""
  for sle in sle_list:
    if(sle.voucher_type == "Stock Entry"):
      company = frappe.get_doc(sle.voucher_type,sle.voucher_no).company
      currency_pre = frappe.get_doc("Currency", frappe.get_doc("Company", company).default_currency).symbol
    else:
      currency = frappe.get_doc(sle.voucher_type,sle.voucher_no).currency
      currency_pre = frappe.get_doc("Currency", currency).symbol
    serial_tracking_table += "<tr><td>" + str(sle.timestamp) +"</td>"
    serial_tracking_table += "<td>"+ sle.warehouse +"</td>"
    serial_tracking_table += "<td>"+ str(sle.actual_qty) +"</td>"
    serial_tracking_table += "<td>"+ currency_pre+" "+ str(sle.incoming_rate) +"</td>"
    serial_tracking_table += "<td>"+ sle.voucher_type +"</td>"
    serial_tracking_table += "<td><a href='{2}/desk#Form/{0}/{1}' style='font-weight: bold;'>{1}</a></td></tr>".format(sle.voucher_type, sle.voucher_no, get_url())
  return serial_tracking_table

