"""Trasforma i tre json di un'espansione di ptcgp-carddump in quattro txt.

I tre input sono i file della stessa espansione nelle tre lingue
(<codice>_it_IT.json, <codice>_en_US.json, <codice>_ja_JP.json). L'italiano
dà tutti i dati della carta e delle sue righe, l'inglese e il giapponese
danno i nomi tradotti di attacchi, abilità e carte Allenatore. I quattro
output sono, nella cartella indicata da -out: (la corrente, se manca)

    <codice>_carte.txt        una riga per carta, tutti i dati della pagina
    <codice>_attacchi.txt     Nome IT / EN / JP degli attacchi, senza doppioni
    <codice>_abilita.txt      Nome IT / EN / JP delle abilità, senza doppioni
    <codice>_allenatori.txt   Nome IT / Classe / EN / JP delle carte Allenatore

Le colonne sono separate da "|" e la prima riga è l'intestazione, così il
file si apre in un foglio di calcolo o si legge a occhio. Nella tabella
delle carte "Testo Allenatore" è il testo della carta (il campo rule del
dump), non la regola della classe (il footer, "Puoi giocare una sola carta
Aiuto durante il tuo turno"): quella non va mai nel file.

Il numero delle carte segrete che il gioco numera con un negativo (Primi
Amici: -1, -2, -3) diventa il numero che porta la carta sul wiki (28, 29,
30), cioè il totale del set più il valore assoluto. Il secondo tipo delle
carte a due tipi (Mega Greninja-ex, Mega Mewtwo X-ex in Fusione Duale) è il
campo "type2" dei json: un dump creato prima che ptcgp-carddump lo
scrivesse lascia vuota quella colonna, e si risolve rigenerando il dump.

Il testo passa dai marcatori del gioco ai segni del wiki: \\x04<Tipo>\\x04
diventa {{et|Tipo}}, \\x03 la scritta "ex", \\x05/\\x06 il corsivo, \\x01/\\x02
il grassetto; i marcatori di impaginazione spariscono. Nel testo di una
carta Allenatore le voci di un elenco numerato vanno a capo con <br> e i
capoversi con <br><br>, così la riga del file resta una sola.

Uso:
    python json_to_txt.py <it.json> <en.json> <ja.json> [OPZIONI]

Opzioni:
    -out:<cartella>        dove scrivere i quattro txt (predefinito: .)
    -espansione:<nome>     il nome dell'espansione, senza chiedere al wiki
    -help                  mostra questo testo

Il nome italiano dell'espansione viene da Modulo:GCCPocket/data, come fa
gccp-build.py; senza rete (o se il codice non c'è) resta il codice e lo
script lo dice.
"""

import csv
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

WIKI_API = "https://wiki.pokemoncentral.it/api.php"
SETS_MODULE = "Modulo:GCCPocket/data"
USER_AGENT = "Pywikibot/1.0"

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
# Pokemon.json (e i costi degli attacchi) usano i tipi come numeri
NUM_TYPE = {1: "Incolore", 2: "Erba", 3: "Fuoco", 4: "Acqua", 5: "Lampo",
            6: "Psico", 7: "Lotta", 8: "Oscurità", 9: "Metallo", 10: "Drago"}

ADDITIONAL_CATEGORY = {
    1: "Ultracreatura",
    2: "Tempo Passato",
    3: "Tempo Futuro",
}

# classe delle carte Allenatore, quando il gioco non la scrive già in italiano
TRAINER_CLASS = {
    1: "Aiuto",
    2: "Strumento",
    3: "Oggetto Pokémon",
    4: "Strumento (Fossile)",
    5: "Stadio",
}

# come il gioco disegna la scritta "ex" nel nome di un Pokémon
EX_MARKUP = "'''''<big>ex</big>'''''"

