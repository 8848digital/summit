# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class PageFilterSetting(Document):
	pass

@frappe.whitelist(allow_guest=True)
def update_filters():
	try:
		pages = frappe.get_all('Page Filter Setting')
		results=[]
		for page in pages:
			results.append(update_page(page.name))
		return results
	except Exception as e:
		frappe.logger('filter').exception(e)
		return e

def update_page(page):
	doc = frappe.get_doc('Page Filter Setting',page)
	sections = []
	for i in doc.filter_sections:
		fs = frappe.get_doc('Filter Section Setting',i.filter_section)
		values = []
		template = f"SELECT DISTINCT({fs.field}) AS value FROM `tab{fs.doctype_name}`"
		if fs.static_condition:
			template += " WHERE " + fs.static_condition
		if fs.apply_dynamic_filter and doc.dynamic_field_name:
			if not fs.static_condition:
				template += " WHERE "
			else:
				template += "AND "
			template += f"{doc.dynamic_field_name} = "+ """ "{doc}" """.format(doc=doc.doctype_link)
		data = frappe.db.sql(template,as_dict=1)
		for j in data:
			values.append(j.value)
		values = [i for i in values if i]
		sections.append({
			'section':  i.filter_section,
			'values': values
		})
	result = {
			'doctype': doc.doctype_name,
			'docname': doc.doctype_link,
			'filters': sections
	}
	doc.response_json = json.dumps(result)
	doc.save(ignore_permissions=True)
	return result
	