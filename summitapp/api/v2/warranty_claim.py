import frappe
from summitapp.utils import success_response, error_response
import json
from summitapp.api.v2.utils import get_field_names


@frappe.whitelist()
def create_warranty_claim(kwargs):
    try:
        if frappe.request.data:
            request_data = json.loads(frappe.request.data)
            if not request_data.get('item_code'): 
                return error_response('Please Specify Item Code')
            if not request_data.get('email'): 
                return error_response('Please Specify email')
            if not request_data.get('name'): 
                return error_response('Please Specify name')

            cr_doc = frappe.new_doc('Customer Reviews')
            cr_doc.name1 = request_data.get('name')
            cr_doc.email = request_data.get('email')
            cr_doc.comment = request_data.get('comment')
            cr_doc.item_code = request_data.get('item_code')
            cr_doc.item_name = request_data.get('item_name')
            cr_doc.rating = request_data.get('rating')
            cr_doc.verified = request_data.get('verified')
            cr_doc.date = datetime.now()
            images = request_data.get("images")
            for i in images:
                image = i.get('image')
                cr_doc.append(
                    "review_image",
                    {
                        "doctype": "Return Replacement Image",
                        "image":image
                    },
                )
            cr_doc.save(ignore_permissions=True)  
            return success_response(data={'docname': cr_doc.name, 'doctype': cr_doc.doctype})
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))



def get_warranty_claim(kwargs):
    try:
        filed_names = get_field_names("Warranty Claim")
        warranty_claim = frappe.get_list("Warranty Claim", fields=filed_names) 
        if "item_code" in kwargs:
            item_code = kwargs["item_code"]
            if item_code:
                warranty_claim = frappe.get_list("Warranty Claim", filters={"item_code": item_code}, fields=filed_names)
        return warranty_claim
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))
