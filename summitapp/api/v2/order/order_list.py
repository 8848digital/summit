from datetime import datetime

import frappe

from summitapp.api.v2.customer_address import get_address
from summitapp.api.v2.order.order_details import get_pdf_link
from summitapp.api.v2.product.product_list import get_product_url
from summitapp.api.v2.return_replacement import get_return_date
from summitapp.api.v2.utilities.currency import (get_currency,
                                                 get_currency_symbol)
from summitapp.api.v2.utilities.fields import get_field_names
from summitapp.api.v2.utilities.utils import error_response, success_response


@frappe.whitelist()
def get_list(kwargs):
	try:
		order_id = kwargs.get("order_id")
		date_range = kwargs.get("date_range")
		is_cancelled = kwargs.get("is_cancelled")
		session_id = kwargs.get("session_id")
		email = frappe.session.user
		customer = frappe.get_value("Customer", {"email": email})
		result, order_count = get_listing_details(
			customer, order_id, date_range, is_cancelled, session_id
		)
		return {"msg": "success", "data": result, "order_count": order_count}
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_listing_details(customer, order_id, date_range, is_cancelled, session_id):
	filters = []
	if customer:
		filters.append(["Sales Order", "customer", "=", customer])
	if order_id:
		filters.append(["Sales Order", "name", "=", order_id])
	if is_cancelled:
		filters.append(["Sales Order", "status", "=", "Cancelled"])
	if date_range:
		filters = get_date_range_filter(filters, date_range)
	if session_id:
		filters.append(["Sales Order", "custom_session_id", "=", session_id])

	orders = frappe.get_all("Sales Order", filters=filters, fields="*")
	charges_fields = get_processed_order(orders, customer)
	return charges_fields, len(charges_fields)


def get_date_range_filter(filters, date_range):
	if date_range == "past_3_months":
		filters.append(["Sales Order", "transaction_date", "Timespan", "last quarter"])
	elif date_range == "last_30_days":
		filters.append(["Sales Order", "transaction_date", "Timespan", "last month"])
	elif date_range == "last_6_months":
		filters.append(["Sales Order", "transaction_date", "Timespan", "last 6 months"])
	elif date_range == "2022":
		filters.append(["Sales Order", "transaction_date", "fiscal year", "2022-2023"])
	elif date_range == "2021":
		filters.append(["Sales Order", "transaction_date", "fiscal year", "2021-2022"])
	elif date_range == "2020":
		filters.append(["Sales Order", "transaction_date", "fiscal year", "2020-2021"])
	elif date_range:
		filters.append(
			["Sales Order", "transaction_date", "Timespan", date_range.replace("_", " ")]
		)
	return filters


def get_processed_order(orders, customer):
	order_data = []
	for order in orders:
		tax_table = frappe.get_all(
			"Sales Taxes and Charges", filters={"parent": order.name}, fields=["*"]
		)
		try:
			sales_invoice = frappe.get_doc("Sales Invoice", filters={"sales_order": order.name})
			print_url = (
				get_pdf_link("Sales Invoice", sales_invoice.name) if sales_invoice else ""
			)
		except frappe.DoesNotExistError as e:
			print(f"Sales Invoice not found for order {order.name}: {e}")
			print_url = ""

		charges = get_charges_from_table(tax_table)
		computed_fields = {
			"tax": lambda charges=charges: {"tax": charges.get("tax", 0)},
			"shipping": lambda charges=charges: {"shipping": charges.get("shipping", 0)},
			"gateway_charge": lambda charges=charges: {
				"gateway_charges": charges.get("gateway_charge", 0)
			},
			"subtotal_include_tax": lambda order=order, charges=charges: {
				"subtotal_include_tax": order.total + charges.get("tax", 0)
			},
			"subtotal_exclude_tax": lambda order=order: {"subtotal_exclude_tax": order.total},
			"total": lambda order=order: {
				"total": order.rounded_total - order.store_credit_used
			},
			"creation": lambda order=order: {"creation": get_creation_date_time(order.creation)},
			"order_details": lambda order=order: {
				"order_details": get_product_details(order.name)
			},
			"payment_status": lambda order=order: {"payment_status": order.workflow_state},
			"coupon_code": lambda order=order: {"coupon_code": order.coupon_code},
			"coupon_amount": lambda order=order: {"coupon_amount": order.discount_amount},
			"currency": lambda order=order: {"currency": get_currency(order.currency)},
			"currency_symbol": lambda order=order: {
				"currency_symbol": get_currency_symbol(order.currency)
			},
			"addresses": lambda order=order: {
				"addresses": get_address(
					customer, order.customer_address, order.shipping_address_name
				)
			},
			"shipping_method": lambda order=order: {
				"shipping_method": {
					"transporter": order.transporter,
					"transport_charges": order.transport_charges,
					"door_delivery": order.door_delivery,
					"godown_delivery": order.godown_delivery,
					"location": order.location,
					"remarks": order.remarks,
				}
			},
			"outstanding_amount": lambda order=order: {
				"outstanding_amount": frappe.db.get_value(
					"Return Replacement Request", {"new_order_id": order.name}, "outstanding_amount"
				)
				or 0
			},
			"print_url": lambda print_url=print_url: {"print_url": print_url},
		}

		charges_fields = {}
		for field_name, compute_func in computed_fields.items():
			charges_fields.update(compute_func())

		order_data.append(charges_fields)

	return order_data


