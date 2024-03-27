import frappe

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_tagged_products(kwargs):
	from summitapp.api.v2.product.product_details import get_detailed_item_list

	try:
		currency = kwargs.get("currency")
		if not kwargs.get("tag"):
			return error_response("key missing 'tag'")

		tag = kwargs.get("tag")
		# Fetching the product limit from Tags MultiSelect
		tag_doc = frappe.get_doc("Tag", tag)
		product_limit = tag_doc.product_limit

		items = frappe.get_list(
			"Tags MultiSelect", {"tag": tag}, pluck="parent", ignore_permissions=True
		)
		customer_id = kwargs.get("customer_id")
		res = get_detailed_item_list(currency, items, customer_id, None, product_limit)
		return success_response(data=res)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_tagged_product_limit(user_role, customer_id):
	if user_role == "Guest":
		web_settings = frappe.get_single("Web Settings")
		if web_settings.apply_product_limit:
			return web_settings.apply_product_limit
	elif customer_id:
		grp = frappe.db.get_value("Customer", customer_id, "customer_group")
		if grp:
			apply_customer_group_limit = frappe.db.get_value(
				"Customer Group", grp, "apply_product_limit"
			)

			if apply_customer_group_limit:
				return apply_customer_group_limit

	return 0
