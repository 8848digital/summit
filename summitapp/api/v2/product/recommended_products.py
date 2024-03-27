import frappe

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_recommendation(kwargs):
	from summitapp.api.v2.product.product_details import get_detailed_item_list

	# ptype = ["Equivalent", "Suggested", "Mandatory", "Alternate"]
	currency = kwargs.get("currency")
	if kwargs.get("item_code"):
		item_code = kwargs.get("item_code")
	elif kwargs.get("item"):
		item_code = frappe.get_value("Item", {"slug": kwargs.get("item")})
	else:
		return error_response("invalid argument 'item'")
	fieldnames = [
		"item_code_1",
		"item_code_2",
		"item_code_3",
		"item_code_4",
		"item_code_5",
		"item_code_6",
		"item_code_7",
		"item_code_8",
		"item_code_9",
		"item_code_10",
		"item_code_11",
		"item_code_12",
		"item_code_13",
		"item_code_14",
		"item_code_15",
		"item_code_16",
		"item_code_17",
		"item_code_18",
		"item_code_19",
		"item_code_20",
	]
	if kwargs.get("ptype") == "Suggested":
		condition = f"item_code_1 = '{item_code}'"
	else:
		condition = " or ".join(
			[
				f'{field} = "{item_code}"'
				for field, item_code in zip(fieldnames, [item_code] * len(fieldnames))
			]
		)
	items = frappe.db.sql(
		f"""select {', '.join(fieldnames)} from `tabMatching Items` where type = '{kwargs.get('ptype','')}' and ({condition})""",
		as_list=True,
	)
	res = []
	if items:
		for item in items:
			for code in item:
				if code and code not in res:
					res.append(code)
		items = res
		if kwargs.get("item_only"):
			return items
		items.remove(item_code)
	else:
		if kwargs.get("item_only"):
			return []
		return error_response("No match found")
	result = get_detailed_item_list(currency, items, kwargs.get("customer_id"))
	return success_response(data=result)
