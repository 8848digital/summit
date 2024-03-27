import frappe


def success_response(data=None, id=None):
	response = {"msg": "success"}
	response["data"] = data
	if id:
		response["data"] = {"id": id, "name": id}
	return response


def error_response(err_msg):
	return {"msg": "error", "error": err_msg}


@frappe.whitelist(allow_guest=True)
def download_pdf(
	doctype, name, format=None, doc=None, no_letterhead=0, language=None, letter_head=None
):
	from frappe.utils.print_format import download_pdf

	download_pdf(doctype, name, format=format, doc=doc, no_letterhead=no_letterhead)


def get_pdf_attachments(doctype, doc_name):
	try:
		files = frappe.get_list(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": doc_name},
			fields=["file_url"],
		)
		pdf_files = [file for file in files if file.get("file_url").endswith(".pdf")]
		pdf_urls = [file.get("file_url") for file in pdf_files]
		return pdf_urls
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def autofill_slug(doc, method=None):
	if hasattr(doc, "slug") and not doc.get("slug"):
		doc.slug = frappe.utils.slug(doc.name)


def get_access_level(customer_id=None):
	if customer_id:
		grp = frappe.db.get_value("Customer", customer_id, "customer_group")
		access_level = frappe.db.get_value("Customer Group", grp, "access_level") or 0
		return access_level
	return 0


def get_product_url(item_detail, url_type="product"):
	if not item_detail:
		return "/"
	item_cat = item_detail.get("category")
	item_cat_slug = frappe.db.get_value("Category", item_cat, "slug")
	product_slug = item_detail.get("slug")
	from summitapp.api.v2.mega_menu import get_item_url

	return get_item_url(url_type, item_cat_slug, product_slug)
