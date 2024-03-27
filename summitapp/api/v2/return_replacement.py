import json
from datetime import datetime

import frappe
from dateutil.relativedelta import relativedelta

from summitapp.api.v2.utilities.user import get_logged_user
from summitapp.api.v2.utilities.utils import error_response, success_response


@frappe.whitelist()
def return_replace_item(kwargs):
	try:
		email = get_logged_user()
		customer = frappe.get_list("Customer", filters={"email": email})
		if frappe.request.data:
			request_data = json.loads(frappe.request.data)
			if not request_data.get("order_id"):
				return error_response("Please Specify Order ID")
			if not request_data.get("product_id"):
				return error_response("Please Specify Product ID")

			rr_doc = frappe.new_doc("Return Replacement Request")
			rr_doc.type = kwargs.get("type")
			rr_doc.reason = kwargs.get("reason")
			rr_doc.order_id = request_data.get("order_id")
			rr_doc.product_id = request_data.get("product_id")
			rr_doc.customer = (
				customer[0].name if customer else None
			)  # Accessing the first customer if exists
			rr_doc.date = datetime.now()
			rr_doc.customer_email = email
			images = request_data.get("images", [])
			for i in images:
				image = i.get("image")
				rr_doc.append(
					"return_replacement_image",
					{"doctype": "Return Replacement Image", "image": image},
				)
			rr_doc.save(ignore_permissions=True)
			return success_response(data={"docname": rr_doc.name, "doctype": rr_doc.doctype})
	except Exception as e:
		frappe.logger("rr").exception(e)
		return error_response(str(e))


def get_return_date(item, transaction_date):
	return_days = frappe.db.get_value("Item", item, "return_days")
	if return_days:
		return_date = (transaction_date + relativedelta(days=return_days)).strftime(
			"%d-%m-%Y"
		)
		return return_date
