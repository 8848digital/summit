import frappe
from frappe.utils.password import check_password
from frappe import auth

# Manualy generated access token
def get_access_token(kwargs):
	usr = kwargs.get("usr")
	pwd = kwargs.get("pwd")
	access_api_token = {}
	try:
		check_password(usr,pwd)
	except Exception as e:
		return e
	doc = frappe.get_doc("User", {'name':usr})
	api_key = doc.api_key
	api_secret = doc.get_password('api_secret')
	if api_key and api_secret:
		api_token = "token "+api_key+":"+api_secret
		access_api_token = {"access_token": api_token}
			
	return access_api_token 

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
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)

    frappe.response["message"] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "api_token" : "token "+user.api_key+":"+api_generate,
        "username":user.username,
        "email":user.email
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