import json

import frappe

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_filters(kwargs):
	try:
		if kwargs.get("doctype") and kwargs.get("docname"):
			doc_name = frappe.db.get_value(
				kwargs.get("doctype"), {"slug": kwargs.get("docname")}
			)
			if not doc_name:
				return error_response("Docname invalid")
			doc = frappe.get_doc(
				"Page Filter Setting",
				{"doctype_name": kwargs.get("doctype"), "doctype_link": doc_name},
			)
			return success_response(data=json.loads(doc.response_json))
		return error_response("please Specify docname and doctype")
	except Exception as e:
		frappe.logger("filter").exception(e)
		return error_response(e)


def get_filter_listing(kwargs):
	filters = {"disabled": 0}
	display_both_item_and_variant = int(
		frappe.db.get_value("Web Settings", "Web Settings", "display_both_item_and_variant")
	)

	if display_both_item_and_variant == 1:
		filters["has_variants"] = 0
		filters["show_on_website"] = 1
	elif kwargs.get("category"):
		filters["show_on_website"] = 1
		filters["has_variants"] = 0
	else:
		filters["variant_of"] = ["is", "not set"]
		filters["has_variants"] = 0

	for key, val in kwargs.items():
		if val:
			filters.update({key: val})
	print("FILTERS", filters)
	return filters


def get_filter_list(kwargs):
	filters = {
		"disabled": 0,
	}
	for key, val in kwargs.items():
		if val:
			filters.update({key: val})
	return filters


def append_applied_filters(filters, filter_list):
	section_list = filter_list.get("sections")
	filters_list = list(filters.items())  # Convert filters to a list of key-value tuples
	sort_order = None  # Initialize sort_order variable
	for section in section_list:
		doc_name = frappe.db.get_value(
			"Filter Section Setting", {"filter_section_name": section["name"]}, "doctype_name"
		)
		if doc_name == "Item":
			field_val = frappe.db.get_value(
				"Filter Section Setting", {"filter_section_name": section["name"]}, "field"
			)
			filters_list.append((field_val, ["in", section["value"]]))
			if field_val == "sequence":
				# Get the sort order value from the section's value list
				sort_order = section["value"][0]

	filters = dict(filters_list)  # Convert filters_list back to a dictionary
	return filters, sort_order
