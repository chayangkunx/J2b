import os
import json
import glob
from crossbow_util import Crossbow_Util


# ----------------------------------------------------
# อ่าน overrides ของ crossbow.json
# ----------------------------------------------------
if os.path.exists("assets/minecraft/models/item/crossbow.json"):
    with open("assets/minecraft/models/item/crossbow.json") as f:
        data = json.load(f)
        predicate = [d["predicate"] for d in data["overrides"]]
        model = [d["model"] for d in data["overrides"]]

    for m, p in zip(model, predicate):

        # ข้าม model vanilla
        if m in [
            "item/crossbow_standby",
            "item/crossbow_pulling_0",
            "item/crossbow_pulling_1",
            "item/crossbow_pulling_2",
            "item/crossbow_arrow",
            "item/crossbow_firework"
        ] or "custom_model_data" not in p:
            continue

        # ----------------------------------------------------
        # Mapping stage ใหม่ (ถูกต้อง 100% ตาม override)
        # ----------------------------------------------------
        i = 0  # default stage

        # pulling stages
        if p.get("pulling") == 1:
            pull = p.get("pull", 0)
            if pull == 0:
                i = 1  # pulling_0
            elif pull == 0.58:
                i = 2  # pulling_1
            else:
                i = 3  # pulling_2

        # charged stage
        elif p.get("charged") == 1 and not p.get("firework"):
            i = 4

        # charged + firework stage
        elif p.get("charged") == 1 and p.get("firework") == 1:
            i = 5

        # ----------------------------------------------------
        # เก็บไฟล์แคช
        # ----------------------------------------------------
        fpath = f"cache/crossbow/{p['custom_model_data']}.json"
        if not os.path.exists(fpath):
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w") as f:
                f.write("{}")

        with open(fpath, "r") as f:
            data = json.load(f)

        with open(fpath, "w") as f:
            data["check"] = data.get("check", 0) + 1
            data[f"texture_{i}"] = m
            json.dump(data, f, indent=2)


# ----------------------------------------------------
# Build final attachables
# ----------------------------------------------------
files = glob.glob("cache/crossbow/*.json")
Crossbow_Util.animation()
Crossbow_Util.rendercontrollers()

gmdllist = []

for file in files:
    try:
        with open(file, "r") as f:
            data = json.load(f)

        # ต้องมีครบ 6 stage
        if data.get("check", 0) < 6:
            continue

        # ----------------------------------------------------
        # เติม missing texture_i ให้ครบ 6 อัน
        # ----------------------------------------------------
        for i in range(6):
            if f"texture_{i}" not in data:
                # fallback ใช้ texture เดิมของเฟรมก่อนหน้า
                if i > 0 and f"texture_{i-1}" in data:
                    data[f"texture_{i}"] = data[f"texture_{i-1}"]
                else:
                    data[f"texture_{i}"] = data.get("texture_0")

        textures = []
        geometry = []

        for i in range(6):
            namespace = data[f"texture_{i}"].split(":")[0]
            path = data[f"texture_{i}"].split(":")[1]

            # find attachable
            files2 = glob.glob(f"target/rp/attachables/{namespace}/{path}*.json")
            for fa in files2:
                if f"{path.split('/')[-1]}." in fa:
                    break

            with open(fa, "r") as f:
                dataA = json.load(f)

            # textures
            textures.append(
                dataA["minecraft:attachable"]["description"]["textures"]["default"]
            )

            # geometry
            model_path = glob.glob(f"target/rp/models/blocks/{namespace}/{path}.json")[0]
            is2Dc = Crossbow_Util.is2Dcrossbow(model_path)

            if is2Dc:
                geometry.append(f"geometry.crossbow_stage_{i}")
            else:
                geometry.append(
                    dataA["minecraft:attachable"]["description"]["geometry"]["default"]
                )

            # Stage 0: copy base info
            if i == 0:
                mfile = fa
                mdefault = dataA["minecraft:attachable"]["description"]["materials"]["default"]
                menchanted = dataA["minecraft:attachable"]["description"]["materials"]["enchanted"]
                gmdl = dataA["minecraft:attachable"]["description"]["identifier"].split(":")[1]

                animations = dataA["minecraft:attachable"]["description"]["animations"]

                gmdllist.append(f"geyser_custom:{gmdl}")
                Crossbow_Util.item_texture(gmdl, textures[0])
            else:
                os.remove(fa)

        # ----------------------------------------------------
        # เขียน attachable สุดท้าย
        # ----------------------------------------------------
        Crossbow_Util.write(
            mfile,
            gmdl,
            textures,
            geometry,
            mdefault,
            menchanted,
            animations,
            animate=[
                {"thirdperson_main_hand": "v.main_hand && !c.is_first_person"},
                {"thirdperson_off_hand": "v.off_hand && !c.is_first_person"},
                {"thirdperson_head": "v.head && !c.is_first_person"},
                {"firstperson_main_hand": "v.main_hand && c.is_first_person"},
                {"firstperson_off_hand": "v.off_hand && c.is_first_person"},
                {"firstperson_head": "c.is_first_person && v.head"}
            ],
            pre_animation=[
                "v.main_hand = c.item_slot == 'main_hand';",
                "v.off_hand = c.item_slot == 'off_hand';",
                "v.head = c.item_slot == 'head';",
                "v.charge_amount = math.clamp((q.main_hand_item_max_duration - (q.main_hand_item_use_duration - q.frame_alpha + 1.0)) / 10.0, 0.0, 1.0f);",
                "v.total_frames = 3;",
                "v.step = v.total_frames / 60;",
                "v.frame = query.is_using_item && v.main_hand ? math.clamp((v.frame ?? 0) + v.step, 1, v.total_frames) : 0;",
                "v.frame = query.item_is_charged && !query.is_item_name_any('slot.weapon.offhand', 0, 'minecraft:firework_rocket') ? 4 : v.frame;",
                "v.frame = query.item_is_charged && query.is_item_name_any('slot.weapon.offhand', 0, 'minecraft:firework_rocket') ? 5 : v.frame;"
            ]
        )

    except Exception as e:
        print("ERROR:", e)

Crossbow_Util.acontroller(gmdllist)
