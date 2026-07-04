import json
import csv
import re
import sys

# --- Mappings ---
TYPE_MAP = {
    "Grass": "Erba",
    "Fire": "Fuoco",
    "Water": "Acqua",
    "Lightning": "Lampo",
    "Psychic": "Psico",
    "Fighting": "Lotta",
    "Darkness": "Oscurità",
    "Metal": "Metallo",
    "Dragon": "Drago",
    "Colorless": "Incolore",
}

RARITY_MAP = {
    100: "Diamante 1",
    200: "Diamante 2",
    300: "Diamante 3",
    400: "Diamante 4",
    500: "Stella 1",
    600: "Stella 2",
    700: "Stella 2",
    800: "Stella 2",
    830: "Cromatico 1",
    860: "Cromatico 2",
    900: "Corona 1",
}

ADDITIONAL_CATEGORY_MAP = {
    1: "Ultracreatura",
    2: "Tempo Passato",
    3: "Tempo Futuro",
}

HEADER = [
    "cardId", "expansion", "collectionNumber", "name",
    "isEX", "isMega", "additionalCategory", "hp", "type",
    "ability>name", "ability>jname", "ability>desc",
    "attacks>name", "attacks>jname", "attacks>desc",
    "attacks>cost1", "attacks>cost2", "attacks>cost3", "attacks>cost4", "attacks>cost5",
    "attacks>damage+glyph",
    "attacks2>name", "attacks2>jname", "attacks2>desc",
    "attacks2>cost1", "attacks2>cost2", "attacks2>cost3", "attacks2>cost4", "attacks2>cost5",
    "attacks2>damage+glyph",
    "weakness", "retreat", "illustrator", "rarity",
    "flavor", "flavorjp",
    "footer", "typeLabel",
]


def tr_type(eng: str) -> str:
    return TYPE_MAP.get(eng, eng)


def tr_rarity(val: int) -> str:
    return RARITY_MAP.get(val, str(val))


def tr_additional_category(val) -> str:
    if val is None:
        return ""
    return ADDITIONAL_CATEGORY_MAP.get(val, str(val))


def clean_text(text: str) -> str:
    """
    - Sostituisce \\n con uno spazio
    - Traduce i tipi inglesi racchiusi tra \\x04 (es. \\x04Water\\x04) in {{et|TipoItaliano}}
    - Sostituisce Pokémon-\\x03 con Pokémon-''''''<big>ex</big>''''''
    - Rimuove gli spazi multipli
    """
    if not text:
        return text

    # \n → spazio
    text = text.replace("\n", " ")

    # \x04<TipoInglese>\x04 → {{et|<TipoItaliano>}}
    for eng, ita in TYPE_MAP.items():
        text = text.replace("\x04" + eng + "\x04", "{{et|" + ita + "}}")

    # Pokémon-\x03 → Pokémon-''''''<big>ex</big>''''''
    text = text.replace("Pokémon-\x03", "Pokémon-''''''<big>ex</big>''''''")

    # Spazi multipli → spazio singolo
    text = re.sub(r" +", " ", text)

    return text.strip()


def extract_attack(atk):
    """(name, jname, desc, [cost1..cost5], damage+glyph)"""
    if atk is None:
        return ("", "", "", ["", "", "", "", ""], "")

    name = atk.get("name", "")
    desc = clean_text(atk.get("desc", ""))
    costs = [tr_type(c) for c in atk.get("cost", [])]
    while len(costs) < 5:
        costs.append("")

    dmg = atk.get("damage", 0)
    glyph = atk.get("damageSymbolGlyph", "")
    dmg_str = f"{dmg}{glyph}" if dmg or glyph else ""

    return (name, "", desc, costs, dmg_str)


def json_to_txt(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for card in data:
        kind = card.get("kind", "pokemon")

        # ability
        ability = card.get("ability")
        if ability and isinstance(ability, dict):
            aname = ability.get("name", "")
            adesc = clean_text(ability.get("desc", ""))
        else:
            aname, adesc = "", ""

        # attacks
        atks = card.get("attacks", [])
        a1 = extract_attack(atks[0] if len(atks) >= 1 else None)
        a2 = extract_attack(atks[1] if len(atks) >= 2 else None)

        # type
        if kind == "trainer":
            ctype = card.get("typeLabel", "")
        else:
            ctype = tr_type(card.get("type", ""))

        # additionalCategory
        ac = tr_additional_category(card.get("additionalCategory"))

        # flavor: \n → spazio
        flavor = card.get("flavor", "")
        if flavor:
            flavor = flavor.replace("\n", " ")

        # footer e typeLabel
        ui = card.get("ui", {})
        footer = ui.get("footer", "") if isinstance(ui, dict) else ""
        type_label = card.get("typeLabel", "")

        row = [
            card.get("cardId", ""),
            card.get("expansion", ""),
            card.get("collectionNumber", ""),
            card.get("name", ""),
            card.get("isEX", False),
            card.get("isMega", False),
            ac,
            card.get("hp", ""),
            ctype,
            aname,
            "",                     # ability>jname
            adesc,
            a1[0], a1[1], a1[2],   # atk0 name, jname, desc
            a1[3][0], a1[3][1], a1[3][2], a1[3][3], a1[3][4],
            a1[4],                 # atk0 dmg+glyph
            a2[0], a2[1], a2[2],   # atk1 name, jname, desc
            a2[3][0], a2[3][1], a2[3][2], a2[3][3], a2[3][4],
            a2[4],                 # atk1 dmg+glyph
            tr_type(card.get("weakness", "")),
            card.get("retreat", ""),
            card.get("illustrator", ""),
            tr_rarity(card.get("rarity", 0)),
            flavor,
            "",                     # flavorjp
            footer,                 # footer
            type_label,             # typeLabel
        ]
        rows.append(row)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"Fatto: {len(rows)} righe → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python json_to_txt.py <input.json> <output.txt>")
        sys.exit(1)
    json_to_txt(sys.argv[1], sys.argv[2])
