"""Build the "<Pokémon> (GCC Pocket)" pages from a ptcgp-carddump dump.

The pages are written one per file, named after the page title (as
gccp-upload-dir.py expects), and contain the same structure as the ones built
from Bulbapedia: navigation, intro, the card list table, a gallery and the
interwiki links. Everything comes from the game's own data, so no page has to
be downloaded or translated.

No other files are needed: the cards, their release dates (including the promo
ones), the rarities and the types all come from the dump, and the names of the
expansions come from Modulo:GCCPocket/data on the wiki (the same module the
templates use), so a new set only has to be added there.

Examples:
    python gccp-build.py -data:C:\\ptcgp-carddump\\out -out:data\\gccp-itpages

Usage:
    python gccp-build.py [OPTIONS]

Options:
    -data:<path>        the dump's out directory (default: $PTCGP_DATA)
    -out:<path>         where the pages are written (default: data/gccp-itpages)
    -locale:<code>      the language of the cards (default: it_IT)
    -interwiki:<list>   interwiki links to add, comma separated, among en, es, ja
                        (default: en,es)
    -help               show this help text.
"""

import datetime
import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SHARED_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "shared")

WIKI_API = "https://wiki.pokemoncentral.it/api.php"
SETS_MODULE = "Modulo:GCCPocket/data"

PAGE_SUFFIX = " (GCC Pocket)"
GALLERY_SIZE = "x200px"

