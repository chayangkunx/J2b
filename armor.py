import os
import json
import shutil
import glob
from jproperties import Properties

optifine = Properties()
i = 0
item_type = ["leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots"]
DEBUG = True


def debug(message: str) -> None:
	if DEBUG:
		print(f"[ARMOR] {message}")

def write_armor(file, gmdl, layer, i):
	if i == 0:
		type = "helmet"
	elif i == 1:
		type = "chestplate"
	elif i == 2:
		type = "leggings"
	elif i == 3:
		type = "boots"
	ajson = {
		"format_version": "1.10.0",
		"minecraft:attachable": {
			"description": {
				"identifier": f"geyser_custom:{gmdl}.player",
				"item": { f"geyser_custom:{gmdl}": "query.owner_identifier == 'minecraft:player'" },
				"materials": {
					"default": "armor_leather",
					"enchanted": "armor_leather_enchanted"
				},
				"textures": {
					"default": f"textures/armor_layer/{layer}",
					"enchanted": "textures/misc/enchanted_item_glint"
				},
				"geometry": {
					"default": f"geometry.player.armor.{type}"
				},
				"scripts": {
					"parent_setup": "variable.helmet_layer_visible = 0.0;"
				},
				"render_controllers": ["controller.render.armor"]
			}
		}
	}
	with open(file, "w") as f:
		f.write(json.dumps(ajson))
	debug(f"Wrote attachable override -> {file}")

while i < 4:
	try:
		debug(f"Processing base item: {item_type[i]}")
		with open(f"assets/minecraft/models/item/{item_type[i]}.json", "r") as f:
			data = json.load(f)
	except:
		i += 1
		continue
	for override in data.get("overrides", []):
		predicate = override.get("predicate", {})
		if "custom_model_data" not in predicate:
			debug("Skip override without custom_model_data")
			continue

		custom_model_data = predicate["custom_model_data"]
		model = override.get("model")
		if not model:
			debug("Skip override without model path")
			continue
		debug(f"Override matched (cmd={custom_model_data}) model={model}")
		namespace = model.split(":")[0]
		item = model.split("/")[-1]
		if item in item_type:
			debug("Skip vanilla model reference")
			continue
		else:
			try:
				path = model.split(":")[1]
				optifine_file = f"{namespace}_{item}"
				debug(f"Loading OptiFine properties {optifine_file}.properties")
				with open(f"assets/minecraft/optifine/cit/ia_generated_armors/{optifine_file}.properties", "rb") as f:
					optifine.load(f)
					if i == 2:
						layer = optifine.get("texture.leather_layer_2").data.split(".")[0]
					else:
						layer = optifine.get("texture.leather_layer_1").data.split(".")[0]
				debug(f"Resolved layer texture={layer}")
				if not os.path.exists("target/rp/textures/armor_layer"):
					os.mkdir("target/rp/textures/armor_layer")
				if not os.path.exists(f"target/rp/textures/armor_layer/{layer}.png"):
					shutil.copy(f"assets/minecraft/optifine/cit/ia_generated_armors/{layer}.png", "target/rp/textures/armor_layer")
					debug(f"Copied layer texture {layer}.png")
				with open(f"assets/{namespace}/models/{path}.json", "r") as f :
					texture = json.load(f)["textures"]["layer1"]
					tpath = texture.split(":")[1]
					try:
						shutil.copy(f"assets/{namespace}/textures/{tpath}.png", f"target/rp/textures/{namespace}/{path}.png")
					except Exception as e:
						print(e)
						debug("Failed to copy texture; see error above")
				afile = glob.glob(f"target/rp/attachables/{namespace}/{path}*.json")
				if not afile:
					debug(f"Attachable template missing for {namespace}:{path}")
					continue
				with open(afile[0], "r") as f:
					da = json.load(f)["minecraft:attachable"]
					gmdl = da["description"]["identifier"].split(":")[1]
				pfile = afile[0].replace(".json", ".player.json")
				write_armor(pfile, gmdl, layer, i)
			except Exception as e:
				print(e)
				print("Item not found of ...")
				debug("Encountered exception; continuing")
				continue
	i += 1
print("[ARMOR] Completed OptiFine armor processing")