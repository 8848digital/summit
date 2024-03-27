import frappe

from summitapp.api.v2.stock import get_stock_info
from summitapp.api.v2.utilities.utils import error_response, success_response


def get_variant_size(item_code):
	return frappe.get_value(
		"Item Variant Attribute",
		{"parent": item_code, "attribute": "Size"},
		"attribute_value",
	)


def get_variant_colour(item_code):
	colour = frappe.get_value(
		"Item Variant Attribute",
		{"parent": item_code, "attribute": "Colour"},
		"attribute_value",
	)
	return frappe.get_value("Item Attribute Value", {"attribute_value": colour}, "abbr")


def get_variant_slug(item_code):
	return frappe.get_value("Item", {"item_code": item_code}, "slug")


def get_variant_info(variant_list):
	from summitapp.api.v2.utilities import get_slide_images

	return [
		{
			"variant_code": item.name,
			"slug": get_variant_slug(item.name),
			"size": get_variant_size(item.name),
			"colour": get_variant_colour(item.name),
			"stock": True if get_stock_info(item.name, "stock_qty") != 0 else False,
			"image": get_slide_images(item.name, False),
		}
		for item in variant_list
	]


# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_variants(kwargs):
	try:
		slug = kwargs.get("item")
		item_code = frappe.get_value("Item", {"slug": slug})
		filters = {"item_code": item_code}
		variant_list = get_variant_details(filters)
		variant_info = get_variant_info(variant_list)
		default_size = get_default_variant(item_code, "size")
		default_colour = get_default_variant(item_code, "colour")
		size = list({var.get("size") for var in variant_info if var.get("size")})
		sorted_size = frappe.get_all(
			"Item Attribute Value",
			{"attribute_value": ["in", size], "parent": "Size"},
			pluck="attribute_value",
			order_by="idx asc",
		)
		colour = list({var.get("colour") for var in variant_info if var.get("colour")})
		stock_len = len([var.get("stock") for var in variant_info if var.get("stock")])
		attributes = []
		if size:
			attributes.append(
				{
					"field_name": "size",
					"label": "Select Size",
					"values": sorted_size,
					"default_value": default_size,
					"display_thumbnail": variant_thumbnail_reqd(item_code, "size"),
				}
			)
		if colour:
			attributes.append(
				{
					"field_name": "colour",
					"label": "Select Colour",
					"values": colour,
					"default_value": default_colour,
					"display_thumbnail": variant_thumbnail_reqd(item_code, "colour"),
				}
			)
		attr_dict = {
			"item_code": item_code,
			"variants": get_variant_info(variant_list),
			"attributes": attributes,
		}
		return success_response(data=attr_dict)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_default_variant(item_code, attribute):
	attr = frappe.get_value(
		"Item Variant Attribute",
		{"variant_of": item_code, "is_default": 1, "attribute": attribute},
		"attribute_value",
	)
	return frappe.get_value("Item Attribute Value", {"attribute_value": attr}, "abbr")


def variant_thumbnail_reqd(item_code, attribute):
	res = frappe.get_value(
		"Item Variant Attribute",
		{"parent": item_code, "display_thumbnail": 1, "attribute": attribute},
		"name",
	)
	return bool(res)


def get_variant_details(item_code):
	if not item_code:
		return []
	item = frappe.db.get_all(
		"Item", filters={"variant_of": item_code}, fields=["name as item_code"]
	)
	for i in item:
		item_doc = frappe.get_doc("Item", i)
		i["attr"] = {}
		for attr in item_doc.attributes:
			if attr.attribute == "Category":
				attr_abbr = frappe.db.get_value(
					"Item Attribute Value",
					{"parent": attr.attribute, "attribute_value": attr.attribute_value},
					"abbr",
				)
			else:
				attr_abbr = attr.attribute_value
			i["attr"][attr.attribute] = attr_abbr
		for key, val in i["attr"].items():
			i[key] = val
	return item
