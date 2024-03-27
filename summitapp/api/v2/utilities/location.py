import frappe

from summitapp.api.v2.utilities.utils import success_response


def validate_pincode(kwargs):
	pincode = True if frappe.db.exists("Pin Code", kwargs.get("pincode")) else False
	return success_response(data=pincode)


def get_cities(kwargs):
	city_list = frappe.db.get_list(
		"City",
		filters={"state": kwargs.get("state")},
		fields=["name", "state", "country"],
		ignore_permissions=True,
	)
	return success_response(data=city_list)


def get_states(kwargs):
	state_list = frappe.db.get_list(
		"State", filters={}, fields=["name", "country"], ignore_permissions=True
	)
	return success_response(state_list)


def get_countries(kwargs):
	country_list = frappe.db.get_list(
		"Country", filters={}, fields=["name as country_name"], ignore_permissions=True
	)
	return success_response(data=country_list)
