from typing import List
from deepinesStore.app_info import AppInfo, AppType
from lxml import etree
import locale

# Flathub appstream.xml file location
appstream_file = "/var/lib/flatpak/appstream/flathub/x86_64/active/appstream.xml"

# Flathub app categories
categories = [
		"AudioVideo", "Development", "Education", "Games", "Game", "Productivity",
		"Graphics", "Network", "Office", "Science", "System", "Utility"
	]

# FIXME: HARDCODED!! Remove when this is figured out!
hc_desktop = [
		"app.organicmaps.desktop",
		"chat.delta.desktop", "chat.schildi.desktop",
		"com.bitwarden.desktop", "com.jgraph.drawio.desktop",
		"org.kiwix.desktop", "org.telegram.desktop"]

nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}

def get_preferred_text(element, tag, preferred_lang):
	# Try to find the element with the full preferred xml:lang attribute
	full_lang_xpath = f'{tag}[@xml:lang="{preferred_lang}"]'
	full_lang_elem = element.find(full_lang_xpath, namespaces=nsmap)
	if full_lang_elem is not None:
		return full_lang_elem.text

	# If not found, try to find the element with the base language (e.g., 'en' from 'en_US')
	base_lang = preferred_lang.split('_')[0]
	base_lang_xpath = f'{tag}[@xml:lang="{base_lang}"]'
	base_lang_elem = element.find(base_lang_xpath, namespaces=nsmap)
	if base_lang_elem is not None:
		return base_lang_elem.text

	# If neither is found, try to find the element without xml:lang attribute (default language)
	default_lang_elems = element.findall(tag)
	for elem in default_lang_elems:
		if elem.get(f'{{{nsmap["xml"]}}}lang') is None:
			return elem.text

	# If none of the above is found, return None
	return None

def app_list_flatpak() -> List[AppInfo]:
	# Get the system language
	system_lang = locale.getdefaultlocale()[0]

	# Parse the appstream file with lxml
	tree = etree.parse(appstream_file)
	root = tree.getroot()
	app_list = []

	for component in root.findall('component'):
		if component.get('type') in ['runtime', 'addon']:
			continue

		app_id = component.find('id').text
		og_app_id = app_id
		# If ends with .desktop but is not in hc_desktop remove that last part
		if app_id.endswith(".desktop") and app_id not in hc_desktop:
			app_id = app_id[:-8]

		# Don't include if id has BaseApp
		if "BaseApp" in app_id:
			continue

		app_name = get_preferred_text(component, 'name', system_lang)
		app_summary = get_preferred_text(component, 'summary', system_lang)
		app_version = None
		app_releases = component.find('releases')
		if app_releases is not None:
			releases = app_releases.findall('release')
			if releases:
				app_version = releases[-1].get('version')

		# Get <icon> with attribute type="cached" and type="remote"
		icon_elems = component.findall('icon')
		cached_icons = set()
		cached_icons.add(og_app_id + ".png")
		remote_icons = set()
		for elem in icon_elems:
			icon_type = elem.get('type')
			icon_url = elem.text
			if icon_type == 'cached':
				cached_icons.add(icon_url)
			elif icon_type == 'remote':
				remote_icons.add(icon_url)
		app_icons = {
			'cached': list(cached_icons),
			'remote': list(remote_icons)
		}

		app_category = "other"
		app_categories = component.find('categories')
		if app_categories is not None:
			for category in app_categories.findall('category'):
				if category.text in categories:
					app_category = category.text
					break

		app_info = AppInfo(name=app_name, id=app_id, description=app_summary, version=app_version, category=app_category, type=AppType.FLATPAK_APP, icons=app_icons)
		app_list.append(app_info)

	return app_list