import frappe
from summit_api.utils import error_response, success_response, create_temp_user, get_company_address, check_guest_user
from summit_api.api.v1.product import get_stock_info, get_slide_images, get_recommendation, get_product_url
from summit_api.api.v1.utils import get_price_list,get_field_names
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe.utils import flt, getdate
import json

def get_list(kwargs):
	try:
		if frappe.session.user != "Guest":
			email = frappe.session.user
		else:
			return error_response('Please login as a customer')

		customer = frappe.get_value("Customer",{'email':email})
		result, grand_total, grand_total_excluding_tax = get_quotation_details(customer)
		return {'msg': 'success', 'data': result, 'grand_total_including_tax': grand_total,'grand_total_excluding_tax': grand_total_excluding_tax}
	except Exception as e:
		frappe.logger('cart').exception(e)
		return error_response(e)


def put_products(kwargs):  
	try:
		if frappe.session.user == "Guest":
			create_temp_user()

		items = kwargs.get('item_list')
		if isinstance(items,str):
			items = json.loads(items)
		item_list = []
		if not items:
			return error_response('Please Specify item list')

		allow_items_not_in_stock = frappe.db.get_single_value("Web Settings", "allow_items_not_in_stock")
		for row in items:
			kwargs.update({"item_only":1,"item_code":row.get("item_code"), "ptype":"Mandatory"})
			recommendations = get_recommendation(kwargs)
			if recommendations:
				for item in recommendations:
					if not item:
						continue
					item_list.append({"item_code": item, "quantity": row["quantity"]})
			else:
				item_list.append({"item_code": row.get("item_code"), "quantity": row["quantity"]})

		in_stock_status = True
		for item in item_list:
			quantity = item.get('quantity') or 1
			if product_bundle:=frappe.db.exists("Product Bundle", {'new_item_code': item.get("item_code")}):
				item_bundle_list = frappe.get_list("Product Bundle Item",{'parent':product_bundle},['item_code','qty'], ignore_permissions=1)
				for i in item_bundle_list:
					if int(get_stock_info(i.item_code, 'stock_qty')) < int(quantity) * flt(i.qty):
						in_stock_status = False
						break
			else:
				if int(get_stock_info(item.get("item_code"), 'stock_qty')) < int(quantity):
					in_stock_status = False
			if (not in_stock_status) and (not allow_items_not_in_stock): return error_response('Stock Not Available!')
		
		added_to_cart = add_item_to_cart(item_list, frappe.session.sid)
		return success_response(data = added_to_cart)
	except Exception as e:
		frappe.logger('cart').exception(e)
		return error_response(e)

def delete_products(kwargs):  
	try:
		if frappe.session.user != "Guest":
			email = frappe.session.user
		else:
			return error_response('Please Login To Continue')

		item_code = kwargs.get('item_code')
		quotation_id = kwargs.get("quotation_id")
		customer = frappe.db.get_value('Customer', {"email": email})
		if not quotation_id:
			quotation_id = frappe.db.exists("Quotation",{'party_name': customer, 'status': 'Draft'})
		if not quotation_id:
			return error_response("Cart not found")
		quot_doc = frappe.get_doc('Quotation', quotation_id)
		
		params = {"item_only":1,"item_code":item_code, "ptype":"Mandatory"}
		item_list = []
		recommendations = get_recommendation(params)
		if recommendations:
			for item in recommendations:
				if not item:
					continue
				item_list.append(item)
		else:
			item_list.append(item_code)

		deleted_from_cart = delete_item_from_cart(item_list, quot_doc)
		return success_response(data = deleted_from_cart)
	except Exception as e:
		frappe.logger('cart').exception(e)
		return error_response('error deleting items to cart')


def clear_cart(kwargs):
	try:
		if frappe.session.user == "Guest":
			return error_response('Please login as a customer')
		quotation_id = kwargs.get('quotation_id')
		if not quotation_id: return error_response('Quotation Not Found')
		frappe.delete_doc("Quotation",quotation_id,ignore_permissions=True, ignore_missing=True)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)

def get_quotation_details(customer=None):
    or_filter = {"owner": frappe.session.user}
    if customer:
        or_filter["party_name"] = customer
    quotations = frappe.get_list("Quotation", filters={'status': 'Draft'}, or_filters=or_filter, fields='*')
    grand_total = 0
    item_fields = []
    grand_total_excluding_tax = 0
    for quot in quotations:
        quot_doc = frappe.get_doc('Quotation', quot['name'])
        grand_total = quot_doc.rounded_total or quot_doc.grand_total
        grand_total_excluding_tax = quot_doc.total
        item_fields = get_processed_cart(quot_doc)
    return item_fields, grand_total,grand_total_excluding_tax

