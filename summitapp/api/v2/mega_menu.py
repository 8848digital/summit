import frappe
from summitapp.utils import error_response, success_response, get_allowed_categories, get_parent_categories

# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get(kwargs):
	try:
		filters = {'parent_category':['is','not set']}
		categories = get_allowed_categories()
		if categories:
			filters.update({"name": ["in", categories]})
		category_list = get_item_list('Category', filters)
		category_list = [{'values': get_sub_cat(cat, allowed_categories=categories), **cat} for cat in category_list]
		return success_response(data=category_list)
	except Exception as e:
		frappe.logger('registration').exception(e)
		return error_response(e)


def breadcrums(kwargs):
	try:
		listing_map = {
			"listing": "product-category",
			"brand": "brand",
			"catalog": "catalog"
		}
		product_type = kwargs.get('product_type')
		if product_type not in listing_map.keys():
			return error_response('Please Specify Correct Product Type')
		category = kwargs.get('category')
		if category:
			parent_categories = get_parent_categories(category)
		else:
			parent_categories = []
		product = kwargs.get('product')
		brand = kwargs.get('brand')
		res = []
		url=None
		last_cat = None
		if not brand:
			for cat in parent_categories:
				url = prepare_url(listing_map.get(product_type), cat.slug)
				res.append({
					'name': cat.label or cat.name,
					'link': url
				})
				last_cat = cat.slug
			if product:
				res.append({
					'name': frappe.get_value('Item', {'slug': product}, 'item_name'),
					'link': prepare_url("product", product, prepare_url("product", last_cat))
				})

		else:
			res.append({
				'name': brand.capitalize(),
				'link': get_item_url(listing_map.get(product_type), brand)
			})
			if product:
				res.append({
					'name': frappe.get_value('Item', {'slug': product}, 'item_name'),
					'link': prepare_url("product", product, prepare_url('brand-product', brand))
				})

		return success_response(data=res)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response('error fetching breadcrums url')
	

def get_sub_cat(cat, url=None, allowed_categories = None):
	filters = {'parent_category': cat['name']}
	if allowed_categories:
		filters.update({"name": ["in", allowed_categories]})
	sub_cat_list = get_item_list('Category', filters=filters)
	sub_cat_list = [{
						'url': prepare_url("product-category", sub_cat['slug'], parent = url), 
						'values': get_sub_cat(sub_cat, allowed_categories=allowed_categories), 
						**sub_cat
					} for sub_cat in sub_cat_list]
	return sub_cat_list


def get_item_list(doctype, filters):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list(doctype,
						   filters=filters,
						   fields=['name', 'label', 'sequence as seq', 'slug', 'image'],
						   order_by='sequence', ignore_permissions=ignore_permissions)


def get_item_url(product_type, category=None, product=None):
	url_str = f'/{product_type}'
	if category:
		url_str += f'/{category}'
	if product:
		url_str += f'/{product}'
	return url_str

def prepare_url(prefix, category, parent=None):
	if parent:
		return f"{parent}/{category}"
	else:
		return f"/{prefix}/{category}"
	
@frappe.whitelist(allow_guest=True)
def get_mega_menu(kwargs):
	try:
		category = frappe.get_list("Category",fields=['name', 'label', 'sequence as seq', 'slug', 'image','url'])
		return success_response(category)
	except Exception as e:
		frappe.logger('mega_menu').exception(e)
		return error_response(e)	


@frappe.whitelist(allow_guest=True)
def get_navbar_data(kwargs):
    try:
        user_language = kwargs.get('language')
        parent_categories = frappe.get_all("Category", filters={"is_group": 1}, fields=["category_name", "label","sequence", "slug"],order_by = "sequence")

        navbar_data = []

        for category in parent_categories:
            parent = None
            navbar_item = {
                "name": category.category_name,
                "label": category.label,
                "url": create_url(category.slug, parent),
                "seq": category.sequence,
                "slug": category.slug,
                "navbar_values": []
            }

            child_categories = frappe.get_all("Category", filters={"parent_category": category.category_name}, fields=["category_name", "label", "sequence", "slug"],order_by = "sequence")
            
            for child_category in child_categories:
                child_navbar_item = {
                    "name": child_category.category_name,
                    "label": child_category.label,
                    "url": create_url(child_category.slug,category.slug),
                    "seq": child_category.sequence,
                    "slug": child_category.slug,
                    "navbar_values": []
                }
                navbar_item['navbar_values'].append(child_navbar_item)

            navbar_data.append(navbar_item)
        # translated_data = translate_keys(navbar_data, user_language)
        return success_response(data=navbar_data)
    except Exception as e:
        frappe.logger("Navbar").exception(e)
        return error_response(e)


def create_url(prefix, parent=None):
    if parent:
        return f"/{parent}/{prefix}"
    elif prefix:
        return f"/{prefix}"
    else:
        return ""		