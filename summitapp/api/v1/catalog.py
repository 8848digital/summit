import frappe
from summitapp.utils import success_response,error_response
from summitapp.api.v1.product import get_list as get_item_details


def get(kwargs):
	try:
		catalog_list = frappe.get_list('Catalog', {}, '*', ignore_permissions=1, order_by='sequence')
		result = [{"id": catalog.name, "access_level": catalog.access_level, "name": catalog.name,"slug":catalog.slug,"image":catalog.image,"sequence":catalog.sequence, "product_counts": len(get_item_list(catalog.name)), "url": f"catalog/{catalog.slug}"} for catalog in catalog_list]
		return success_response(data=result)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Catalog Error')
		return error_response(e)

def get_items(kwargs):
	try:
		catalog_slug = kwargs.get('catalog_slug')
		catalog = frappe.db.get_value('Catalog', {'slug': catalog_slug})
		if not catalog:
			return error_response('Catalog Does Not Exist')
		item_list = get_item_list(catalog)
		result = get_item_details({'item': ["in", item_list]}).get('data')
		for item in result:
			item['url'] = f"/catalog-product/{catalog_slug}/{item.get('product_slug')}"
		return success_response(result)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Catalog Error')
		return error_response(e)

def get_item_list(catalog):
	items = frappe.get_list("Item Child",{"parent":catalog,"parenttype":'Catalog'},pluck='item', ignore_permissions=1)
	return items or []