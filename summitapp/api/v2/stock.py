import frappe
from frappe.utils import add_days, cint, flt, nowdate, today
from webshop.webshop.utils.product import adjust_qty_for_expired_items

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_stock_info(item_code, key, with_future_stock=True):
	try:
		roles = frappe.get_roles(frappe.session.user)
		is_dealer = "Dealer" in roles
		warehouse_field = "dealer_warehouse" if is_dealer else "website_warehouse"
		variant_list = frappe.db.get_all("Item", {"variant_of": item_code}, "name")
		if not variant_list:
			variant_list = frappe.db.get_all("Item", {"name": item_code}, "name")
		stock = 0
		for variant in variant_list:
			stock_qty = get_web_item_qty_in_stock(variant.get("name"), warehouse_field).get(key)
			stock += flt(stock_qty)
			if with_future_stock:
				future_stock = get_web_item_future_stock(variant.get("name"), warehouse_field)
				stock += flt(future_stock)
		if key == "stock_qty":
			return stock
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	try:
		stock_qty = 0
		template_item_code = frappe.db.get_value("Item", item_code, ["variant_of"])
		if not warehouse:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": item_code}, item_warehouse_field
			)
		if not warehouse and template_item_code and template_item_code != item_code:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": template_item_code}, item_warehouse_field
			)
		if warehouse:
			stock_qty = frappe.db.sql(
				"""
				select sum(quantity)
				from `tabItem Future Availability`
				where date >= CURDATE() and item=%s and warehouse=%s""",
				(item_code, warehouse),
			)
			if stock_qty:
				return stock_qty[0][0]
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_web_item_qty_in_stock(item_code, item_warehouse_field, warehouse=None):
	try:
		in_stock, stock_qty = 0, ""
		total_qty = 0
		template_item_code, is_stock_item = frappe.db.get_value(
			"Item", item_code, ["variant_of", "is_stock_item"]
		)
		default_warehouse = frappe.get_cached_value("Web Settings", None, "default_warehouse")
		warehouses = [default_warehouse] if default_warehouse else []
		if not warehouse:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": item_code}, item_warehouse_field
			)

		if not warehouse and template_item_code and template_item_code != item_code:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": template_item_code}, item_warehouse_field
			)
		if warehouse:
			warehouses.append(warehouse)
			stock_list = frappe.db.sql(
				f"""
				select GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1),
				S.warehouse
				from tabBin S
				inner join `tabItem` I on S.item_code = I.Item_code
				left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
				where S.item_code='{item_code}' and S.warehouse in ('{"', '".join(warehouses)}')"""
			)
			if stock_list:
				for stock_qty in stock_list:
					stock_qty = adjust_qty_for_expired_items(item_code, [stock_qty], stock_qty[1])
					total_qty += stock_qty[0][0]
					if not in_stock:
						in_stock = stock_qty[0][0] > 0 and 1 or 0
		return frappe._dict(
			{"in_stock": in_stock, "stock_qty": total_qty, "is_stock_item": is_stock_item}
		)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def check_availability(kwargs):
	try:
		item_code = kwargs.get("item_code")
		if not item_code:
			return error_response("item_code missing")

		req_qty = flt(kwargs.get("qty", 1))

		stock_qty = flt(get_stock_info(item_code, "stock_qty", with_future_stock=False))

		qty = min(req_qty, stock_qty)

		template_item_code, lead_days = frappe.db.get_value(
			"Item", item_code, ["variant_of", "lead_time_days"]
		)

		warehouse = frappe.db.get_value(
			"Website Item", {"item_code": item_code}, "website_warehouse"
		)

		if not warehouse and template_item_code and template_item_code != item_code:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": template_item_code}, "website_warehouse"
			)

		future_stock = frappe.get_list(
			"Item Future Availability",
			{"item": item_code, "date": [">", frappe.utils.today()], "quantity": [">", 0]},
			"warehouse, date, quantity",
			order_by="date",
			ignore_permissions=True,
		)

		res = []
		data = {
			"warehouse": warehouse,
			"qty": qty,
			"date": today(),
			"incoming_qty": 0,
			"incoming_date": "",
		}

		if req_qty <= stock_qty:
			return success_response(data=[data])

		req_qty -= stock_qty

		for row in future_stock:
			if req_qty <= 0:
				break

			qty = min(req_qty, row.get("quantity"))
			req_qty -= qty

			if row.get("warehouse") == data["warehouse"] and not data["incoming_qty"]:
				data.update({"incoming_qty": qty, "incoming_date": row.get("date")})
			else:
				res.append(
					{
						"warehouse": row.get("warehouse"),
						"incoming_qty": qty,
						"incoming_date": row.get("date"),
					}
				)
			res = [data] + res

			if req_qty > 0:
				res[-1].update(
					{"additional_qty": req_qty, "available_on": add_days(row.get("date"), lead_days)}
				)
			return success_response(data=res)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)
