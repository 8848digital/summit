import frappe
from frappe.utils import getdate

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_quotation_details(customer, token):
	or_filter = {"session_id": token}
	if customer:
		or_filter["party_name"] = customer
	quotations = frappe.get_list(
		"Quotation", filters={"status": "Draft"}, or_filters=or_filter, fields="*"
	)
	grand_total = 0
	item_fields = []
	grand_total_excluding_tax = 0
	result = {}
	for quot in quotations:
		quot_doc = frappe.get_doc("Quotation", quot["name"])
		grand_total = quot_doc.rounded_total or quot_doc.grand_total
		grand_total_excluding_tax = quot_doc.total
		from summitapp.api.v2.cart.cart_list import get_processed_cart

		item_fields = get_processed_cart(quot_doc)
		result = {
			"party_name": quot_doc.party_name,
			"name": quot_doc.name,
			"total_qty": quot_doc.total_qty,
			"transaction_date": quot_doc.transaction_date,
			"categories": item_fields,
			"grand_total_including_tax": grand_total,
			"grand_total_excluding_tax": grand_total_excluding_tax,
		}
	return result


def request_for_quotation(kwargs):
	quot_id = kwargs.get("quotation_id")
	if not quot_id:
		return error_response("Quotation id is required")
	doc = frappe.get_doc("Quotation", quot_id)
	new_doc = frappe.get_doc(doc.as_dict().copy()).insert(ignore_permissions=1)
	doc.send_quotation = 1
	doc.flags.ignore_permissions = 1
	doc.submit()
	return success_response(
		data={
			"quotation_id": new_doc.name,
			"print_url": get_pdf_link("Quotation", new_doc.name),
		}
	)


def get_quotation_history(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	customer = kwargs.get("customer_id")
	if not customer:
		customer = frappe.db.get_value("Customer", {"email": frappe.session.user})
	if not customer:
		return error_response("Please login as a customer")
	send_quotation = kwargs.get("only_requested", 1)
	filters = {"party_name": customer, "docstatus": 1}
	quotations = frappe.get_list(
		"Quotation",
		filters=filters,
		fields=["name", "modified", "total_qty", "rounded_total", "grand_total"],
	)
	if quotations:
		quotations = [
			{
				"name": row.name,
				"enquiry_date": getdate(row.modified),
				"total_qty": row.total_qty,
				"grand_total": row.get("rounded_total") or row.grand_total,
				"print_url": get_pdf_link("Quotation", row.name),
			}
			for row in quotations
		]
	return success_response(data=quotations)


def get_pdf_link(voucher_type, voucher_no, print_format=None):
	if not print_format:
		print_format = frappe.db.get_value(
			"Property Setter",
			dict(property="default_print_format", doc_type=voucher_type),
			"value",
		)
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}"
	return "#"
