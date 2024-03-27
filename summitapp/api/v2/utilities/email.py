import frappe


def send_mail(template_name, recipients, context):
	frappe.sendmail(
		recipients=recipients,
		subject=frappe.render_template(
			frappe.db.get_value("Email Template", template_name, "subject"),
			context,
		),
		cc="",
		bcc="",
		delayed=False,
		message=frappe.render_template(
			frappe.db.get_value("Email Template", template_name, "response"),
			context,
		),
		reference_doctype="",
		reference_name="",
		attachments="",
		print_letterhead=False,
	)
	return "Email Sent"
