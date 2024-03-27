import frappe

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_contact_us(kwargs):
	try:
		contact_us = frappe.get_doc("Contact Us")
		result = {
			"sales_email_id": contact_us.sales_email_id,
			"sales_contact_number": contact_us.sales_contact_number,
			"supports_email_id": contact_us.supports_email_id,
			"supports_contact_number": contact_us.supports_contact_number,
		}
		return success_response(result)
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_about_us(kwargs):
	try:
		about_us = frappe.get_doc("About Us")
		result = {"description": about_us.description}
		return success_response(result)
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_home_page(kwargs):
	try:
		home_page = frappe.get_doc("Home Page")
		result = {
			"about_us_summary": home_page.about_us_summary,
			"image": home_page.image,
			"about_us_link": home_page.about_us_link,
			"heading": home_page.heading,
		}
		return success_response(result)
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_marquee(kwargs):
	try:
		marquee = frappe.get_doc("Marquee")
		result = [
			{"heading_1": marquee.heading_1},
			{"heading_2": marquee.heading_2},
			{"heading_3": marquee.heading_3},
			{"heading_4": marquee.heading_4},
			{"heading_5": marquee.heading_5},
			{"heading_6": marquee.heading_6},
			{"heading_7": marquee.heading_7},
			{"heading_8": marquee.heading_8},
			{"heading_9": marquee.heading_9},
			{"heading_10": marquee.heading_10},
		]
		return success_response(result)
	except Exception as e:
		frappe.logger("product").exception(e)
		return error_response(e)


def get_company_motto(kwargs):
	try:
		# Assuming frappe.get_doc() returns a document with the specified fields
		company_motto = frappe.get_doc("Company Motto")
		result = {
			"heading_1": company_motto.heading_1,
			"heading_2": company_motto.heading_2,
			"heading_3": company_motto.heading_3,
			"description_1": company_motto.description_1,
			"description_2": company_motto.description_2,
			"details": get_company_motto_details(company_motto),
		}
		return success_response(result)

	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_company_motto_details(doc):
	try:
		details = frappe.get_all(
			"Company Motto Details",
			filters={"parent": doc},
			fields=["image", "heading", "sequence"],
			order_by="sequence",
		)
		return details
	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_testomonial(kwargs):
	try:
		if not kwargs.get("category"):
			return error_response("Please Specify Category")

		test_doc = frappe.get_list(
			"Testomonial",
			filters={"category": kwargs.get("category")},
			fields=["category", "heading", "description", "name"],
		)

		test_with_details = []
		for t in test_doc:
			details = get_testomonial_details(t["name"])  # Fetch images for each review
			t["details"] = details  # Append images to the review
			test_with_details.append(t)
		response_data = test_with_details
		return success_response(response_data)

	except Exception as e:
		frappe.logger("utils").exception(e)
		return error_response(str(e))


def get_testomonial_details(doc):
	try:
		details = frappe.get_all(
			"Testomonial Details",
			filters={"parent": doc},
			fields=["image", "name1", "comment", "url", "label", "sequence"],
			ignore_permissions=True,
			order_by="sequence",
		)
		return details
	except Exception as e:
		frappe.logger("profile").exception(e)
		return error_response(str(e))
