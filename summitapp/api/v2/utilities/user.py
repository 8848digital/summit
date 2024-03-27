import frappe
import requests
from frappe.utils import get_url, random_string

from summitapp.api.v2.utilities.utils import error_response, success_response


def check_user_exists(email):
	"""
	Check if a user with the provied Email. exists
	"""
	return frappe.db.exists("User", email)


def check_user_exists_mobile(mobile):
	"""
	Check if a user with the provied mobile number.
	"""
	print(
		"111",
		frappe.db.get_list(
			"User",
			filters={"mobile_no": mobile},
			fields=["email", "new_password", "api_key", "api_secret"],
		),
	)
	return frappe.db.get_list(
		"User",
		filters={"mobile_no": mobile},
		fields=["email", "new_password", "api_key", "api_secret"],
	)


def create_temp_user(kwargs):
	try:
		frappe.local.login_manager.login_as("Administrator")
		username = random_string(8)
		usr = frappe.get_doc(
			{
				"doctype": "User",
				"email": username + "@random.com",
				"first_name": "TGuest",
				"send_welcome_email": 0,
				"language": kwargs.get("language_code"),
			}
		).insert()
		usr.add_roles("Customer")
		# frappe.local.login_manager.login_as(usr.email)
		return usr.email
	except Exception as e:
		frappe.logger("cart").exception(e)
		return error_response(e)


def sync_contact(old_id, new_id):
	frappe.local.login_manager.login_as("Administrator")
	if temp := frappe.db.exists("Contact", {"user": old_id}):
		frappe.delete_doc("Contact", temp)
	contact = frappe.get_doc("Contact", {"email_id": new_id})
	contact.user = new_id
	contact.save()


@frappe.whitelist()
def sync_guest_user(email):
	if "random" in frappe.session.user:
		temp = frappe.session.user
		frappe.rename_doc("User", frappe.session.user, email)
		sync_contact(temp, email)
		frappe.local.login_manager.login_as(email)
	else:
		return


def check_guest_user(email=frappe.session.user):
	return "random" in email


def create_user_tracking(kwargs, page):
	if frappe.session.user == "Guest":
		return
	doc = frappe.new_doc("User Tracking")
	doc.user = frappe.session.user
	doc.page = page
	doc.ip_address = frappe.local.request_ip
	for key, value in kwargs.items():
		if key in ["version", "method", "entity", "cmd"]:
			continue
		doc.append("parameters", {"key": key, "value": value})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def get_logged_user():
	header = {"Authorization": frappe.request.headers.get("Authorization")}
	response = requests.post(
		get_url() + "/api/method/frappe.auth.get_logged_user", headers=header
	)
	user = response.json().get("message")
	return user


def get_customer_id(kwargs):
	customer_id = kwargs.get("customer_id")

	if not customer_id and frappe.request.headers:
		email = get_logged_user()
		customer_id = frappe.db.get_value("Customer", {"email": email}, "name")
	return customer_id


def get_guest_user(auth_header):
	guest_user = frappe.db.get_value("Access Token", {"token": auth_header}, "email")
	if guest_user:
		return guest_user
