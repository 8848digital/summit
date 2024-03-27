import frappe


def get_allowed_categories(category_list=None):
	categories = []
	user = frappe.session.user
	if user != "Guest":
		cust = frappe.db.get_value(
			"Customer", {"email": user}, ["name", "customer_group"], as_dict=1
		)
		if cust:
			categories = frappe.db.get_values(
				"Category Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1
			)
			if not categories and cust.get("customer_group"):
				categories = frappe.db.get_values(
					"Category Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1
				)
	if not categories:
		categories = frappe.db.get_values(
			"Category Multiselect", {"parent": "Web Settings"}, "name1", pluck=1
		)
	allowed_categories = []
	for category in categories:
		allowed_categories += get_child_categories(category, True, True)
	filtered_category = []
	if allowed_categories:
		if category_list is None:
			category_list = []
			filtered_category = [
				category for category in allowed_categories if category in category_list
			]
	return filtered_category or (allowed_categories if categories else category_list)


def get_parent_categories(category, is_name=False, excluded=None, name_only=False):
	if excluded is None:
		excluded = []
	filters = category if is_name else {"slug": category}
	print("parent filetr", filters)
	cat = frappe.db.get_value("Category", filters, ["lft", "rgt"], as_dict=1)
	print("parent cat", cat)
	if not (cat and category):
		return []
	excluded_cat = "', '".join(excluded)
	print("exclude cat", excluded_cat)
	parent_categories = frappe.db.sql(
		f"""select name, slug, parent_category from `tabCategory`
		where lft <= %s and rgt >= %s
		and enable_category='Yes' and name not in ('{excluded_cat}')
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	print("parent cat", parent_categories)
	if name_only:
		return [row.name for row in parent_categories] if parent_categories else []
	return parent_categories


def get_child_categories(category, is_name=False, with_parent=False):
	filters = category if is_name else {"slug": category}
	print("2 filters", filters)
	cat = frappe.db.get_value("Category", filters, ["lft", "rgt"], as_dict=1)
	print("3 cat", cat)
	category_list = []
	if not (cat and filters):
		return []
	child_categories = frappe.db.sql(
		"""select name, slug, parent_category from `tabCategory`
		where lft >= %s and rgt <= %s
		and enable_category='Yes'
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	print("child cat", child_categories)
	category_list = [child.name for child in child_categories]
	print("category list", category_list)
	if category_list and with_parent:
		for category in category_list:
			category_list += get_parent_categories(category, True, category_list, True)
	return category_list


def get_category_slug(item_detail):
	if not item_detail:
		return []
	item_cat = item_detail.get("category")
	item_cat_slug = frappe.db.get_value("Category", item_cat, "slug")
	return item_cat_slug