# caratteri "spazio" anomali -> spazio normale
WEIRD_SPACES = [
    "\u00a0",  # NO-BREAK SPACE
    "\u2007",  # FIGURE SPACE
    "\u2009",  # THIN SPACE
    "\u200a",  # HAIR SPACE
    "\u202f",  # NARROW NO-BREAK SPACE
    "\u3000",  # IDEOGRAPHIC SPACE
]
# caratteri da rimuovere senza sostituzione
DROP_CHARS = [
    "\u200b",  # ZERO WIDTH SPACE
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE
]

MAIN_HEADER = [
    "Nome espansione", "Numero carta", "Nome carta",
    "isEX", "isMega", "additionalCategory", "PS", "Tipo", "Tipo 2",
    "Nome Abilità", "Effetto Abilità",
    "Nome Attacco 1", "Effetto Attacco 1",
    "Energia 1 Attacco 1", "Energia 2 Attacco 1", "Energia 3 Attacco 1",
    "Energia 4 Attacco 1", "Energia 5 Attacco 1", "Danno Attacco 1",
    "Nome Attacco 2", "Effetto Attacco 2",
    "Energia 1 Attacco 2", "Energia 2 Attacco 2", "Energia 3 Attacco 2",
    "Energia 4 Attacco 2", "Energia 5 Attacco 2", "Danno Attacco 2",
    "Debolezza", "Ritirata", "Illustratore",
    "Pokédex", "Jdex", "Testo Allenatore",
]

ATTACKS_HEADER = ["Nome IT Attacco", "Nome EN Attacco", "Nome JP Attacco"]
ABILITIES_HEADER = ["Nome IT Abilità", "Nome EN Abilità", "Nome JP Abilità"]
TRAINERS_HEADER = ["Nome IT", "Classe", "Nome EN", "Nome JP"]


# ── testo ──────────────────────────────────────────────────────────────────────
def it_type(name):
    """Tipo dai dati (nome inglese o numero) -> nome italiano."""
    if isinstance(name, int):
        return NUM_TYPE.get(name, str(name))
    return TYPES.get(name, name or "")


def clean_text(text, japanese=False, line_breaks=False):
    """Il testo del gioco come va scritto sul wiki.

    - \\x04<Tipo>\\x04 -> {{et|<tipo italiano>}}
    - \\x03 -> la scritta "ex" ('''<big>ex</big>'''), \\x01/\\x02 -> grassetto,
      \\x05/\\x06 -> corsivo
    - \\x14<len>\\x14, \\x15, \\x16, \\x17, \\x0e<f>\\x0e, \\x0f, \\x10<d>\\x10 ->
      tolti: sono misure di impaginazione
    - \\x11/\\x12 delimitano il nome di una forma ("Alolan" Exeggutor,
      Exeggutor "di Alola"): diventano lo spazio che separa le due parole,
      se dall'altra parte c'è una parola (non davanti a "-ex"); in
      giapponese non c'è spazio
    - \\n -> spazio, o a capo conservato con line_breaks (per rule_text)
    - spazi anomali -> spazio normale; in giapponese lo spazio ideografico
      resta, perché è quello che usa il testo della carta
    """
    if not text:
        return ""

    # icone di Energia e scritta "ex"
    for eng, ita in TYPES.items():
        text = text.replace("\x04" + eng + "\x04", "{{et|" + ita + "}}")
    text = text.replace("\x03", EX_MARKUP)

    # misure di impaginazione, prima dei marcatori di stile
    text = re.sub("\x14[^\x14]*\x14", "", text)
    text = re.sub("\x0e[^\x0e]*\x0e", "", text)
    text = re.sub("\x10[^\x10]*\x10", "", text)
    for ch in ("\x15", "\x16", "\x17", "\x0f"):
        text = text.replace(ch, "")

    # corsivo e grassetto
    text = text.replace("\x05", "''").replace("\x06", "''")
    text = text.replace("\x01", "'''").replace("\x02", "'''")

    # a capo
    if line_breaks:
        text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    else:
        text = text.replace("\n", " ")

    # nome di una forma: lo spazio fra nome e qualificatore
    if japanese:
        text = text.replace("\x11", "").replace("\x12", "")
    else:
        text = re.sub(r"(?<=\w)\x11", " ", text)
        text = text.replace("\x11", "")
        text = re.sub(r"\x12(?=\w)", " ", text)
        text = text.replace("\x12", "")

    # "Nidoran ♀" si scrive "Nidoran♀"
    text = text.replace("Nidoran\u202f♀", "Nidoran♀").replace("Nidoran\u202f♂", "Nidoran♂")

    # spazi anomali
    for ch in WEIRD_SPACES:
        if japanese and ch == "\u3000":
            continue
        text = text.replace(ch, " ")
    for ch in DROP_CHARS:
        text = text.replace(ch, "")

    # trattino non separabile -> trattino normale (Pokémon‑ex)
    text = text.replace("\u2011", "-")
    # le temperature del gioco alternano "º" e "°": sul wiki si scrive "°C"
    text = text.replace("\u00ba", "\u00b0")
    # tabulazioni e spazi multipli
    text = text.replace("\t", " ")
    text = re.sub(r" +", " ", text)
    if line_breaks:
        text = re.sub(r"(?: *<br> *)+", "<br>", text)
        text = re.sub(r"^(?:<br>)+|(?:<br>)+$", "", text)
    return text.strip()


CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def rule_text(text):
    """Il testo di una carta Allenatore, su una riga sola.

    I punti di un elenco numerato vanno a capo con <br>, i capoversi con
    <br><br>: è la forma che hanno le pagine delle carte (Borsa Eevee,
    Provocazione di Blu).
    """
    text = clean_text(text, line_breaks=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ""
    out = lines[0]
    for line in lines[1:]:
        out += ("<br>" if line[0] in CIRCLED else "<br><br>") + line
    return out


def damage_text(attack):
    """"30+", "50×", "120-": il segno segue il numero, come sulla carta."""
    value = attack.get("damage") or 0
    glyph = attack.get("damageSymbolGlyph") or ""
    if not value and not glyph:
        return ""
    return f"{value}{glyph}"


def sort_key(text):
    """Ordine alfabetico italiano, senza badare ad accenti e maiuscole."""
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return plain.casefold()


# ── lettura ────────────────────────────────────────────────────────────────────
def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def by_id(cards):
    return {card.get("cardId"): card for card in cards}


def trainer_class(card):
    """La classe di una carta Allenatore, come la scrive il gioco."""
    return card.get("typeLabel") or TRAINER_CLASS.get(card.get("trainerType"), "")


def number_of(card, offset):
    """Numero della carta; i negativi del gioco vanno dopo il totale del set."""
    number = card.get("collectionNumber")
    if isinstance(number, int) and number < 0:
        return offset + abs(number)
    return number


def number_offset(cards):
    """Totale del set: il numero più alto fra quelli positivi."""
    numbers = [c["collectionNumber"] for c in cards
               if isinstance(c.get("collectionNumber"), int) and c["collectionNumber"] > 0]
    return max(numbers) if numbers else 0


def second_type(card):
    """Il secondo tipo di una carta, se ne ha due."""
    return it_type(card["type2"]) if card.get("type2") else ""


def fetch_set_name(code):
    """Nome italiano dell'espansione da Modulo:GCCPocket/data, se il wiki risponde."""
    params = {"action": "parse", "page": SETS_MODULE, "prop": "wikitext",
              "format": "json", "formatversion": "2"}
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    block = re.search(r"data\.codes\s*=\s*\{(.*?)\n\}", data["parse"]["wikitext"], re.S)
    if not block:
        raise ValueError(f"data.codes non trovato in {SETS_MODULE}")
    names = {c.casefold(): n for n, c in re.findall(
        r"\[\s*['\"](.+?)['\"]\s*\]\s*=\s*['\"]([^'\"]+)['\"]", block.group(1))}
    return names.get(code.casefold())


# ── le quattro tabelle ─────────────────────────────────────────────────────────
def card_rows(cards, others, set_name):
    """Una riga per carta, con il testo italiano e il Pokédex giapponese."""
    offset = number_offset(cards)
    english = others["en_US"]
    japanese = others["ja_JP"]
    rows = []
    for card in sorted(cards, key=lambda c: (number_of(c, offset), c.get("cardId", ""))):
        other = english.get(card.get("cardId"), {})
        ja = japanese.get(card.get("cardId"), {})
        is_trainer = card.get("kind") == "trainer"

        ability = card.get("ability")
        if isinstance(ability, dict):
            ability_name = clean_text(ability.get("name", ""))
            ability_effect = clean_text(ability.get("desc", ""))
        else:
            ability_name, ability_effect = "", ""

        attacks = []
        for index in range(2):
            atk = (card.get("attacks") or [])
            atk = atk[index] if len(atk) > index else None
            if not atk:
                attacks.append(["", "", "", "", "", "", "", ""])
                continue
            costs = [it_type(c) for c in atk.get("cost") or []][:5]
            costs += [""] * (5 - len(costs))
            attacks.append([clean_text(atk.get("name", "")),
                            clean_text(atk.get("desc", "")),
                            *costs,
                            damage_text(atk)])

        rows.append([
            set_name,
            number_of(card, offset),
            clean_text(card.get("name", "")),
            card.get("isEX") is True,
            card.get("isMega") is True,
            ADDITIONAL_CATEGORY.get(card.get("additionalCategory")) or "",
            card.get("hp", ""),
            trainer_class(card) if is_trainer else it_type(card.get("type", "")),
            "" if is_trainer else second_type(card),
            ability_name,
            ability_effect,
            *attacks[0],
            *attacks[1],
            "" if is_trainer else it_type(card.get("weakness", "")),
            card.get("retreat", ""),
            clean_text(card.get("illustrator", "")),
            clean_text(card.get("flavor", "")),
            clean_text(ja.get("flavor", ""), japanese=True),
            rule_text(card.get("rule", "")) if is_trainer else "",
        ])
    return rows


def attack_rows(cards, others):
    """Nome di ogni attacco nelle tre lingue, senza doppioni."""
    found = {}
    english = others["en_US"]
    japanese = others["ja_JP"]
    for card in cards:
        other = english.get(card.get("cardId"), {})
        ja = japanese.get(card.get("cardId"), {})
        for index, atk in enumerate(card.get("attacks") or []):
            name = clean_text(atk.get("name", ""))
            if not name:
                continue
            other_atk = (other.get("attacks") or [])
            ja_atk = (ja.get("attacks") or [])
            row = [
                name,
                clean_text(other_atk[index].get("name", "")) if len(other_atk) > index else "",
                clean_text(ja_atk[index].get("name", ""), japanese=True) if len(ja_atk) > index else "",
            ]
            if name in found:
                if found[name] != row:
                    print(f"ATTENZIONE: l'attacco {name!r} ha due traduzioni: {found[name]} e {row}",
                          file=sys.stderr)
                continue
            found[name] = row
    return sorted(found.values(), key=lambda row: sort_key(row[0]))


def ability_rows(cards, others):
    """Nome di ogni abilità nelle tre lingue, senza doppioni."""
    found = {}
    english = others["en_US"]
    japanese = others["ja_JP"]
    for card in cards:
        ability = card.get("ability")
        if not isinstance(ability, dict):
            continue
        name = clean_text(ability.get("name", ""))
        if not name:
            continue
        other = english.get(card.get("cardId"), {}).get("ability")
        ja = japanese.get(card.get("cardId"), {}).get("ability")
        row = [
            name,
            clean_text(other.get("name", "")) if isinstance(other, dict) else "",
            clean_text(ja.get("name", ""), japanese=True) if isinstance(ja, dict) else "",
        ]
        if name in found:
            if found[name] != row:
                print(f"ATTENZIONE: l'abilità {name!r} ha due traduzioni: {found[name]} e {row}",
                      file=sys.stderr)
            continue
        found[name] = row
    return sorted(found.values(), key=lambda row: sort_key(row[0]))


def trainer_rows(cards, others):
    """Nome e classe di ogni carta Allenatore nelle tre lingue, senza doppioni."""
    found = {}
    english = others["en_US"]
    japanese = others["ja_JP"]
    for card in cards:
        if card.get("kind") != "trainer":
            continue
        name = clean_text(card.get("name", ""))
        if not name:
            continue
        row = [name, trainer_class(card),
               clean_text(english.get(card.get("cardId"), {}).get("name", "")),
               clean_text(japanese.get(card.get("cardId"), {}).get("name", ""), japanese=True)]
        found.setdefault(tuple(row), row)
    return sorted(found.values(), key=lambda row: (sort_key(row[0]), sort_key(row[1])))


def write_txt(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Fatto: {len(rows)} righe -> {path}")


# ── avvio ──────────────────────────────────────────────────────────────────────
def parse_args(argv):
    files = []
    options = {"out": os.getcwd(), "espansione": ""}
    for arg in argv:
        if arg.startswith("-"):
            name, _, value = arg[1:].partition(":")
            if name == "help":
                options["help"] = True
                continue
            if name not in options:
                raise SystemExit(f"Opzione sconosciuta: {arg}")
            options[name] = value.strip()
        else:
            files.append(arg)
    if len(files) != 3 and not options.get("help"):
        raise SystemExit("Uso: python json_to_txt.py <it.json> <en.json> <ja.json>"
                         " [-out:<cartella>] [-espansione:<nome>]")
    options["files"] = files
    return options


def main():
    # un carattere che la console non sa scrivere non deve fermare lo script
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    options = parse_args(sys.argv[1:])
    if options.get("help"):
        print(__doc__)
        return

    it_path, en_path, ja_path = options["files"]
    italian = read_json(it_path)
    others = {"en_US": by_id(read_json(en_path)), "ja_JP": by_id(read_json(ja_path))}

    missing = [c.get("cardId") for c in italian
               if c.get("cardId") not in others["en_US"] or c.get("cardId") not in others["ja_JP"]]
    if missing:
        print(f"ATTENZIONE: {len(missing)} carte italiane senza la stessa carta in inglese"
              f" o giapponese (es. {missing[0]}): restano senza nomi tradotti", file=sys.stderr)

    code = italian[0].get("expansion", "") if italian else ""
    set_name = options["espansione"]
    if not set_name:
        try:
            set_name = fetch_set_name(code)
        except Exception as error:  # noqa: BLE001
            print(f"ATTENZIONE: non leggo {SETS_MODULE} dal wiki ({error}):"
                  f" uso il codice {code}", file=sys.stderr)
            set_name = code
        if not set_name:
            print(f"ATTENZIONE: il codice {code} non ha un nome in {SETS_MODULE}:"
                  f" uso il codice", file=sys.stderr)
            set_name = code

    os.makedirs(options["out"], exist_ok=True)
    stem = os.path.join(options["out"], re.sub(r"[^a-z0-9-]", "", code.lower()) or "carte")
    write_txt(f"{stem}_carte.txt", MAIN_HEADER, card_rows(italian, others, set_name))
    write_txt(f"{stem}_attacchi.txt", ATTACKS_HEADER, attack_rows(italian, others))
    write_txt(f"{stem}_abilita.txt", ABILITIES_HEADER, ability_rows(italian, others))
    write_txt(f"{stem}_allenatori.txt", TRAINERS_HEADER, trainer_rows(italian, others))


if __name__ == "__main__":
    main()