def get_processed_cart(quot_doc):
    field_names = get_field_names('Cart')
    processed_items = []
    for item in quot_doc.items:
        item_doc = frappe.db.get_value("Item",item.item_code,"*")
        computed_fields = {
            'party_name': lambda:{'party_name':quot_doc.party_name},
            'name': lambda:{'name':quot_doc.name},
            'total_qty': lambda: {'total_qty':quot_doc.total_qty},
	    	'colour':lambda:{'colour':quot_doc.colour},
		    'cust_name':lambda:{'cust_name':quot_doc.cust_name},
		    'transaction_date':lambda:{'transaction_date':quot_doc.transaction_date},
			'common_comment':lambda:{'common_comment':quot_doc.common_comment},
			'orders':lambda:{'orders':get_order_items(item_doc, item)},
			'level_1_category':lambda:{'level_1_category':item_doc.get("level_1_category")},
			'level_2_category':lambda:{'level_2_category':item_doc.get("level_2_category")},
			'min_order_qty': lambda: {'min_order_qty': item_doc.get("min_order_qty")},
			'category': lambda: {'category': item_doc.category},
			'brand_img': lambda:{'brand_img':frappe.get_value('Brand', {'name': item_doc.get('brand')}, 'image')},
			'level_three_category_name': lambda: {'level_three_category_name': item_doc.get("level_three_category_name")},
			'tax': lambda: {'tax': flt(get_item_wise_tax(quot_doc.taxes).get(item_doc.name, {}).get('tax_amount', 0), 2)},
   			'product_url': lambda: {'product_url': get_product_url(item_doc)},
			'in_stock_status': lambda:{"in_stock_status": True if get_stock_info(item_doc.name, 'stock_qty') != 0 else False},
			'image_url':lambda:{"image_url": get_slide_images(item.item_code, True)},
			'details':lambda:{"details": get_item_details(item_doc, item)},
   			'store_pickup_available':lambda:{"store_pickup_available" : item_doc.get("store_pick_up_available", "No")},
			'home_delivery_available':lambda:{"home_delivery_available" : item_doc.get("home_delivery_available", "No")}
		}
        item_fields = {}
        for field_name in field_names:
            if field_name in computed_fields.keys():
                item_fields.update(computed_fields.get(field_name)())
            else:
                item_fields.update({field_name: item.get(field_name)})
        processed_items.append(item_fields)    
    return processed_items

def get_order_items(item_doc,item):
	if item_doc:
		return {
			'item_code': item_doc.item_code,
			'weight_abbr':item_doc.weight_abbr,
			'level_1_category':item_doc.level_1_category,
			'level_2_category':item_doc.level_2_category,
			'qty':item.qty,
			'size':item.size,
			'colour': item.colour,
			'bar_code_image':get_bar_code_image(item_doc['item_code']),
			'remark':item.remark,
			'wastage':item.wastage
		}

@frappe.whitelist(allow_guest=True)
def get_bar_code_image(item_code):
	# pip install python-barcode
	from barcode import Code128
	from barcode.writer import ImageWriter
	image_name = item_code + '_bar_code'  
	barcode_path = frappe.get_site_path()+'/public/files/'
	item_bar_code = Code128(item_code, writer=ImageWriter())	
	item_bar_code.save(barcode_path + image_name)  
	return frappe.utils.get_url() + f'/files/{image_name}.png'

def get_item_wise_tax(taxes):
	itemised_tax = {}
	for tax in taxes:
		if getattr(tax, "category", None) and tax.category == "Valuation":
			continue

		item_tax_map = json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
		if item_tax_map:
			for item_code, tax_data in item_tax_map.items():
				itemised_tax.setdefault(item_code, frappe._dict())
				existing = itemised_tax.get(item_code)
				tax_rate = existing.get('tax_rate',0.0)
				tax_amount =  existing.get('tax_amount',0.0)

				if isinstance(tax_data, list):
					tax_rate += flt(tax_data[0])
					tax_amount += flt(tax_data[1])
				else:
					tax_rate += flt(tax_data)

				itemised_tax[item_code] = frappe._dict(
					dict(tax_rate=tax_rate, tax_amount=tax_amount)
				)

	return itemised_tax

def calculate_quot_taxes(quot_doc):
	sales_taxes_and_charges_template = frappe.db.get_value('Quotation', quot_doc.get("name"), 'taxes_and_charges')
	if not sales_taxes_and_charges_template: return "Item Added To Cart"
	taxes = get_taxes_and_charges("Sales Taxes and Charges Template",sales_taxes_and_charges_template)
	quot = frappe.get_doc('Quotation', quot_doc.get("name"))
	quot.taxes = []
	for i in taxes:
		quot.append('taxes', i)
	if quot:
		quot.save(ignore_permissions=True)  
	else:
		return {'name': quot_doc.get("name")}
	return {'name': quot_doc.get("name")}


