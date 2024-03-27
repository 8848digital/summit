import frappe


def make_payment_entry(sales_order):
	invoice = frappe.db.get_value("Sales Invoice", {"sales_order": sales_order}, "name")
	if invoice:
		dt = "Sales Invoice"
		dn = invoice
	else:
		dt = "Sales Order"
		dn = sales_order
	from erpnext.accounts.doctype.payment_entry.payment_entry import \
	    get_payment_entry
	from frappe.utils import getdate

	payment_entry_doc = get_payment_entry(dt, dn)
	payment_entry_doc.reference_no = sales_order
	payment_entry_doc.reference_date = getdate()
	payment_entry_doc.save(ignore_permissions=True)
	payment_entry_doc.submit()
