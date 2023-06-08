from frappe.auth import CookieManager
from summit_api.overrides.auth import set_cookie

from erpnext.selling.doctype.customer.customer import Customer
from summit_api.overrides.customer import _create_primary_contact, _create_primary_address

CookieManager.set_cookie = set_cookie

Customer.create_primary_contact = _create_primary_contact
Customer.create_primary_address = _create_primary_address