def create_cart(session_id = frappe.session.user, party_name = None):
	or_filter = {
		"session_id": session_id
	}
	if party_name:
		or_filter["party_name"] = party_name

	if quot:=frappe.db.get_list("Quotation",filters = {'status': 'Draft'}, or_filters = or_filter, fields=['name']):
		quot_doc = frappe.get_doc('Quotation', quot[0].get('name'))
	else:
		quot_doc = frappe.new_doc('Quotation')
		quot_doc.order_type = "Shopping Cart"
		quot_doc.party_name = party_name
		quot_doc.session_id = session_id
		if check_guest_user(frappe.session.user):
			quot_doc.gst_category = "Unregistered"
		company_addr = get_company_address(quot_doc.company)
		quot_doc.company_address = company_addr.get("company_address")
		quot_doc.company_gstin = company_addr.get("gstin")
	return quot_doc

def add_item_to_cart(item_list, session):
	# quotation = quot_doc
	customer_id = frappe.db.get_value('Customer', {'email': frappe.session.user})
	quotation = create_cart(session, customer_id)
	price_list = get_price_list(customer_id)
	quotation.selling_price_list = price_list
	for item in item_list:
		quotation_items = quotation.get("items", {"item_code": item.get("item_code")})
		if not quotation_items:
			item_data = {
                "doctype": "Quotation Item",
                "item_code": item.get("item_code"),
                "qty": item.get("quantity")
            }
			if "size" in item:
				item_data["size"] = item["size"]
			if "wastage" in item:
				item_data["wastage"] = item["wastage"]
			if "remark" in item:
				item_data["remark"] = item["remark"]
			if "colour" in item:
				item_data["colour"] = item["colour"]
			if "purity" in item:
				item_data["purity"] = item["purity"]
			quotation.append("items", item_data)
		else:
			quotation_items[0].qty = item.get("quantity")
			
	# apply_cart_settings(quotation=quotation)
	quotation.flags.ignore_mandatory = True
	quotation.flags.ignore_permissions = True
	quotation.payment_schedule = []
	quotation.save()
	return f'Item {", ".join([row["item_code"] for row in item_list])} Added To Cart'

def delete_item_from_cart(item_list, quot_doc):
	item_deleted = False
	for item in item_list:
		quotation_items = quot_doc.get("items", {"item_code": item})
		if quotation_items and len(quot_doc.get("items",[])) == 1:
			frappe.delete_doc("Quotation",quot_doc.name,ignore_permissions=True)
			return "Item Deleted"
		elif quotation_items:
			frappe.db.delete('Quotation Item', 
							{'parent': quot_doc.name, 'item_code': item})
			quot_doc.reload()
			item_deleted = True
	if item_deleted:
		quot_doc.reload()
		quot_doc.save(ignore_permissions=True)
		return 'Item Deleted'
	return f"Following Items: {', '.join(item_list)} do not exist in cart!"


def get_item_details(item_doc, item_row):
	res = []
	res.append({'name': 'Model No', 'value': item_doc.name})
	res.append({'name': 'Price', 'value': item_row.get("price_list_rate")})
	res.extend({"name": attr.attribute, "value": attr.attribute_value} for attr in item_doc.get("attributes",[]))
	return res

def request_for_quotation(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	quot_id = kwargs.get('quotation_id')
	if not quot_id:
		return error_response("Quotation id is required")
	doc = frappe.get_doc("Quotation",quot_id)
	new_doc = frappe.get_doc(doc.as_dict().copy()).insert(ignore_permissions=1)
	doc.send_quotation = 1
	doc.flags.ignore_permissions=1
	doc.submit()
	return success_response(data={"quotation_id":new_doc.name})

def get_quotation_history(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	customer = kwargs.get("customer_id")
	if not customer:
		customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
	if not customer:
		return error_response('Please login as a customer')
	send_quotation = kwargs.get("only_requested",1)
	filters = {"party_name": customer, "send_quotation":send_quotation,"docstatus":1}
	quotations = frappe.get_list("Quotation",filters=filters,fields=["name","modified","total_qty", "rounded_total","grand_total"])
	if quotations:
		quotations = [
			{
				"name": row.name,
				"enquiry_date": getdate(row.modified),
				"total_qty": row.total_qty,
				"grand_total": row.get("rounded_total") or row.grand_total,
				"print_url": get_pdf_link("Quotation",row.name)
			} for row in quotations
		]
	return success_response(data=quotations)

def get_pdf_link(voucher_type, voucher_no, print_format = None):
	if not print_format:
		print_format = frappe.db.get_value(
			"Property Setter",
			dict(property="default_print_format", doc_type=voucher_type),
			"value",
		)
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}&no_letterhead=0&settings=%7B%7D&_lang=en"
	return "#"
