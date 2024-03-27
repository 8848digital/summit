from shutil import ExecError

import frappe

from summitapp.api.v2.product.product_details import get_details
from summitapp.api.v2.product.product_list import get_list
from summitapp.api.v2.utilities.fields import get_field_names
from summitapp.api.v2.utilities.utils import error_response, success_response


def get(kwargs):
	filters = {"publish": 1}
	if brands := get_allowed_brands():
		filters["name"] = ["in", brands]

	ignore_permissions = bool(frappe.session.user == "Guest")
	field_names = get_field_names("Brand")
	brand_list = frappe.db.get_list(
		"Brand", filters=filters, fields=field_names, ignore_permissions=ignore_permissions
	)
	transformed_brand_list = []

	for brand in brand_list:
		transformed_brand = get_brand_json(brand)
		transformed_brand["url"] = f"/brand/{brand.get('slug')}"
		transformed_brand_list.append(transformed_brand)
	return success_response(data=transformed_brand_list)


def get_brand_json(brand):
	transformed_brand = {}
	for field_name in brand:
		transformed_brand[field_name] = brand[field_name]
	return transformed_brand


def get_product_list(kwargs):
	try:
		brand_name = kwargs.get("brand_name")
		brand_name = frappe.db.get_value("Brand", {"slug": brand_name}, "name")
		return get_list({"brand": brand_name})
	except Exception as e:
		frappe.logger("brand").exception(e)
		return error_response(e)


def get_product_details(kwargs):
	try:
		brand_name, item = kwargs.get("brand_name"), kwargs.get("item")
		brand_name = frappe.db.get_value("Brand", {"slug": brand_name}, "name")
		return get_details({"brand": brand_name, "item": item})
	except Exception as e:
		frappe.logger("brand").exception(e)
		return error_response(e)


def check_brand_exist(filters):
	return any("brand" in i for i in filters)


def get_allowed_brands():
	brands = []
	user = frappe.session.user
	if user != "Guest":
		cust = frappe.db.get_value(
			"Customer", {"email": user}, ["name", "customer_group"], as_dict=1
		)
		if cust:
			brands = frappe.db.get_values(
				"Brand Multiselect", {"parent": cust["name"]}, "name1", pluck=1
			)
			if not brands and cust.get("customer_group"):
				brands = frappe.db.get_values(
					"Brand Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1
				)
	if not brands:
		brands = frappe.db.get_values(
			"Brand Multiselect", {"parent": "Web Settings"}, "name1", pluck=1
		)
	return brands
