import time

import frappe

from summitapp.api.V2 import V2
from summitapp.api.v2.utilities.utils import error_response, success_response


@frappe.whitelist(allow_guest=True)
def api(**kwargs):
	try:
		st = time.time()
		version = kwargs.get("version")
		# if version == "v1":
		#     api = V1()
		if version == "v2":
			print("version 2", version)
			api = V2()
		response = api.class_map(kwargs)
		et = time.time()
		if type(response) == dict:
			response["exec_time"] = f"{round(et - st, 4)} seconds"
		return response
	except Exception as e:
		frappe.logger("registration").exception(e)
		return error_response(e)
