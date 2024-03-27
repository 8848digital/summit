import frappe


def get_currency(currency):
	if currency is None:
		currency = "INR"
	currency_doc = frappe.get_doc("Currency", currency)
	return currency_doc.get("currency_name", currency)


def get_currency_symbol(currency):
	if currency is None:
		currency = "INR"
	currency_doc = frappe.get_doc("Currency", currency)
	return currency_doc.get("symbol", currency)


def convert_currency(amount, currency):
	if currency and currency != "INR":
		exchange_rate = get_exchange_rate(currency)
		if exchange_rate is not None:
			amount = round(amount * exchange_rate, 2)
	return amount


def get_exchange_rate(currency):
	filters = {"to_currency": currency, "from_currency": "INR"}
	exchange_rate_doc = frappe.get_list(
		"Currency Exchange", filters=filters, fields=["exchange_rate"]
	)
	if exchange_rate_doc:
		exchange_rate = exchange_rate_doc[0].exchange_rate
		return exchange_rate
	else:
		return None


def get_default_currency(kwargs):
	ecom_settings = frappe.get_single("Webshop Settings")
	company_name = ecom_settings.company
	default_currency = frappe.get_value("Company", company_name, "default_currency")
	if not default_currency:
		frappe.throw(f"Default currency not set for company '{company_name}'.")
	return {"default_currency": default_currency, "company": company_name}
