import frappe
from frappe.utils import flt

from summitapp.api.v2.order.order_list import get_charges_from_table
from summitapp.api.v2.utilities import get_currency_symbol
from summitapp.api.v2.utilities.utils import error_response, success_response


@frappe.whitelist()
def get_summary(kwargs):
	try:
		id = kwargs.get("id")
		quot_doc = frappe.get_doc("Quotation", id)
		symbol = get_currency_symbol(quot_doc.currency)
		data = {
			"name": "Order Summary",
			"id": id,
			"currency_symbol": symbol,
			"values": get_summary_details(quot_doc),
		}
		return success_response(data=data)
	except Exception as e:
		frappe.logger("order").exception(e)
		return error_response(e)


@frappe.whitelist()
def get_order_id(kwargs):
	try:
		email = frappe.session.user
		session_id = kwargs.get("session_id")
		customer = frappe.get_value("Customer", {"email": email}, "name")
		if customer:
			order_id = frappe.db.get_value("Sales Order", {"customer": customer}, "name")
		else:
			order_id = frappe.db.get_value(
				"Sales Order", {"custom_session_id": session_id}, "name"
			)
		return success_response(data=order_id)
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(e)


def get_summary_details(quot_doc):
	charges = get_charges_from_table(quot_doc)
	tax_amt = charges.get("tax", 0)
	summ_list = [get_summary_list_json("Subtotal Excluding Tax", quot_doc.total)]
	summ_list.append(get_summary_list_json("Tax", tax_amt))
	summ_list.append(get_summary_list_json("Shipping Charges", charges.get("shipping", 0)))
	summ_list.append(
		get_summary_list_json("Assembly Charges", quot_doc.get("total_assembly_charges"))
	)
	summ_list.append(
		get_summary_list_json("Payment Gateway Charges", charges.get("gateway_charge", 0))
	)
	summ_list.append(
		get_summary_list_json("Subtotal Including Tax", quot_doc.total + tax_amt)
	)
	summ_list.append(get_summary_list_json("Coupon Code", quot_doc.coupon_code))
	summ_list.append(get_summary_list_json("Coupon Amount", quot_doc.discount_amount))
	summ_list.append(
		get_summary_list_json("Store Credit", quot_doc.get("store_credit_used"))
	)
	summ_list.append(
		get_summary_list_json("Round Off", quot_doc.get("rounding_adjustment", 0))
	)
	summ_list.append(
		get_summary_list_json(
			"Total",
			quot_doc.get("rounded_total", quot_doc.grand_total)
			- flt(quot_doc.get("store_credit_used", 0)),
		)
	)
	return summ_list


def get_summary_list_json(name, value):
	return {"name": name, "value": value}


def recently_bought(kwargs):
	from summitapp.api.v2.product.product_list import get_detailed_item_list

	try:
		if frappe.session.user == "Guest":
			return error_response("Please login first")
		customer = kwargs.get("customer_id")
		if not customer:
			customer = frappe.db.get_value("Customer", {"email": frappe.session.user}, "name")
		if not customer:
			return error_response("Customer not found")

		orders = frappe.db.get_values("Sales Order", {"customer": customer}, "name", pluck=1)
		items = (
			frappe.db.get_list(
				"Sales Order Item",
				{"parent": ["in", orders]},
				pluck="item_code",
				distinct=1,
				limit_page_length=8,
				ignore_permissions=1,
			)
			or []
		)
		res = []
		res = get_detailed_item_list(items, customer)
		return success_response(data=res)
	except Exception as e:
		frappe.logger("order").exception(e)
		return error_response(e)
