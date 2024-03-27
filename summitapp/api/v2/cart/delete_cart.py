import frappe

from summitapp.api.v2.product.recommended_products import get_recommendation
from summitapp.api.v2.utilities.user import get_guest_user, get_logged_user
from summitapp.api.v2.utilities.utils import error_response, success_response


@frappe.whitelist(allow_guest=True)
def delete_products(kwargs):
	try:
		email = None
		headers = frappe.request.headers
		if not headers or "Authorization" not in headers:
			return error_response("Please Specify Authorization Token")
		auth_header = headers.get("Authorization")
		if "token" in auth_header:
			email = get_logged_user()
		else:
			email = get_guest_user(auth_header)
		item_code = kwargs.get("item_code")
		quotation_id = kwargs.get("quotation_id")
		owner = frappe.db.get_value("User", {"email": email})
		if not quotation_id:
			quotation_id = frappe.db.exists("Quotation", {"owner": owner, "status": "Draft"})
		if not quotation_id:
			return error_response("Cart not found")
		quot_doc = frappe.get_doc("Quotation", quotation_id)

		params = {"item_only": 1, "item_code": item_code, "ptype": "Mandatory"}
		item_list = []
		recommendations = get_recommendation(params)
		if recommendations:
			for item in recommendations:
				if not item:
					continue
				item_list.append(item)
		else:
			item_list.append(item_code)

		deleted_from_cart = delete_item_from_cart(item_list, quot_doc)
		return success_response(data=deleted_from_cart)
	except Exception as e:
		frappe.logger("cart").exception(e)
		return error_response("error deleting items to cart")


@frappe.whitelist(allow_guest=True)
def clear_cart(kwargs):
	try:
		quotation_id = kwargs.get("quotation_id")
		if not quotation_id:
			return error_response("Quotation Not Found")
		frappe.delete_doc(
			"Quotation", quotation_id, ignore_permissions=True, ignore_missing=True
		)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def delete_item_from_cart(item_list, quot_doc):
	item_deleted = False
	for item in item_list:
		quotation_items = quot_doc.get("items")
		if quotation_items and len(quot_doc.get("items", [])) == 1:
			frappe.delete_doc("Quotation", quot_doc.name, ignore_permissions=True)
			return "Item Deleted"
		elif quotation_items:
			frappe.db.delete("Quotation Item", {"parent": quot_doc.name, "item_code": item})
			quot_doc.reload()
			item_deleted = True
	if item_deleted:
		quot_doc.reload()
		quot_doc.save(ignore_permissions=True)
		return "Item Deleted"
	return f"Following Items: {', '.join(item_list)} do not exist in cart!"