# Define the missing functions (get_pdf_link, get_charges_from_table, get_creation_date_time, get_product_details,
# get_currency, get_currency_symbol, get_address) as per your implementation.


def get_charges_from_table(doc, table=None):
	if table is None:
		table = []
	charges = {}
	for row in doc.get("taxes", table):
		if row.description == "Payment Gateway Charges":
			charges["gateway_charge"] = row.get("tax_amount", 0)
		elif "Shipping" in row.description:
			charges["shipping"] = row.get("tax_amount", 0)
		elif "Assembly" in row.description:
			charges["assembly"] = row.get("tax_amount", 0)
		elif "CGST" in row.description:
			charges["cgst"] = charges.get("cgst", 0) + row.get("tax_amount", 0)
		elif "SGST" in row.description:
			charges["sgst"] = charges.get("sgst", 0) + row.get("tax_amount", 0)
		elif "IGST" in row.description:
			charges["igst"] = charges.get("igst", 0) + row.get("tax_amount", 0)
		else:
			charges["others"] = charges.get("others", 0) + row.get("tax_amount", 0)
		charges["total"] = charges.get("total", 0) + row.get("tax_amount", 0)
	charges["tax"] = (
		charges.get("total", 0)
		- charges.get("gateway_charge", 0)
		- charges.get("shipping", 0)
		- charges.get("assembly", 0)
	)
	return charges


def get_creation_date_time(order):
	quot_doc = frappe.get_doc("Sales Order", order)
	if quot_doc:
		creation = str(quot_doc.creation)
		creation_datetime = datetime.strptime(creation, "%Y-%m-%d %H:%M:%S.%f")
		formatted_date = creation_datetime.strftime("%d-%m-%Y")
		formatted_time = creation_datetime.strftime("%I:%M %p")
		formatted_date_time = formatted_date + " " + formatted_time
		return formatted_date_time


def get_product_details(order):
	quot_doc = frappe.get_doc("Sales Order", order)
	return [
		get_item_details(item.item_code, item, quot_doc.transaction_date)
		for item in quot_doc.items
	]


def get_item_details(item_code, item_row, transaction_date):
	from summitapp.api.v2.slide_imgaes import get_slide_images

	item = frappe.get_value("Item", item_code, "*")
	return {
		"name": item.name,
		"item_name": item.item_name,
		"img": get_slide_images(item.name, True),
		"brand": item.get("brand"),
		"brand_img": frappe.get_value("Brand", {"name": item.get("brand")}, "image"),
		"prod_info": get_item_info(item, item_row),
		"product_url": get_product_url(item),
		"return_date": get_return_date(item.name, transaction_date),
	}


def get_item_info(item, item_row):
	from summitapp.api.v2.cart.cart_list import get_item_details as item_details

	l1 = item_details(item, item_row)
	l1.append({"name": "Quantity", "value": item_row.qty})
	return l1
