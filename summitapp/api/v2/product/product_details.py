import frappe
from frappe import _

from summitapp.api.v2.filter import get_filter_list
from summitapp.api.v2.product.product_list import get_list_data
from summitapp.api.v2.product.tagged_products import get_tagged_product_limit
from summitapp.api.v2.utilities.user import create_user_tracking
from summitapp.api.v2.utilities.utils import error_response, get_access_level


# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_details(kwargs):
	from summitapp.api.v2.utilities.fields import (get_field_names,
	                                               get_item_field_values)

	try:
		create_user_tracking(kwargs, "Product Detail")
		item_slug = kwargs.get("item")
		currency = kwargs.get("currency")
		if not item_slug:
			return error_response(_("Invalid key 'item'"))
		customer_id = (
			kwargs.get("customer_id")
			or frappe.db.get_value("Customer", {"email": frappe.session.user}, "name")
			if frappe.session.user != "Guest"
			else None
		)
		filters = get_filter_list(
			{"slug": item_slug, "access_level": get_access_level(customer_id)}
		)
		count, item = get_list_data(None, filters, None, None, None, limit=1)
		field_names = get_field_names("Details")
		processed_items = []

		if item:
			item_fields = get_item_field_values(currency, item, customer_id, None, field_names)
			translated_item_fields = {}
			for fieldname, value in item_fields.items():
				translated_item_fields[fieldname] = _(value)
			processed_items.append(translated_item_fields)

		return {"msg": ("Success"), "data": processed_items}

	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(str(e))


def get_detailed_item_list(
	currency, items, customer_id=None, filters=None, product_limit=None
):
	from summitapp.api.v2.utilities.fields import get_processed_list

	if filters is None:
		filters = {}
	access_level = get_access_level(customer_id)
	filter = {"name": ["in", items], "access_level": access_level}
	if filters:
		filter.update(filters)

	if not customer_id:
		customer_id = frappe.db.get_value("Customer", {"email": frappe.session.user}, "name")

	user_role = frappe.session.user
	apply_product_limit = get_tagged_product_limit(user_role, customer_id)
	data = frappe.get_list("Item", filter, "*", ignore_permissions=True)

	if product_limit is not None and apply_product_limit == 1:
		limited_data = []
		for item in data:
			if len(limited_data) >= product_limit:
				break
			limited_data.append(item)
		data = limited_data

	result = get_processed_list(currency, data, customer_id, "product")
	return result
