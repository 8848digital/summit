import json

import frappe
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils import cint
from frappe.utils.global_search import search

from summitapp.api.v2.category import (get_allowed_categories,
                                       get_child_categories)
from summitapp.api.v2.filter import append_applied_filters, get_filter_listing
from summitapp.api.v2.product.product_limit import get_list_product_limit
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.utilities.user import (create_user_tracking,
                                             get_customer_id)
from summitapp.api.v2.utilities.utils import error_response, get_access_level
from summitapp.api.v2.variant import get_variant_details, get_variant_info


@frappe.whitelist()
def get_list(kwargs):
	from summitapp.api.v2.brand import check_brand_exist
	from summitapp.api.v2.utilities.fields import get_processed_list

	try:
		create_user_tracking(kwargs, "Product Listing")
		internal_call = kwargs.get("internal", 0)
		category_slug = kwargs.get("category")
		page_no = cint(kwargs.get("page_no", 1)) - 1
		customer_id = get_customer_id(kwargs)
		user_role = frappe.session.user
		product_limit = get_list_product_limit(user_role, customer_id)
		if product_limit != 0:
			limit = product_limit
		else:
			limit = kwargs.get("limit", 20)
		filter_list = kwargs.get("filter")
		field_filters = kwargs.get("field_filters")
		or_filters = kwargs.get("or_filters")
		price_range = kwargs.get("price_range")
		search_text = kwargs.get("search_text")
		currency = kwargs.get("currency")
		access_level = get_access_level(customer_id)
		if not search_text:
			order_by = None
			filter_args = {"access_level": access_level}
			if category_slug:
				child_categories = get_child_categories(category_slug)
				filter_args["category"] = child_categories
			if kwargs.get("brand"):
				filter_args["brand"] = frappe.get_value("Brand", {"slug": kwargs.get("brand")})

			if kwargs.get("item"):
				print("@@@", kwargs.get("item"))
				filter_args["name"] = frappe.get_value("Item", {"name": kwargs.get("item")})

			filters = get_filter_listing(filter_args)
			type = "brand-product" if check_brand_exist(filters) else "product"
			if field_filters:
				field_filters = json.loads(field_filters)
				for value in field_filters.values():
					if len(value) == 2 and value[0] == "like":
						value[1] = f"%{value[1]}%"
				filters.update(field_filters)
			if or_filters:
				or_filters = json.loads(or_filters)
				for value in or_filters.values():
					if len(value) == 2 and value[0] == "like":
						value[1] = f"%{value[1]}%"
			if filter_list:
				filter_list = json.loads(filter_list)
				filters, sort_order = append_applied_filters(filters, filter_list)
				if sort_order:
					order_by = "sequence {}".format(sort_order)
					del filters["sequence"]
			debug = kwargs.get("debug_query", 0)
			count, data = get_list_data(
				order_by,
				filters,
				price_range,
				None,
				page_no,
				limit,
				or_filters=or_filters,
				debug=debug,
			)
		else:
			type = "product"
			global_items = search(search_text, doctype="Item")
			count, data = get_list_data(None, {}, price_range, global_items, page_no, limit)
		result = get_processed_list(currency, data, customer_id, type)
		print("RESTULT", result)
		total_count = count
		translated_item_fields = translate_result(result)
		if internal_call:
			return translated_item_fields
		return {"msg": "success", "data": translated_item_fields, "total_count": total_count}
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(str(e))


def get_list_data(
	order_by, filters, price_range, global_items, page_no, limit, or_filters=None, debug=0
):
	from summitapp.api.v2.brand import get_allowed_brands

	if or_filters is None:
		or_filters = {}
	offset = 0
	if page_no is not None:
		offset = int(page_no) * int(limit)
	if "access_level" not in filters:
		filters["access_level"] = 0

	if categories := get_allowed_categories(filters.get("category")):
		filters["category"] = ["in", categories]
	if brands := get_allowed_brands():
		if not (filters.get("brand") and filters.get("brand") in brands):
			filters["brand"] = ["in", brands]

	if global_items is not None:
		return get_items_via_search(global_items, filters)

	ignore_permissions = frappe.session.user == "Guest"

	if not order_by:
		order_by = (
			"valuation_rate asc"
			if price_range != "high_to_low"
			else "valuation_rate desc"
			if price_range
			else ""
		)
	else:
		order_by = order_by
	data = frappe.get_list(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields="*",
		limit_page_length=limit,
		limit_start=offset,
		order_by=order_by,
		ignore_permissions=ignore_permissions,
		debug=debug,
	)
	count = get_count(
		"Item", filters=filters, or_filters=or_filters, ignore_permissions=ignore_permissions
	)

	if limit == 1:
		data = data[0] if data else []

	return count, data


def get_count(doctype, **args):
	distinct = "distinct " if args.get("distinct") else ""
	args["fields"] = [f"count({distinct}`tab{doctype}`.name) as total_count"]
	res = DatabaseQuery(doctype).execute(**args)
	data = res[0].get("total_count")
	return data


def get_items_via_search(global_items, filters):
	item_list = []
	items = [item.name for item in global_items]
	filters["name"] = ["in", items]
	ignore_permission = bool(frappe.session.user == "Guest")
	item_list = frappe.get_list("Item", filters, "*", ignore_permissions=ignore_permission)
	return len(item_list), item_list


def get_item(item_code, size, colour):  # for cart
	variant_list = get_variant_details({"item_code": item_code})
	variants = get_variant_info(variant_list)
	if size and colour:
		item_code = [
			i.get("variant_code")
			for i in variants
			if i.get("size") == size and i.get("colour") == colour
		]
	elif size:
		item_code = [i.get("variant_code") for i in variants if i.get("size") == size]
	elif colour:
		item_code = [i.get("variant_code") for i in variants if i.get("colour") == colour]
	else:
		item_code = [item_code]
	return item_code[0] if item_code else []


def get_product_url(item_detail, url_type="product"):
	if not item_detail:
		return "/"
	item_cat = item_detail.get("category")
	item_cat_slug = frappe.db.get_value("Category", item_cat, "slug")
	product_slug = item_detail.get("slug")
	from summitapp.api.v2.mega_menu import get_item_url

	return get_item_url(url_type, item_cat_slug, product_slug)
