import frappe

from summitapp.api.v2.utilities.currency import convert_currency


def get_price_list(customer=None):
	selling_settings = frappe.get_cached_value("Web Settings", None, "default_price_list")
	if customer:
		cust = frappe.get_cached_value(
			"Customer", customer, ["default_price_list", "customer_group"], as_dict=True
		)
		cust_grp_pl = frappe.get_cached_value(
			"Customer Group", cust.get("customer_group"), "default_price_list"
		)
		return cust.get("default_price_list") or cust_grp_pl or selling_settings
	return selling_settings


def get_item_price(
	currency, item_name, customer_id=None, price_list=None, valuation_rate=0
):
	item_filter = {"item_code": item_name, "price_list": price_list}

	if customer_id:
		item_filter["customer"] = customer_id
		price, mrp_price = frappe.db.get_value(
			"Item Price", item_filter, ["price_list_rate", "strikethrough_rate"]
		) or (0, 0)
		if price:
			return convert_currency(price, currency), convert_currency(mrp_price, currency)

	item_filter["customer"] = ["is", "null"]
	price, mrp_price = frappe.get_value(
		"Item Price", item_filter, ["price_list_rate", "strikethrough_rate"]
	) or (0, 0)
	return convert_currency(price, currency), convert_currency(mrp_price, currency)
