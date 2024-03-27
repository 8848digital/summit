import frappe
from frappe.utils import random_string
from frappe.utils.password import check_password

from summitapp.api.v2.utilities.user import create_temp_user
from summitapp.api.v2.utilities.utils import error_response, success_response


# Manualy generated access token
def get_access_token(kwargs):
	try:
		usr = kwargs.get("usr")
		pwd = kwargs.get("pwd")
		result = retrieve_api_token(usr, pwd)
		return success_response(data=result)
	except Exception as e:
		frappe.logger("token").exception(e)
		return error_response(str(e))


def retrieve_api_token(usr, pwd):
	try:
		check_password(usr, pwd)
	except Exception as e:
		return e
	doc = frappe.get_doc("User", {"name": usr})
	api_key = doc.api_key
	api_secret = doc.get_password("api_secret")
	if api_key and api_secret:
		api_token = f"token {api_key}:{api_secret}"
		full_name = doc.full_name
		result = {"access_token": api_token, "full_name": full_name}
		return result


# Dynamic Generated Access token
def login(kwargs):
	try:
		usr = kwargs.get("usr")
		pwd = kwargs.get("pwd")
		login_manager = frappe.auth.LoginManager()
		login_manager.authenticate(user=usr, pwd=pwd)
		login_manager.post_login()
	except frappe.exceptions.AuthenticationError:
		frappe.clear_messages()
		frappe.local.response["message"] = {
			"success_key": 0,
			"message": "Authentication Error!",
		}

		return

	api_generate = generate_keys(frappe.session.user)
	user = frappe.get_doc("User", frappe.session.user)

	frappe.response["message"] = {
		"success_key": 1,
		"message": "Authentication success",
		"sid": frappe.session.sid,
		"api_key": user.api_key,
		"api_secret": api_generate,
		"api_token": "token " + user.api_key + ":" + api_generate,
		"username": user.username,
		"email": user.email,
	}


def generate_keys(user_id):
	user = frappe.get_doc("User", user_id)
	if not user:
		return "User not found."
	api_key = frappe.generate_hash(length=15)
	api_secret = frappe.generate_hash(length=15)
	user.api_key = api_key
	user.api_secret = api_secret
	user.save(ignore_permissions=True)
	return api_secret


def auth(kwargs):
	login_manager = frappe.auth.LoginManager()
	login_manager.authenticate(user=kwargs.get("usr"), pwd=kwargs.get("pwd"))
	login_manager.post_login()
	return get_access_token(kwargs)


def get_token(email):
	doc = frappe.get_doc("User", {"email": email})
	api_key = doc.api_key
	api_secret = doc.get_password("api_secret")
	if api_key and api_secret:
		api_token = "token " + api_key + ":" + api_secret
		access_api_token = api_token

	return access_api_token


def get_token_with_mobile(mobile):
	try:
		doc = frappe.get_doc("User", {"mobile_no": mobile})
		if doc:
			api_key = doc.api_key
			api_secret = doc.get_password("api_secret")

			if api_key and api_secret:
				api_token = "token " + api_key + ":" + api_secret
				result = {"access_token": api_token, "full_name": doc.full_name}
				return success_response(result)
			else:
				# Handle the case where either api_key or api_secret is not found
				return error_response("API key or API secret not found")
	except Exception as e:
		frappe.logger("token").exception(e)
		return error_response(e)


def create_access_token(kwargs):
	try:
		token = random_string(20)
		email = create_temp_user(kwargs)
		access = frappe.get_doc(
			{"doctype": "Access Token", "token": token, "email": email}
		).insert()
		return access.token, access.email
	except Exception as e:
		frappe.logger("cart").exception(e)
		return error_response(e)
