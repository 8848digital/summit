import frappe


def get_list_product_limit(user_role, customer_id):
	if user_role == "Guest":
		web_settings = frappe.get_single("Web Settings")
		if web_settings.product_limit is not None and web_settings.apply_product_limit == 1:
			return web_settings.product_limit
	elif customer_id:
		grp = frappe.db.get_value("Customer", customer_id, "customer_group")
		if grp:
			customer_group_limit = frappe.db.get_value("Customer Group", grp, "product_limit")
			apply_customer_group_limit = frappe.db.get_value(
				"Customer Group", grp, "apply_product_limit"
			)

			if customer_group_limit is not None and apply_customer_group_limit == 1:
				return customer_group_limit
	return 0
