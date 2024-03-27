import contextlib
from datetime import datetime, timedelta

import frappe
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from webshop.webshop.shopping_cart.cart import _get_cart_quotation

from summitapp.api.v2.utilities.utils import error_response, success_response


def place_order(kwargs):
	try:
		frappe.set_user("Administrator")
		party_name = kwargs.get("party_name")
		common_comment = kwargs.get("common_comment")
		payment_date = kwargs.get("payment_date")
		order_id = kwargs.get("order_id")
		billing_address_id = kwargs.get("billing_address_id")
		shipping_address_id = kwargs.get("shipping_address_id")
		transporter = kwargs.get("transporter")
		transport_charges = kwargs.get("transport_charges")
		door_delivery = kwargs.get("door_delivery")
		godown_delivery = kwargs.get("godown_delivery")
		location = kwargs.get("location")
		remarks = kwargs.get("remarks")
		if not order_id:
			quotation = _get_cart_quotation()
		else:
			quotation = frappe.get_doc("Quotation", order_id)
		quotation.common_comment = common_comment
		quotation.transporter = transporter
		quotation.door_delivery = door_delivery
		quotation.godown_delivery = godown_delivery
		quotation.location = location
		quotation.remarks = remarks
		quotation.transport_charges = transport_charges
		quotation.party_name = party_name
		order = submit_quotation(
			quotation, billing_address_id, shipping_address_id, payment_date, None
		)
		return order
	except Exception as e:
		frappe.logger("order").exception(e)
		return error_response(f"Cart Does Not Exists /{e}")


def submit_quotation(
	quot_doc, billing_address_id, shipping_address_id, payment_date, company_gstin
):
	print("quote doc", quot_doc)
	quot_doc.customer_address = billing_address_id
	quot_doc.shipping_address_name = shipping_address_id
	quot_doc.payment_schedule = []
	quot_doc.save()
	quot_doc.submit()
	return create_sales_order(quot_doc, payment_date, company_gstin)


def create_sales_order(quot_doc, payment_date, company_gstin):
	print("quotation create so", quot_doc)
	so_doc = make_sales_order(quot_doc.name)
	if payment_date:
		payment_date = datetime.strptime(payment_date, "%d/%m/%Y").strftime("%Y-%m-%d")
		so_doc.delivery_date = datetime.strptime(payment_date, "%Y-%m-%d")
	else:
		transaction_date = datetime.strptime(so_doc.transaction_date, "%Y-%m-%d")
		so_doc.delivery_date = (transaction_date + timedelta(days=7)).date()
	so_doc.company_gstin = company_gstin
	so_doc.custom_session_id = quot_doc.session_id
	so_doc.payment_schedule = []

	so_doc.flags.ignore_permissions = True
	so_doc.save()

	return confirm_order(so_doc)


def confirm_order(so_doc):
	print("sodoc", so_doc)
	with contextlib.suppress(Exception):
		so_doc.flags.ignore_permissions = True
		so_doc.payment_schedule = []
		so_doc.save()
	return so_doc.name


def razorpay_place_order(
	order_id=None,
	party_name=None,
	common_comment=None,
	payment_date=None,
	billing_address_id=None,
	shipping_address_id=None,
	transporter=None,
	transport_charges=None,
	door_delivery=None,
	godown_delivery=None,
	location=None,
	remarks=None,
	company_gstin=None,
):
	try:
		frappe.set_user("Administrator")
		if not order_id:
			quotation = _get_cart_quotation()
		else:
			quotation = frappe.get_doc("Quotation", order_id)

		quotation.common_comment = common_comment
		quotation.transporter = transporter
		quotation.door_delivery = door_delivery
		quotation.godown_delivery = godown_delivery
		quotation.location = location
		quotation.remarks = remarks
		quotation.transport_charges = transport_charges
		quotation.party_name = party_name
		order = submit_quotation(
			quotation, billing_address_id, shipping_address_id, payment_date, company_gstin
		)
		return order
	except Exception as e:
		frappe.logger("order").exception(e)
		return error_response(f"Cart Does Not Exists /{e}")


# Whitelisted Function
@frappe.whitelist()
def get_razorpay_payment_url(kwargs):
	try:
		email = frappe.session.user
		kwargs["full_name"], kwargs["email"] = frappe.db.get_value(
			"User", email, ["full_name", "email"]
		) or [None, None]
		# Returns Checkout Url Of Razorpay for payments
		payment_details = get_payment_details(kwargs)
		doc = frappe.get_doc("Razorpay Settings")
		return doc.get_payment_url(**payment_details)
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(e)


def get_payment_details(kwargs):
	return {
		"amount": kwargs.get("amount"),
		"title": f"Payment For {kwargs.get('order_id')}",
		"description": f"Payment For {kwargs.get('order_id')}",
		"payer_name": kwargs.get("full_name"),
		"payer_email": kwargs.get("email"),
		"reference_doctype": kwargs.get("document_type"),
		"reference_docname": kwargs.get("order_id"),
		"order_id": kwargs.get("order_id"),
		"currency": "INR",
		"redirect_to": "failed",
	}
