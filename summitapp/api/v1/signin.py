import frappe
from summitapp.utils import check_user_exists,success_response,error_response, resync_cart


def signin(kwargs):
	try:
		if kwargs.get('usr') == frappe.session.user: return success_response(data='Already Logged In')
		if kwargs.get('via_google'):
			return login_via_google(kwargs)
		if not check_user_exists(kwargs.get('usr')):
			return error_response('No account with this Email id')
		temp_session = frappe.session.user
		login_manager = frappe.auth.LoginManager()
		
		if kwargs.get('with_otp'):
			# Validate OTP
			from summitapp.api.v1.otp import verify_otp
			if verify_otp({"email":kwargs.get('usr'), "otp":kwargs.get('pwd')}).get('msg') != 'success':
				return error_response('Invalid OTP')
			else:
				return login_via_otp(kwargs.get('usr'))
		else:
			login_manager.authenticate(user=kwargs.get('usr'),pwd=kwargs.get('pwd'))
			login_manager.post_login()
			if frappe.response['message'] == 'Logged In':
				synced = resync_cart(temp_session)
				frappe.response["data"] = {"is_synced": synced,"message":"Logged In"}
			else:
				return error_response("Email or Password is incorrect")
	except frappe.exceptions.AuthenticationError as e:
		frappe.logger("registration").exception(e)
		return error_response(e)


def signin_as_guest(kwargs):
	try:
		"""
			Store guest user id, Create User with given params
			Login User and Transfer Quotation Items From Guest Cart to User Cart 
		"""
		from summitapp.api.v1.registration import create_user, create_customer, create_address
		temp_user = frappe.session.user
		temp_session = frappe.session.sid
		if not check_user_exists(kwargs.get('email')): 
			create_user(kwargs)
			customer_doc = create_customer(kwargs)
		else:
			customer_doc = frappe.get_doc('Customer', {'email': kwargs.get('email')})
		frappe.local.login_manager.login_as(kwargs.get('email'))
		address_doc = create_address(kwargs,customer_doc.name)
		address_doc.save(ignore_permissions=True)
		resync_cart(temp_user)
		return success_response(data={"address_id":address_doc.name, "customer_id":customer_doc.name})
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response(e)


def get_user_profile(kwargs):
	roles = frappe.get_roles(frappe.session.user)
	is_superadmin = "Administrator" in roles
	is_dealer = "Dealer" in roles
	return success_response(data = {
									"is_superadmin": is_superadmin,
									"is_dealer": is_dealer
								})

def login_via_google(kwargs):
	if check_user_exists(kwargs.get('usr', kwargs.get("email"))):
		return login_without_password(kwargs.get('usr', kwargs.get("email")))
	else:
		from summitapp.api.v1.registration import customer_signup
		return customer_signup(kwargs)

def login_via_otp(email):
	return login_without_password(email)

def login_without_password(email):
	frappe.local.login_manager.login_as(email)
	roles = frappe.get_roles(frappe.session.user)
	is_superadmin = "Administrator" in roles
	is_dealer = "Dealer" in roles
	return success_response(data = {
									"is_superadmin": is_superadmin,
									"is_dealer": is_dealer
								})

def get_redirecting_urls(kwargs):
	return frappe.get_all("Redirect URLs",fields=["from", "to"])