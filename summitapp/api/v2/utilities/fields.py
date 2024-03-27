import frappe

from summitapp.api.v2.category import get_category_slug
from summitapp.api.v2.price_list import get_item_price, get_price_list
from summitapp.api.v2.product.product_list import get_product_url
from summitapp.api.v2.product.product_specifictaions import (
    get_features, get_specifications)
from summitapp.api.v2.slide_imgaes import get_default_slide_images
from summitapp.api.v2.stock import get_stock_info
from summitapp.api.v2.utilities.currency import (get_currency,
                                                 get_currency_symbol)
from summitapp.api.v2.utilities.utils import (error_response,
                                              get_pdf_attachments)
from summitapp.api.v2.variant import get_variant_details


def get_field_names(product_type):
	return frappe.db.get_all(
		"Product Fields",
		filters={
			"parent": frappe.get_value("Product Page Field", {"product_type": product_type})
		},
		pluck="field",
	)


def get_processed_list(currency, items, customer_id, url_type="product"):
	field_names = get_field_names("List")
	processed_items = []
	for item in items:
		item_fields = get_item_field_values(
			currency, item, customer_id, url_type, field_names
		)
		print("ITEM Fields", item_fields)
		processed_items.append(item_fields)
	return processed_items


def get_item_field_values(currency, item, customer_id, url_type, field_names):
	computed_fields = {
		"image_url": lambda: {"image_url": get_default_slide_images(item, True, "size")},
		"status": lambda: {"status": "template" if item.get("has_variants") else "published"},
		"in_stock_status": lambda: {
			"in_stock_status": True
			if get_stock_info(item.get("name"), "stock_qty") != 0
			else False
		},
		"brand_img": lambda: {
			"brand_img": frappe.get_value("Brand", item.get("brand"), ["image"]) or None
		},
		"mrp_price": lambda: {
			"mrp_price": get_item_price(
				currency, item.get("name"), customer_id, get_price_list(customer_id)
			)[1]
		},
		"price": lambda: {
			"price": get_item_price(
				currency, item.get("name"), customer_id, get_price_list(customer_id)
			)[0]
		},
		"currency": lambda: {"currency": get_currency(currency)},
		"currency_symbol": lambda: {"currency_symbol": get_currency_symbol(currency)},
		"display_tag": lambda: {
			"display_tag": item.get("display_tag")
			or frappe.get_list(
				"Tags MultiSelect", {"parent": item.name}, pluck="tag", ignore_permissions=True
			)
		},
		"url": lambda: {"url": get_product_url(item, url_type)},
		"category_slug": lambda: {"category_slug": get_category_slug(item)},
		"variant": lambda: {"variant": get_variant_details(item.get("variant_of"))},
		"variant_of": lambda: {"variant_of": item.get("variant_of")},
		"equivalent": lambda: {"equivalent": bool(item.get("equivalent") == "1")},
		"alternate": lambda: {"alternate": bool(item.get("alternate") == "1")},
		"mandatory": lambda: {"mandatory": bool(item.get("mandatory") == "1")},
		"suggested": lambda: {"suggested": bool(item.get("suggested") == "1")},
		"e_commerce_platforms": lambda: {
			"e_commerce_platforms": get_ecommerce_platforms(item)
		},
		"brand_video_url": lambda: {
			"brand_video_url": frappe.get_value("Brand", item.get("brand"), ["brand_video_link"])
			or None
		},
		"size_chart": lambda: {
			"size_chart": frappe.get_value("Size Chart", item.get("size_chart"), "chart")
		},
		"slide_img": lambda: {"slide_img": get_default_slide_images(item, False, "size")},
		"features": lambda: {
			"features": get_features(item.key_features) if item.key_features else []
		},
		"why_to_buy": lambda: {
			"why_to_buy": frappe.db.get_value(
				"Why To Buy", item.get("select_why_to_buy"), "name1"
			)
		},
		"prod_specifications": lambda: {"prod_specifications": get_specifications(item)},
		"item_pdf_url": lambda: {
			"item_pdf_url": get_pdf_attachments("Item", item.get("name"))
		},
		"store_pick_up_available": lambda: {
			"store_pick_up_available": item.get("store_pick_up_available") == "Yes"
		},
		"home_delivery_available": lambda: {
			"home_delivery_available": item.get("home_delivery_available") == "Yes"
		},
	}
	item_fields = {}
	for field_name in field_names:
		if field_name in computed_fields.keys():
			item_fields.update(computed_fields.get(field_name)())
		else:
			item_fields.update({field_name: item.get(field_name)})
	return item_fields


def get_ecommerce_platforms(item):
	try:
		platforms = frappe.get_all(
			"E Commerce Platforms",
			filters={"parent": item.name},
			fields=["platform", "link", "sequence"],
			order_by="sequence",
		)
		return platforms  # Adjusted indentation here
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)
