import frappe
from summitapp.utils import success_response, error_response, send_mail,check_user_exists
import json 
import requests
import random

def send_otp(kwargs):
    try:
        username = kwargs.get('usr')
        if not check_user_exists(username):
            return error_response('No account with this Email id')
        else:
            return generate_otp(username)
    except Exception as e:
        return error_response(e)
    
def send_email_otp(kwargs):
    try:
        username = kwargs.get('email')
        return generate_otp(username)
    except Exception as e:
        return error_response(e)    

def generate_otp(username, otp=None):
    """
    Generate OTP For a user
    """
    try:
        if not otp:
            otp_length = 6
            otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
        if not username:
            frappe.throw(frappe._("NOEMAIL"), exc=LookupError)
        key = f"{username}_otp"
        otp_json = {
            "id": key,
            "otp": otp,
            "timestamp": str(frappe.utils.get_datetime().utcnow()),
        }
        rs = frappe.cache()
        rs.set_value(key, json.dumps(otp_json))
        return success_response( data = send_otp_to_email(username, otp) )
    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}

def send_otp_to_email(username, otp):
    # Params For Send Mail- template_name, recipients(list), context(dict) 
    return send_mail("Send OTP", [username], {'otp': otp})

def verify_otp(kwargs):
    try:
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        if email:
            key = f"{email}_otp"
        if phone:
            key = f"+{phone}_otp"
        otp = kwargs.get("otp")
        rs = frappe.cache()
        stored_otp = rs.get_value(key)
        if not stored_otp:
            msg = "OTP invalid, Please try again!"
            return error_response(msg)
        otp_json = json.loads(stored_otp)
        if str(otp) == otp_json.get("otp"):
            return success_response(data="OTP Verified")
        msg = "OTP invalid, Please try again!!"
        return error_response(msg)
    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}


@frappe.whitelist(allow_guest=True)
def send_twilio_sms(kwargs):
    twilio_details=frappe.get_doc('Twilio Sms Settings')
    account_sid=twilio_details.account_sid
    auth_token=twilio_details.auth_token
    twilio_phone_number=twilio_details.twilio_phone_number
    twilio_api_url=twilio_details.twilio_api_url+f'/{account_sid}/Messages.json'
    phone = (kwargs.get("phone"))
    phone_number = f"+{phone}"
    otp_length = 6
    otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
    key = f"{phone_number}_otp"
    otp_json = {
        "id": key,
        "otp": otp,
        "timestamp": str(frappe.utils.get_datetime().utcnow()),
    }
    rs = frappe.cache()
    rs.set_value(key, json.dumps(otp_json))
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'To': phone_number,
        'From': twilio_phone_number,
        'Body': f'Your Otp is {otp}',
    }
    auth = (account_sid, auth_token)
    response = requests.post(twilio_api_url, headers=headers, data=data, auth=auth)
    if response.status_code == 201:
        # frappe.msgprint(f"SMS sent: {response.json().get('sid')}")
        return success_response("OTP sent on your phone number!")
    else:
        frappe.msgprint(f"Failed to send SMS: {response.status_code}, {response.text}")


def send_pinnacle_sms(kwargs):
    try:
     
        url = "https://api.pinnacle.in/index.php/sms/json"

        payload = json.dumps({
        "sender": "vorinf",
        "message": [
            {
            "number": "919619842421",
            "text": "Dear Customer, Thank you for choosing Vortex Infotech! We appreciate your business. If you have any questions or need further assistance, feel free to contact us. Have a great day!",
            "dlttempid": "1707170229196719185"
            }
        ],
        "messagetype": "TXT"
        })
        headers = {
        'Content-Type': 'application/json',
        'apikey': '982873-eac150-ee9a79-912ce2-ba965a',
        'Cookie': 'PHPSESSID=j8pgh4k3im5972fi722vo3sopg'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}
