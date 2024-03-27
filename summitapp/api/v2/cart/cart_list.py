import json

import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe.utils import flt

from summitapp.api.v2.cart.cart_details import get_quotation_details
from summitapp.api.v2.category import get_parent_categories
from summitapp.api.v2.slide_imgaes import get_slide_images
from summitapp.api.v2.stock import get_stock_info
from summitapp.api.v2.utilities import get_currency, get_currency_symbol
from summitapp.api.v2.utilities.fields import get_field_names
from summitapp.api.v2.utilities.user import get_logged_user
from summitapp.api.v2.utilities.utils import error_response


@frappe.whitelist(allow_guest=True)
def get_list(kwargs):
	try:
		email = None
		token = None
		headers = frappe.request.headers
		if not headers or "Authorization" not in headers:
			return error_response("Please Specify Authorization Token")
		auth_header = headers.get("Authorization")
		if "token" in auth_header:
			email = get_logged_user()
		else:
			token = auth_header
		customer = frappe.get_value("Customer", {"email": email})
		result = get_quotation_details(customer, token)
		return {"msg": "success", "data": result}
	except Exception as e:
		frappe.logger("cart").exception(e)
		return error_response(e)


def get_processed_cart(quot_doc):
	item_dict = {}
	category_wise_item = {}
	processed = []
	field_names = get_field_names(
		"Cart"
	)  # Retrieve field names from admin-controlled function
	for row in quot_doc.items:
		item_doc = frappe.db.get_value("Item", row.item_code, "*")
		computed_fields = {
			"min_order_qty": lambda item_doc=item_doc: {
				"min_order_qty": item_doc.get("min_order_qty")
			},
			"weight_per_unit": lambda item_doc=item_doc: {
				"weight_per_unit": item_doc.get("weight_per_unit")
			},
			"total_weight": lambda row=row: {"total_weight": row.get("total_weight")},
			"brand_img": lambda item_doc=item_doc: {
				"brand_img": frappe.get_value("Brand", {"name": item_doc.get("brand")}, "image")
			},
			"level_three_category_name": lambda item_doc=item_doc: {
				"level_three_category_name": item_doc.get("level_three_category_name")
			},
			"tax": lambda item_doc=item_doc, quot_doc=quot_doc: {
				"tax": flt(
					get_item_wise_tax(quot_doc.taxes).get(item_doc.name, {}).get("tax_amount", 0), 2
				)
			},
			"product_url": lambda item_doc=item_doc: {"product_url": get_product_url(item_doc)},
			"in_stock_status": lambda item_doc=item_doc: {
				"in_stock_status": True
				if get_stock_info(item_doc.name, "stock_qty") != 0
				else False
			},
			"image_url": lambda row=row: {"image_url": get_slide_images(row.item_code, True)},
			"details": lambda item_doc=item_doc, row=row: {
				"details": get_item_details(item_doc, row)
			},
			"currency": lambda quot_doc=quot_doc: {"currency": get_currency(quot_doc.currency)},
			"currency_symbol": lambda quot_doc=quot_doc: {
				"currency_symbol": get_currency_symbol(quot_doc.currency)
			},
			"store_pickup_available": lambda item_doc=item_doc: {
				"store_pickup_available": item_doc.get("store_pick_up_available", "No")
			},
			"home_delivery_available": lambda item_doc=item_doc: {
				"home_delivery_available": item_doc.get("home_delivery_available", "No")
			},
		}

		if row.item_code not in item_dict:
			item_dict[row.item_code] = {}
		for field_name in field_names:
			if field_name in computed_fields.keys():
				item_dict[row.item_code].update(computed_fields[field_name]())
			else:
				item_dict[row.item_code].update({field_name: row.get(field_name)})

		existing_cat = category_wise_item.get(item_doc.category)
		item_list = [row.item_code]
		if existing_cat:
			item_list = existing_cat.get("item_list", [])
			if row.item_code not in item_list:
				item_list.append(row.item_code)
		category_wise_item[item_doc.category] = {
			"item_list": item_list,
			"category": item_doc.category,  # Add the category field to the dictionary
		}
	processed = [
		{
			"category": items.get("category"),  # Get the category from the dictionary
			"parent_categories": get_parent_categories(
				items.get("category"), True, name_only=True
			),
			"orders": [item_dict[item] for item in items["item_list"] if item in item_dict],
		}
		for category, items in category_wise_item.items()
	]
	return processed


@frappe.whitelist(allow_guest=True)
def get_bar_code_image(item_code):
	# pip install python-barcode
	from barcode import Code128
	from barcode.writer import ImageWriter

	image_name = item_code + "_bar_code"
	barcode_path = frappe.get_site_path() + "/public/files/"
	item_bar_code = Code128(item_code, writer=ImageWriter())
	item_bar_code.save(barcode_path + image_name)
	return f"/files/{image_name}.png"


def get_item_wise_tax(taxes):
	itemised_tax = {}
	for tax in taxes:
		if getattr(tax, "category", None) and tax.category == "Valuation":
			continue

		item_tax_map = (
			json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
		)
		if item_tax_map:
			for item_code, tax_data in item_tax_map.items():
				itemised_tax.setdefault(item_code, frappe._dict())
				existing = itemised_tax.get(item_code)
				tax_rate = existing.get("tax_rate", 0.0)
				tax_amount = existing.get("tax_amount", 0.0)

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
	sales_taxes_and_charges_template = frappe.db.get_value(
		"Quotation", quot_doc.get("name"), "taxes_and_charges"
	)
	if not sales_taxes_and_charges_template:
		return "Item Added To Cart"
	taxes = get_taxes_and_charges(
		"Sales Taxes and Charges Template", sales_taxes_and_charges_template
	)
	quot = frappe.get_doc("Quotation", quot_doc.get("name"))
	quot.taxes = []
	for i in taxes:
		quot.append("taxes", i)
	if quot:
		quot.save(ignore_permissions=True)
	else:
		return {"name": quot_doc.get("name")}
	return {"name": quot_doc.get("name")}


def get_item_details(item_doc, item_row):
	res = []
	res.append({"name": "Model No", "value": item_doc.name})
	res.append({"name": "Price", "value": item_row.get("price_list_rate")})
	res.extend(
		{"name": attr.attribute, "value": attr.attribute_value}
		for attr in item_doc.get("attributes", [])
	)
	return res


def get_product_url(item_detail):
	if not item_detail:
		return "/"
	item_cat = item_detail.get("category")
	item_cat_slug = frappe.db.get_value("Category", item_cat, "slug")
	if product_template := item_detail.get("variant_of"):
		product_slug = frappe.db.get_value("Item", product_template, "slug")
	else:
		product_slug = item_detail.get("slug")
	from summitapp.api.v2.mega_menu import get_item_url

	return get_item_url("product", item_cat_slug, product_slug)
