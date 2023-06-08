from . import __version__ as app_version

app_name = "summit_api"
app_title = "Summit API"
app_publisher = "8848 Digital LLP"
app_description = "Customized APIs for Ecommerce"
app_email = "deepak@8848digital.com"
app_license = "MIT"


# include js in doctype views
doctype_js = {"Sales Order" : "public/js/sales_order.js"}

doc_events = {
	"Quotation": {
		"on_payment_authorized": "summit_api.overrides.quotation.on_payment_authorized",
		"validate": "summit_api.overrides.quotation.validate"
	},
	"Item":{
		"before_save": "summit_api.overrides.item.on_save",
		"validate": "summit_api.overrides.item.validate",
        "on_update": "summit_api.overrides.item.on_update"
	},
	"Customer":{
		"on_update": "summit_api.overrides.customer.on_update",
		"before_save": "summit_api.overrides.customer.on_save",
		"validate": "summit_api.overrides.customer.validate"
	},
    "Contact": {
		"validate": "summit_api.overrides.contact.validate"
	},
	"Customer Group":{
		"validate": "summit_api.overrides.customer_group.validate"
	},
	"Sales Invoice":{
		"on_cancel":"summit_api.overrides.sales_invoice.on_cancel",
		"on_submit": "summit_api.overrides.sales_invoice.on_submit"
	},
	"Sales Order": {
		"on_payment_authorized": "summit_api.overrides.sales_order.on_payment_authorized",
		"on_submit": "summit_api.overrides.sales_order.on_submit"
	},
	"*": {
		"validate": "summit_api.utils.autofill_slug"
	},
	"Address": {
		"before_validate": "summit_api.overrides.address.before_validate"
	}
}


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

jinja = {
    "methods": [
		"summit_api.api.v1.product.check_availability"
	]
}


import summit_api.monkey_patches
# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"summit_api.auth.validate"
# ]

