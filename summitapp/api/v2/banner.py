import frappe

from summitapp.api.v2.utilities.fields import get_field_names
from summitapp.api.v2.utilities.utils import error_response, success_response


def button_info(banner):
	btn_list = []
	if banner.get("button_1_title") or banner.get("button_1_url"):
		btn_list.append(
			{"btn_title": banner.get("button_1_title"), "btn_url": banner.get("button_1_url")}
		)

	if banner.get("button_2_title") or banner.get("button_2_url"):
		btn_list.append(
			{"btn_title": banner.get("button_2_title"), "btn_url": banner.get("button_2_url")}
		)

	return btn_list


def get(kwargs):
	try:
		fields = get_field_names("Banner")

		banners = frappe.get_list(
			"Home Banner", filters={"show_on_home_page": 1}, fields=["*"], order_by="sequence"
		)

		if kwargs.get("category"):
			banners = frappe.get_list(
				"Home Banner", filters={"category": kwargs.get("category")}, fields=["*"]
			)

		for banner in banners:
			banner["btn_info"] = button_info(banner)

		# Extracting desired fields after adding button_info
		for banner in banners:
			filtered_banner = {key: value for key, value in banner.items() if key in fields}
			banner.clear()
			banner.update(filtered_banner)

		return success_response(banners)

	except Exception as e:
		frappe.logger("banner").exception(e)
		return error_response(e)
