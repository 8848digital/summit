import frappe

from summitapp.api.v2.product.product_list import get_list
from summitapp.api.v2.utilities.utils import error_response, success_response


# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_cyu_categories(kwargs):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list(
		"CYU Categories",
		filters={},
		fields=[
			"name as product_category",
			"heading",
			"label",
			"image as product_img",
			"slug",
			"url as category_url",
			"description",
			"offer",
			"range_start_from",
		],
		order_by="sequence",
		ignore_permissions=ignore_permissions,
	)


@frappe.whitelist(allow_guest=True)
def get_categories(kwargs):
	filters = {"enable_category": "Yes"}
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list(
		"Category",
		filters=filters,
		fields=["name as category", "image", "slug", "url as category_url", "description"],
		ignore_permissions=ignore_perm,
	)


def get_top_categories(kwargs):
	categories = get_cyu_categories(kwargs)
	limit = int(kwargs.get("limit", 3))
	if limit and len(categories) > limit:
		categories = categories[:limit]
	res = []
	for category in categories:
		data = {
			"container": {
				"container_name": category.get("product_category"),
				"slug": category.get("slug"),
				"banner_img": category.get("product_img"),
				"banner_description": category.get("description"),
			}
		}
		kwargs["category"] = category.get("slug")
		kwargs["internal"] = 1
		kwargs["limit"] = 8
		p_list = get_list(kwargs)
		data["product_list"] = p_list
		res.append(data)
	return success_response(res)
