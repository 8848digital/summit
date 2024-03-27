import frappe

from summitapp.api.v2.utilities.utils import error_response, success_response


def get_features(key_feature):
	key_features = frappe.get_all(
		"Key Feature Detail", {"parent": key_feature}, pluck="key_feature", order_by="idx"
	)
	feat_val = frappe.get_all(
		"Key Feature",
		{"key_feature": ["in", key_features]},
		["key_feature as heading", "description", "image"],
		order_by="idx",
	)
	return {"name": "Key Features", "values": feat_val}


def get_technologies_details(item):
	techs = frappe.get_list(
		"Final Technology",
		{"parent": item.technologies},
		pluck="technology",
		ignore_permissions=True,
		order_by="idx",
	)
	lst = []
	for row in techs:
		name = frappe.db.get_value("Technology", row, "name")
		image = frappe.db.get_value("Technology", row, "image")
		description = frappe.db.get_value("Technology", row, "description")
		tech_details = {}
		tech_details["name"] = name
		tech_details["image"] = image
		tech_details["description"] = description
		technology_details = []

		tech_details_rows = frappe.get_all(
			"Technology Details",
			filters={"parent": name},
			fields=["title", "video_frame", "description", "image", "sequence"],
			order_by="idx ASC",
		)

		for tech_details_row in tech_details_rows:
			details = {}
			details["title"] = tech_details_row.title
			details["video_frame"] = tech_details_row.video_frame
			details["description"] = tech_details_row.description
			details["image"] = tech_details_row.image
			details["sequence"] = tech_details_row.sequence
			technology_details.append(details)

		tech_details["technology_details"] = technology_details
		lst.append(tech_details)
	return lst


def get_specifications(item):
	res = []
	item_filters = frappe.get_all(
		"Item Filters", {"parent": item.name}, ["field_name", "field_value"], order_by="idx"
	)
	if item_filters:
		res.append(
			{
				"name": "Specifications",
				"values": get_specification_details(item_filters) if item_filters else [],
			}
		)
	if item.get("geometry_file"):
		res.append({"name": "Geometry", "values": item.get("geometry_file")})
	if item.get("technologies"):
		res.append(
			{
				"name": "Technologies",
				"values": item.get("technologies"),
				"details": get_technologies_details(item),
			}
		)
	return res


def get_specification_details(filters):
	return [{"name": tech.field_name, "values": tech.field_value} for tech in filters]


def get_product_specifications(kwargs):
	try:
		prod_specifications = frappe.get_all(
			"Specifications Name",
			filters={"parent": kwargs.get("name")},
			fields=["name1"],
			order_by="idx",
		)
		result = []

		for spec in prod_specifications:
			item_specs = frappe.get_all(
				"Item Specifications", filters={"name": spec.get("name1")}, fields=["name", "name1"]
			)

			spec_values = []
			for item_spec in item_specs:
				spec_details = frappe.get_all(
					"Item Specifications Details",
					filters={"parent": item_spec.get("name")},
					fields=["item_specifications_value"],
					order_by="idx",
				)

				item_values = []
				for spec_detail in spec_details:
					spec_value = frappe.get_all(
						"Item Specifications Value",
						filters={"name": spec_detail.get("item_specifications_value")},
						fields=["name_value"],
					)
					value_details = frappe.get_all(
						"Item Specifications Value Details",
						filters={"parent": spec_detail.get("item_specifications_value")},
						fields=["value"],
						order_by="idx",
					)

					value_list = []
					for value_detail in value_details:
						for value in spec_value:
							value_list.append({"value": value_detail.get("value")})

					item_values.append({"name": value.get("name_value"), "values": value_list})

				spec_values.append({"name": item_spec.get("name1"), "values": item_values})

			result.extend(spec_values)

		return success_response(data=result)
	except Exception as e:
		frappe.logger("utils").exception(e)
		# Assuming error_response is a function that creates an error response
		return error_response(str(e))
