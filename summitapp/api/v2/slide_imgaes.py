import frappe


def get_slide_images(item, tile_image):
	img = None if tile_image else []
	imgs = get_slideshow_value(item)
	if imgs:
		if slideshow := imgs.get("slideshow"):
			ss_doc = frappe.get_all(
				"Website Slideshow Item", {"parent": slideshow}, "*", order_by="idx asc"
			)
			ss_images = [image.image for image in ss_doc]
			if ss_images:
				img = ss_images[0] if tile_image else ss_images
				return img
		if imgs.get("website_image"):
			img = imgs.get("website_image") if tile_image else [imgs.get("website_image")]
	return img


def get_default_slide_images(item_doc, tile_image, attribute):
	if images := get_slide_images(item_doc.name, tile_image):
		return images

	if item_doc.get("has_variant") and (
		variant := frappe.get_value(
			"Item Variant Attribute",
			{"variant_of": item_doc.name, "is_default": 1, "attribute": attribute},
			"parent",
		)
	):
		return get_slide_images(variant, tile_image)

	return None if tile_image else []


def get_slideshow_value(item_name):
	return frappe.get_value(
		"Website Item", {"item_code": item_name}, ["slideshow", "website_image"], as_dict=True
	)