# tipi del GCC Pocket: nome inglese nei dati -> nome italiano sul wiki
TYPES = {
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
# Pokemon.json usa i tipi come numeri
NUM_TYPE = {1: "Incolore", 2: "Erba", 3: "Fuoco", 4: "Acqua", 5: "Lampo",
            6: "Psico", 7: "Lotta", 8: "Oscurità", 9: "Metallo", 10: "Drago"}
# rarità: codice -> (nome, numero di gemme)
RARITY = {
    100: ("Diamante", 1), 200: ("Diamante", 2), 300: ("Diamante", 3), 400: ("Diamante", 4),
    500: ("Stella", 1), 600: ("Stella", 2), 700: ("Stella", 2), 800: ("Stella", 3),
    830: ("Cromatico", 1), 860: ("Cromatico", 2), 900: ("Corona", None),
}
# caratteri usati dal gioco come spazi o come marcatori di forma
WEIRD_SPACES = {"\u00a0", "\u2007", "\u2009", "\u200a", "\u202f", "\u3000", "\u0011"}
DROP_CHARS = {"\u0012", "\u200b", "\ufeff"}
# nome carta -> pagina della specie, quando il nome non basta (forme speciali)
SPECIES_OVERRIDES = {
    "UltraNecrozma": "Necrozma",
}
# carte con numero negativo: il gioco le numera dopo il totale del set
NEGATIVE_NUMBER_OFFSET = {"SP1": 27}


def clean(text):
    """Ripulisce un testo del gioco (spazi anomali, marcatori di forma)."""
    if not text:
        return ""
    text = text.replace("\n", " ")
    for ch in WEIRD_SPACES:
        text = text.replace(ch, " ")
    for ch in DROP_CHARS:
        text = text.replace(ch, "")
    return re.sub(r" +", " ", text).strip()


def fix_file_name(file_name):
    """Sostituisce i caratteri non validi nei nomi di file (come utils.fix_file_name)."""
    for ch in r'<>:"/\|?*':
        file_name = file_name.replace(ch, "_")
    return file_name


def image_stem(text):
    """Nei nomi dei file delle carte spazi, apostrofi e punti non ci sono."""
    for ch in (" ", "'", "\u2019", "."):
        text = text.replace(ch, "")
    return text


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch_set_names():
    """Codici delle espansioni da Modulo:GCCPocket/data (nome -> codice)."""
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": SETS_MODULE,
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
    })
    request = urllib.request.Request(f"{WIKI_API}?{params}",
                                     headers={"User-Agent": "Pywikibot/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        wikitext = json.load(response)["parse"]["wikitext"]
    block = re.search(r"data\.codes\s*=\s*\{(.*?)\n\}", wikitext, re.S)
    if not block:
        raise ValueError(f"data.codes non trovato in {SETS_MODULE}")
    pairs = re.findall(r"\[\s*['\"](.+?)['\"]\s*\]\s*=\s*['\"]([^'\"]+)['\"]", block.group(1))
    return {code: name for name, code in pairs}


def load_set_names():
    """Nomi delle espansioni da Modulo:GCCPocket/data (senza rete non si carica nulla)."""
    try:
        names = fetch_set_names()
    except Exception as error:
        raise RuntimeError(f"non riesco a leggere {SETS_MODULE} dal wiki: {error}") from error
    print(f"Nomi dei set da {SETS_MODULE} ({len(names)})")
    return names


def load_promo_dates(masterdir, schedules):
    """Data della prima distribuzione di ogni carta promo, dai dati di gioco.

    Le fonti sono i bonus giornalieri (FeedShared*Pack), le buste promo
    distribuite dagli eventi (SoloEventBattleGroup), il negozio (ItemShop) e le
    missioni (ActivityMissions). Si tiene sempre la data più antica.
    """
    dates = {}

    def keep(card_id, date):
        if date and (card_id not in dates or date < dates[card_id]):
            dates[card_id] = date

    def date_of(schedule_id):
        return schedule_date(schedules, schedule_id) if schedule_id else None

    # bonus giornalieri
    for name in ("FeedSharedFreePack.json", "FeedSharedNPCPack.json"):
        for feed in read_json(os.path.join(masterdir, name)):
            date = date_of(feed.get("ScheduleID"))
            for card_id in feed.get("PokemonCardIDs", []):
                keep(card_id, date)

    # buste promo: la data dell'evento che le distribuisce
    label_to_table = {x["PackTableLabelID"]: x["PackTableID"]
                      for x in read_json(os.path.join(masterdir, "PackTableLabelMaster.json"))}
    table_to_pack = {x["PackTableID"]: x["PackID"]
                     for x in read_json(os.path.join(masterdir, "PackTableMaster.json"))}
    card_packs = {}
    for entry in read_json(os.path.join(masterdir, "PackTableCardMaster.json")):
        pack = table_to_pack.get(label_to_table.get(entry["PackTableLabelID"]))
        if pack:
            card_packs.setdefault(entry["CardID"], set()).add(pack)
    pack_dates = {}
    for group in read_json(os.path.join(masterdir, "SoloEventBattleGroup.json")):
        pack = group.get("PromotionPackId")
        date = date_of(group.get("ScheduleID"))
        if pack and date:
            pack_dates.setdefault(pack, []).append(date)
    for card_id, packs in card_packs.items():
        for pack in packs:
            for date in pack_dates.get(pack, ()):
                keep(card_id, date)

    # negozio
    contents = {}
    for content in read_json(os.path.join(masterdir, "ItemShopContent.json")):
        if content["ItemID"].startswith(("PK_90", "TR_90")):
            contents.setdefault(content["ItemID"], set()).add(content["ContentID"])
    products = {}
    for product in read_json(os.path.join(masterdir, "ItemShopProduct.json")):
        for content_id in product.get("ContentIDs", []):
            products.setdefault(content_id, []).append(product)
    for card_id, content_ids in contents.items():
        for content_id in content_ids:
            for product in products.get(content_id, ()):
                keep(card_id, date_of(product.get("ScheduleID")))

    # missioni
    groups = {x["ID"]: x for x in read_json(os.path.join(masterdir, "MissionGroups.json"))}
    rewards = {}
    for reward in read_json(os.path.join(masterdir, "MissionReward.json")):
        if reward["ItemID"].startswith(("PK_90", "TR_90")):
            rewards.setdefault(reward["RewardID"], set()).add(reward["ItemID"])
    for mission in read_json(os.path.join(masterdir, "ActivityMissions.json")):
        date = date_of(mission.get("ScheduleID"))
        if not date:
            group = groups.get(mission.get("AffiliationID"))
            date = date_of(group.get("ScheduleID")) if group else None
        if not date:
            continue
        for reward_id in mission.get("RewardIDs", []):
            for card_id in rewards.get(reward_id, ()):
                keep(card_id, date)
    return dates


def schedule_date(schedules, schedule_id):
    """Data (o None) di uno ScheduleID."""
    schedule = schedules.get(schedule_id)
    if schedule and schedule.get("OpenAt") and schedule["OpenAt"][0]:
        return datetime.datetime.fromtimestamp(schedule["OpenAt"][0], datetime.UTC).date()
    return None


class Data:
    """Legge il dump e prepara le informazioni comuni a tutte le pagine."""

    def __init__(self, data_dir, locale):
        self.data_dir = data_dir
        self.set_names = load_set_names()

        # espansioni: nome, data di uscita e numero di carte
        masterdir = os.path.join(data_dir, "masterdata_json")
        schedules = {x["ScheduleID"]: x for x in read_json(os.path.join(masterdir, "Schedule.json"))}
        self.expansion_order = {}
        self.expansion_date = {}
        self.expansion_total = {}
        for index, expansion in enumerate(read_json(os.path.join(masterdir, "Expansion.json"))):
            code = expansion["ExpansionID"]
            self.expansion_order[code] = index
            self.expansion_date[code] = schedule_date(schedules, expansion["DisplayScheduleID"])
            base = expansion["CollectionNumber"]
            self.expansion_total[code] = base if base != "000" else expansion["CollectionOverNumber"]
            if code not in self.set_names:
                print(f"ATTENZIONE: manca il nome del set {code} in {SETS_MODULE}", file=sys.stderr)

        # date delle carte promo
        self.promo_dates = load_promo_dates(masterdir, schedules)

        # tipi delle carte (PokemonTypes è per design, non per stampa)
        self.pokemon = {p["PokemonID"]: p for p in read_json(os.path.join(masterdir, "Pokemon.json"))}

        # carte
        self.cards = []
        for path in sorted(glob.glob(os.path.join(data_dir, "cards", f"*_{locale}.json"))):
            code = os.path.basename(path)[: -len(f"_{locale}.json")].upper()
            code = next((c for c in self.expansion_order if c.lower() == code.lower()), code)
            for card in read_json(path):
                if card.get("kind") != "pokemon":
                    continue
                card["_exp"] = code
                card["_num"] = int(card["collectionNumber"])
                card["_design"] = card["cardId"].split("_")[2]
                card["_name"] = clean(card["name"])
                # nei dati "Nidoran ♀" ha uno spazio che nel titolo non c'è
                for space in (" ", "\u202f"):
                    card["_name"] = (card["_name"].replace(f"Nidoran{space}♀", "Nidoran♀")
                                     .replace(f"Nidoran{space}♂", "Nidoran♂"))
                card["_date"] = self.card_date(card)
                self.cards.append(card)

        # nomi delle specie: ndex -> nome italiano
        self.names = read_json(os.path.join(SHARED_DIR, "poke-names.json"))
        self.ndex_of_name = {x["it"]: x["ndex"] for x in self.names}
        self.name_by_ndex = {x["ndex"]: x for x in self.names}
        # dal nome più lungo al più corto: "Raichu di Alola" deve incontrare
        # "Raichu di Alola" prima di "Raichu"
        self.species_names = sorted(self.ndex_of_name, key=len, reverse=True)

    def card_date(self, card):
        """Data di uscita di una stampa: set o promo."""
        if card["_exp"].startswith("PROMO"):
            return self.promo_dates.get(card["cardId"])
        return self.expansion_date.get(card["_exp"])

    def species_of(self, card):
        """Titolo della pagina (nome italiano della specie) e ndex della carta."""
        name = re.sub(r"-ex$", "", card["_name"])
        name = re.sub(r"^Mega ", "", name)
        for space in (" ", "\u202f"):
            name = name.replace(f"Nidoran{space}♀", "Nidoran♀").replace(f"Nidoran{space}♂", "Nidoran♂")
        name = SPECIES_OVERRIDES.get(name, name)
        if name in self.ndex_of_name:
            return name, self.ndex_of_name[name]
        for species in self.species_names:
            if name.startswith(species + " ") or name.startswith(species + "-"):
                return species, self.ndex_of_name[species]
        return None, None

    def sort_key(self, card):
        """Ordine cronologico: data, poi ordine dell'espansione, poi numero."""
        date = card["_date"] or datetime.date.max
        return (date, self.expansion_order[card["_exp"]], self.display_number(card))

    def display_number(self, card):
        """Numero della stampa, con i negativi del gioco riportati dopo il totale."""
        number = card["_num"]
        if number < 0:
            number = NEGATIVE_NUMBER_OFFSET.get(card["_exp"], 0) + abs(number)
        return number

    def release_number(self, card):
        """Numero della stampa come appare nella tabella (es. 001/226, 023/P-A)."""
        code = card["_exp"]
        number = self.display_number(card)
        if code.startswith("PROMO"):
            return f"{number:03d}/P-{code.split('-')[1]}"
        return f"{number:03d}/{self.expansion_total[code]}"

    def type_pair(self, card):
        """Tipi della carta (uno o due) come nomi italiani."""
        types = [NUM_TYPE[t] for t in self.pokemon["PK_" + card["_design"]]["PokemonTypes"]]
        return types[0], (types[1] if len(types) > 1 else None)

    def page_types(self, title, cards):
        """Tipi della specie, ricavati dalle carte della forma base (Mega comprese)."""
        found = []
        for card in cards:
            base = re.sub(r"-ex$", "", card["_name"])
            if base not in (title, "Mega " + title):
                continue
            for t in self.pokemon["PK_" + card["_design"]]["PokemonTypes"]:
                if NUM_TYPE[t] not in found:
                    found.append(NUM_TYPE[t])
        first = min(cards, key=self.sort_key)
        first_type = TYPES.get(first["type"], first["type"])
        second = next((t for t in found if t != first_type), None) if len(found) == 2 else None
        return first_type, second

    def dragon_energies(self, cards):
        """Energie usate dagli attacchi, per i Pokémon di tipo Drago."""
        energies = []
        for card in sorted(cards, key=self.sort_key):
            for attack in card.get("attacks") or []:
                for cost in attack.get("cost") or []:
                    name = TYPES.get(cost, cost)
                    if name != "Incolore" and name not in energies:
                        energies.append(name)
        # l'energia Incolore non si elenca, tranne quando è l'unica usata
        return energies or ["Incolore"]


def card_link(card, data):
    """Nome della carta per {{GCC ID}}/il link alla pagina della carta."""
    name = card["_name"]
    is_ex = card.get("isEX")
    is_mega = data.pokemon["PK_" + card["_design"]]["IsMegaEvolution"]
    ex_suffix = ""
    if is_ex:
        ex_suffix = "{{ex|mega pocket}}" if is_mega else "{{ex|pocket}}"
    return name, is_ex, is_mega, ex_suffix


def split_owner_ex(name):
    """Per "Raticate-ex del Team Rocket" restituisce ("Raticate", "del Team Rocket")."""
    match = re.match(r"^(.*?)-ex (del .+)$", name)
    return (match.group(1), match.group(2)) if match else None


def display_name(card, data):
    """Nome mostrato (senza -ex) per le righe Divider e il parametro 4 di GCC ID."""
    name = card["_name"]
    return re.sub(r"-ex$", "", name) if card.get("isEX") else name


def build_page(title, ndex, cards, data, interwikis):
    """Costruisce il wikitesto di una pagina <Pokémon> (GCC Pocket)."""
    cards = sorted(cards, key=data.sort_key)
    first = cards[0]
    type1, type2 = data.page_types(title, cards)

    # sezioni: una per nome visualizzato (forma, ex, Mega…), dalla prima apparizione
    sections = []
    by_name = {}
    for card in cards:
        by_name.setdefault(card["_name"], []).append(card)
    for name, group in by_name.items():
        sections.append((name, sorted(group, key=data.sort_key)))
    sections.sort(key=lambda s: data.sort_key(s[1][0]))

    lines = []
    # navigazione
    nav = [f"prev={data.species_nav(ndex, -1)}", f"next={data.species_nav(ndex, +1)}"]
    nav.append(f"prevnum={data.species_nav_num(ndex, -1):04d}")
    nav.append(f"nextnum={data.species_nav_num(ndex, +1):04d}")
    nav.append(f"type={type1}")
    if type2:
        nav.append(f"type2={type2}")
    lines.append("{{GCCPocketPokémonPrevNext | " + " | ".join(nav) + " }}")
    lines.append("")
    # introduzione
    intro = f"{{{{GCCPocketPokémonIntro|{data.set_names[first['_exp']]}|{first['stageLabel']}|{type1}|{type2 or ''}"
    if "Drago" in (type1, type2):
        energies = data.dragon_energies(cards)
        intro += "|" + "|".join(energies)
    intro += "}}"
    lines.append(intro)
    lines.append("")
    # tabella
    header_name = sections[0][0] if sections[0][0] != title else title
    header = f"{{{{GCCPocketCardList/Header|{header_name}|{type1}"
    if type2:
        header += f"|{type2}"
    if header_name != title:
        header += f"|catname={title}"
    header += "}}"
    lines.append(header)
    gallery_cards = []
    for section_index, (section_name, section_cards) in enumerate(sections):
        if section_index > 0:
            divider_name = display_name(section_cards[0], data)
            if section_cards[0].get("isEX"):
                is_mega = data.pokemon["PK_" + section_cards[0]["_design"]]["IsMegaEvolution"]
                icon = "{{ex|mega pocket}}" if is_mega else "{{ex|pocket}}"
                owner = split_owner_ex(section_cards[0]["_name"])
                if owner:
                    divider_name = f"{owner[0]}{icon} {owner[1]}"
                else:
                    divider_name += icon
            divider = f"{{{{GCCPocketCardList/Divider|{divider_name}|{type1}"
            if type2:
                divider += f"|{type2}"
            # l'ancora della sezione serve ai collegamenti dalle pagine delle carte
            if section_cards[0].get("isEX"):
                divider += f"|name={section_cards[0]['_name']}"
            divider += "}}"
            lines.append(divider)
        designs = {}
        for card in section_cards:
            designs.setdefault(card["_design"], []).append(card)
        for design_index, design in enumerate(sorted(designs, key=lambda d: data.sort_key(designs[d][0]))):
            releases = designs[design]
            card = releases[0]
            name, is_ex, is_mega, ex_suffix = card_link(card, data)
            owner = split_owner_ex(name) if is_ex else None
            if owner:
                # "Raticate-ex del Team Rocket": l'icona ex va fra nome e "del …"
                base, owner_text = owner
                cardname = (f"{{{{GCC ID|{data.set_names[card['_exp']]}|{name}|{data.display_number(card)}|{base}}}}}"
                            + ex_suffix + " "
                            + f"{{{{GCC ID|{data.set_names[card['_exp']]}|{name}|{data.display_number(card)}|{owner_text}}}}}")
            elif is_ex:
                cardname = (f"{{{{GCC ID|{data.set_names[card['_exp']]}|{name}|{data.display_number(card)}"
                            f"|{display_name(card, data)}}}}}" + ex_suffix)
            else:
                cardname = f"{{{{GCC ID|{data.set_names[card['_exp']]}|{name}|{data.display_number(card)}}}}}"
            card_type, card_type2 = data.type_pair(card)
            line = f"{{{{GCCPocketCardList/Card|cardname={cardname}|type={card_type}"
            if card_type2:
                line += f"|type2={card_type2}"
            line += f"|rows={len(releases)}"
            if design_index == 0:
                line += "|firstcard=yes"
            line += "}}"
            lines.append(line)
            for release in releases:
                rarity = RARITY.get(release["rarity"])
                line = f"{{{{GCCPocketCardList/Release|set={data.set_names[release['_exp']]}"
                if not release["_exp"].startswith("PROMO") and rarity:
                    line += f"|rarity={rarity[0]}"
                    if rarity[0] in ("Diamante", "Stella", "Cromatico"):
                        line += f"|rarity count={rarity[1]}"
                line += f"|num={data.release_number(release)}}}}}"
                lines.append(line)
                gallery_cards.append(release)
    lines.append("{{GCCPocketCardList/Footer}}")
    lines.append("")
    # galleria
    lines.append("==Galleria==")
    # i colori _gcc sono quelli della serie GCC: senza suffisso il template usa
    # quelli della serie principale
    gallery = "{{GalleryDisplay/head|type=" + type1.lower() + "_gcc"
    if type2:
        gallery += "|type2=" + type2.lower() + "_gcc"
    gallery += "|content="
    lines.append(gallery)
    for card in gallery_cards:
        image = image_stem(card["_name"]) + image_stem(data.set_names[card["_exp"]]) + str(data.display_number(card)) + ".png"
        target = f"{card['_name']} ({data.set_names[card['_exp']]} {data.display_number(card)})"
        lines.append(f"{{{{GalleryDisplay/entry|{image}|[[{target}]]|{GALLERY_SIZE}}}}}")
    lines.append("}}")
    lines.append("")
    # interwiki
    for language, name in interwikis(title):
        lines.append(f"[[{language}:{name}]]")
    return "\n".join(lines) + "\n"


def main():
    named_args = {"data": os.environ.get("PTCGP_DATA", ""), "out": "data/gccp-itpages",
                  "locale": "it_IT", "interwiki": "en,es"}
    for arg in sys.argv[1:]:
        name, _, value = arg[1:].partition(":")
        named_args[name] = value.strip()
    if "help" in named_args:
        print(__doc__)
        return
    data_dir = named_args["data"]
    if not data_dir:
        print("Manca -data:<cartella out del dump> (o la variabile PTCGP_DATA).", file=sys.stderr)
        return
    if not os.path.isdir(os.path.join(data_dir, "cards")):
        print(f"{data_dir} non sembra la cartella out di ptcgp-carddump", file=sys.stderr)
        return

    try:
        data = Data(data_dir, named_args["locale"])
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return
    languages = [x.strip() for x in named_args["interwiki"].split(",") if x.strip()]

    def interwikis(title):
        row = data.name_by_ndex[data.ndex_of_name[title]]
        out = []
        if "en" in languages and row.get("en"):
            out.append(("en", f"{row['en']} (TCG Pocket)"))
        if "es" in languages and row.get("es"):
            out.append(("es", f"{row['es']} (TCG Pocket)"))
        return out

    # specie con almeno una carta
    by_title = {}
    skipped = 0
    for card in data.cards:
        title, ndex = data.species_of(card)
        if not title:
            skipped += 1
            print(f"ATTENZIONE: carta senza specie: {card['_name']!r} ({card['cardId']})", file=sys.stderr)
            continue
        by_title.setdefault((title, ndex), []).append(card)

    # le pagine, ordinate per numero di Pokédex
    ordered = sorted(by_title.items(), key=lambda kv: kv[0][1])
    # prev/next seguono le specie che hanno una pagina (non tutto il Pokédex:
    # Glalie, per esempio, non ha carte e viene saltato)
    position = {ndex: index for index, ((_, ndex), _) in enumerate(ordered)}

    def nav(ndex, step):
        return ordered[(position[ndex] + step) % len(ordered)][0]

    data.species_nav = lambda ndex, step: nav(ndex, step)[0]
    data.species_nav_num = lambda ndex, step: nav(ndex, step)[1]

    out_dir = named_args["out"]
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for (title, ndex), cards in ordered:
        text = build_page(title, ndex, cards, data, interwikis)
        file_name = fix_file_name(f"{title}{PAGE_SUFFIX}") + ".txt"
        with open(os.path.join(out_dir, file_name), "w", encoding="utf-8") as f:
            f.write(text)
        written += 1
    print(f"Scritte {written} pagine in {out_dir} da {len(data.cards)} stampe"
          f" ({skipped} carte senza specie).")


if __name__ == "__main__":
    main()
