#!/usr/bin/env python3
"""
Compila il template {{credits}} nella pagina File: di una carta PCW.
Riceve in input fam, lang e:
  a) il titolo di una pagina carta (Pokémon o Allenatore) -> elabora quella carta
  b) il nome di un'espansione GCC Pocket -> elabora TUTTE le carte
     dell'espansione (regolari + segrete).

L'artista NON viene piu' letto dalla caption della pagina carta: per ogni
variante (originale + ristampe) il nome dell'illustratore si ricava dai JSON
di gioco prodotti da ptcgp-carddump (out/cards/<set>_it_IT.json), dove ogni
carta porta il campo "illustrator". Le pagine carta servono solo per sapere
quali sono le varianti (immagine + ristampe) e le pagine File: da compilare.

Abbinamento variante -> carta del dump:
  per ogni variante si ricava la coppia (espansione, numero) da tre fonti:
    1. i parametri setN/cardnoN dell'infobox (es. set1=Promo-A|cardno1=023/P-A);
    2. la riga corrispondente di {{PokemoncardInfobox/Expansion}} (le pagine
       piu' vecchie non hanno setN/cardnoN: set e numero stanno solo li');
    3. il nome del file immagine, che e' costruito come
       <nome carta><nome espansione><numero> (es. BulbasaurGeniSupremi227.png).
  Se le fonti concordano si usa quella; se discordano si sceglie la carta del
  dump il cui nome coincide con quello della carta (prefisso del nome file),
  poi quella il cui illustrator coincide con l'artista della caption, e in
  ultima istanza la prima fonte in ordine di priorita'. Ogni disaccordo viene
  segnalato fra gli avvisi.

Supporta carte con DOPPIO ARTISTA: nel dump sono indicate come
"Nome1/Nome2" (es. Nobusawa/Mochipuyo) e vengono compilate come
|artist=Nome1|artist2=Nome2.

In modalita' espansione, le carte segrete vengono risolte seguendo i redirect:
  - redirect nella STESSA espansione -> ignorato (la carta base ha gia' il reprint)
  - redirect in un'ALTRA espansione -> il file viene cercato tra i reprint
    dell'infobox della carta target, filtrando per nome espansione

L'auto-riconoscimento della modalita' avviene tramite pattern: se il titolo
contiene "(NomeSet Numero)" viene trattato come carta singola, altrimenti
come nome espansione (la pagina cercata sara' "NomeEspansione (GCC Pocket)").

Gestisce il template credits in TUTTI i formati presenti su PCW:
  - {{credits|...}} senza artist            -> inserisce artist e cardartist
  - {{credits|artist=}} o {{credits|artist=|...}} -> riempie artist (vuoto)
  - {{credits|artist=[[nome]]}}             -> sostituisce con nome pulito
  - {{credits|artist=Nome|cardartist=...}}  -> gia' compilato, non tocca

Doppio artista                                -> |artist=Nome1|artist2=Nome2

Se l'artista ha una pagina PCW "Nome (illustratore)", il template viene compilato con
artist=Nome (illustratore) e artistalt=Nome (solo per singolo artista).

MODALITA' DI VERIFICA (--check):
  Invece di scrivere, controlla che i template {{credits}} delle carte
  siano compilati correttamente (artist + cardartist, ed eventualmente artist2),
  confrontandoli con l'artista del dump. Stampa un riepilogo con l'elenco delle
  carte OK e di quelle non compilate.

DIPENDENZE:
  - Python 3.6+
  - pywikibot (pip install pywikibot)
  - user-config.py configurato per pcw (it)
  - i dump di ptcgp-carddump (https://github.com/pokemoncentral/ptcgp-carddump):
    out/cards/<set>_it_IT.json, generati con `carddump cards`

NOMI DELLE ESPANSIONI:
  la corrispondenza fra il codice del gioco (A1, B3b, ...) e il nome
  dell'espansione usato su PCW si legge dal modulo Modulo:GCCPocket/data:
  una nuova espansione si aggiunge li', senza toccare questo script.

PERCORSO DEI DUMP:
  la variabile d'ambiente PTCGP_CARD_DUMP o --dump CARTELLA; se non sono
  indicate si usa un checkout di ptcgp-carddump accanto a wiki-util
  (<cartella di wiki-util>/../ptcgp-carddump/out/cards).

ESEMPI D'USO
  Interattivo:
      $ python compila_credits.py

  Carta singola (doppio artista):
      $ python compila_credits.py pcw it "Camelia (Giorni Giocondi 66)"

  Espansione:
      $ python compila_credits.py pcw it "Giorni Giocondi"

  Dump in un'altra cartella:
      $ python compila_credits.py --dump "D:\\ptcgp\\out\\cards" \
            pcw it "Giorni Giocondi"

  Verifica carta singola:
      $ python compila_credits.py --check pcw it "Camelia (Giorni Giocondi 66)"

  Verifica espansione:
      $ python compila_credits.py --check pcw it "Giorni Giocondi"
"""

import json
import os
import re
import sys

import pywikibot


# Cartella dei dump di ptcgp-carddump, con un file per espansione e lingua.
# Si può indicare con PTCGP_CARD_DUMP o con --dump; altrimenti si usa un
# checkout di ptcgp-carddump accanto a wiki-util, come fa ptcgp-cardrender.
DUMP_DIR = os.environ.get(
    "PTCGP_CARD_DUMP",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.pardir,
        "ptcgp-carddump",
        "out",
        "cards",
    ),
)
DUMP_LOCALE = "it_IT"  # i nomi su PCW sono quelli italiani

# Codice espansione del gioco -> nome dell'espansione su PCW: si legge dal
# modulo del wiki (EXPANSION_MODULE) all'avvio, cosi' una nuova espansione si
# aggiunge li' e non qui. Lo riempie load_expansion_names().
EXPANSION_MODULE = "GCCPocket/data"
EXPANSION_NAMES = {}

# Indici ricavati da EXPANSION_NAMES, riempiti da set_expansion_names().
SET_KEYS = {}
SET_KEYS_BY_LENGTH = []
CODE_BY_SET_NAME = {}
CODE_BY_LOWER_CODE = {}

# Caratteri invisibili che compaiono nei nomi dei file e nelle voci del wiki.
INVISIBLE_CHARS = "\u200e\u200f\u200b\u200c\u200d\u00ad\ufeff\x11\x12"

# Template infobox riconosciuti (case-insensitive)
INFOBOX_NAMES = {
    "pokémoncardinfobox",
    "pokemoncardinfobox",
    "gcccartatrainerinfobox",
}

# Nome dell'artista nei JSON: i doppi artisti sono separati da "/".
ARTIST_SEPARATOR = "/"


# ======================================================================
#  DUMP DI GIOCO
# ======================================================================


def _strip_invisible(text):
    """Toglie caratteri invisibili e di controllo (LRM, ZWSP, \x11, \x12...)."""
    for char in INVISIBLE_CHARS:
        text = text.replace(char, "")
    return text


def normalize_name(text):
    """Forma di confronto di un nome: minuscole, senza spazi ne' apostrofi."""
    text = _strip_invisible(text or "")
    return re.sub(r"[\s'’]", "", text).lower()


def normalize_set(text):
    """Forma di confronto di un nome di espansione."""
    return re.sub(r"\s+", " ", _strip_invisible(text or "")).strip().lower()


def set_expansion_names(names):
    """
    Registra la corrispondenza {codice: nome PCW} e ne ricava gli indici.

    SET_KEYS usa il nome come compare nei nomi dei file immagine, senza spazi
    e apostrofi: "L'Isola Misteriosa" -> "LIsolaMisteriosa".
    """
    global SET_KEYS, SET_KEYS_BY_LENGTH, CODE_BY_SET_NAME, CODE_BY_LOWER_CODE

    EXPANSION_NAMES.clear()
    EXPANSION_NAMES.update(names)
    SET_KEYS = {re.sub(r"[\s'’]", "", name): code for code, name in names.items()}
    SET_KEYS_BY_LENGTH = sorted(SET_KEYS, key=len, reverse=True)
    CODE_BY_SET_NAME = {normalize_set(name): code for code, name in names.items()}
    CODE_BY_LOWER_CODE = {code.lower(): code for code in names}


def expansion_module_title(site):
    """Titolo della pagina del modulo con i codici delle espansioni."""
    prefix = "Modulo"
    try:
        prefix = site.namespace(828) or prefix
    except Exception:
        pass
    return f"{prefix}:{EXPANSION_MODULE}"


def parse_expansion_codes(text):
    """
    Ricava {codice: nome su PCW} dalla tabella data.codes del modulo.

    Il modulo associa il nome dell'espansione al codice del gioco,
    es. ['Geni Supremi'] = 'A1'.
    """
    block = re.search(r"data\.codes\s*=\s*\{(.*?)\n\}", text, re.S)
    if not block:
        raise ValueError("tabella 'data.codes' non trovata")

    # Chiave e valore possono usare apostrofi o virgolette ("L'Isola
    # Misteriosa" sta fra virgolette perche' contiene un apostrofo).
    pattern = re.compile(
        r"\[\s*(?:\"([^\"]*)\"|'([^']*)')\s*\]\s*=\s*(?:\"([^\"]*)\"|'([^']*)')\s*,?"
    )
    names = {}
    for match in pattern.finditer(block.group(1)):
        name = match.group(1) if match.group(1) is not None else match.group(2)
        code = match.group(3) if match.group(3) is not None else match.group(4)
        if not name or not code:
            continue
        names[code.strip()] = name.strip()
    return names


def load_expansion_names(site):
    """Legge dal wiki i codici delle espansioni e li registra."""
    title = expansion_module_title(site)
    page = pywikibot.Page(site, title)
    if not page.exists():
        raise SystemExit(
            f"ERRORE: modulo '{title}' non trovato: senza la corrispondenza "
            f"fra codici del gioco e nomi delle espansioni le carte del dump "
            f"non si riconoscono."
        )
    try:
        names = parse_expansion_codes(page.text)
    except ValueError as error:
        raise SystemExit(f"ERRORE: modulo '{title}': {error}.")
    if not names:
        raise SystemExit(f"ERRORE: modulo '{title}': nessuna espansione letta.")
    set_expansion_names(names)
    print(f"Espansioni: {len(names)} codici letti da {title}")
    return names


def expansion_code(set_name):
    """Codice del dump (es. "B3b") a partire dal nome usato su PCW."""
    text = normalize_set(set_name)
    if not text:
        return None
    return CODE_BY_SET_NAME.get(text) or CODE_BY_LOWER_CODE.get(text)


def parse_image_name(filename):
    """
    Ricava (codice espansione, numero, nome carta) dal nome di un file immagine.

    I file delle carte GCC Pocket si chiamano <nome carta><nome espansione><numero>
    (es. BulbasaurGeniSupremi227.png, ChimcharPromo-A40.png). Restituisce None
    se il nome non segue lo schema.
    """
    stem = os.path.splitext(_strip_invisible(filename or "").strip())[0]
    lowered = stem.lower()
    for key in SET_KEYS_BY_LENGTH:
        position = lowered.find(key.lower())
        if position <= 0:
            continue
        number = stem[position + len(key):]
        if not number.isdigit():
            continue
        return SET_KEYS[key], int(number), stem[:position]
    return None


def load_dump(dump_dir):
    """
    Legge tutti i dump del gioco e restituisce {(codice, numero): carta}.

    Ogni carta e' un dizionario con "name" (nome italiano) e "illustrator".
    """
    if not os.path.isdir(dump_dir):
        raise SystemExit(
            f"ERRORE: cartella dei dump '{dump_dir}' non trovata.\n"
            f"Genera i JSON con `carddump cards` oppure indica la cartella "
            f"con --dump."
        )

    suffix = f"_{DUMP_LOCALE}.json"
    files = sorted(name for name in os.listdir(dump_dir) if name.endswith(suffix))
    if not files:
        raise SystemExit(
            f"ERRORE: nessun file '*{suffix}' in '{dump_dir}'.\n"
            f"Genera i JSON con `carddump cards`."
        )

    cards = {}
    for file_name in files:
        raw_code = file_name[: -len(suffix)]
        code = CODE_BY_LOWER_CODE.get(raw_code.lower(), raw_code)
        if code not in EXPANSION_NAMES:
            print(
                f"ATTENZIONE: l'espansione '{raw_code}' del dump non e' nel "
                f"modulo Modulo:{EXPANSION_MODULE}: le sue carte non verranno "
                f"riconosciute."
            )
        with open(os.path.join(dump_dir, file_name), encoding="utf-8") as handle:
            rows = json.load(handle)

        # I numeri negativi sono le carte "oltre" il totale del set (i tre Mew
        # di SP1): -1 e' la prima dopo l'ultima carta regolare, -2 la seconda e
        # cosi' via, quindi su PCW diventano 28, 29, 30 nell'ordine -1, -2, -3.
        positives = [
            row["collectionNumber"] for row in rows if row["collectionNumber"] > 0
        ]
        highest = max(positives) if positives else 0
        negatives = sorted(
            (row["collectionNumber"] for row in rows if row["collectionNumber"] < 0),
            reverse=True,
        )
        moved = {number: highest + 1 + index for index, number in enumerate(negatives)}

        for row in rows:
            number = moved.get(row["collectionNumber"], row["collectionNumber"])
            cards[(code, number)] = {
                "name": row.get("name") or "",
                "illustrator": (row.get("illustrator") or "").strip(),
            }
    return cards


def split_artists(illustrator):
    """Divide "Nome1/Nome2" nella lista dei nomi (di solito uno solo)."""
    if not illustrator:
        return []
    return [
        name.strip()
        for name in illustrator.split(ARTIST_SEPARATOR)
        if name.strip()
    ]


# ======================================================================
#  ESTRAZIONE DELLE VARIANTI DALLA PAGINA CARTA
# ======================================================================


def extract_variants(card_text):
    """
    Dal wikitext di una pagina carta (Pokemon o Allenatore) estrae le varianti:
    l'originale (image/caption) e le ristampe (reprint{i}/recaption{i}).

    Restituisce una lista di dizionari con "image", "set_name", "cardno"
    (dai parametri setN/cardnoN, vuoti se assenti) e "row" (la coppia
    (espansione, numero) della riga {{PokemoncardInfobox/Expansion}} nella
    stessa posizione, oppure ("", "")).

    Il numero di varianti si ricava dalle chiavi presenti: reprint{i} per le
    ristampe e, per le carte del GCC cartaceo, il parametro reprint=N.
    """
    templates = pywikibot.textlib.extract_templates_and_params(card_text)

    infobox = None
    rows = []

    for tmpl_name, params in templates:
        clean = tmpl_name.strip().lower()
        if clean.startswith("template:"):
            clean = clean[9:]

        if infobox is None and clean in INFOBOX_NAMES:
            infobox = {
                key.strip().lower(): (value or "").strip()
                for key, value in params.items()
            }
        elif clean == "pokémoncardinfobox/expansion":
            # La riga porta l'espansione come {{GCCP|Nome}} e il numero in cardno.
            expansion = params.get("expansion") or ""
            match = re.search(r"\{\{\s*gccp\s*\|([^|}]+)", expansion, re.I)
            rows.append(
                (
                    match.group(1).strip() if match else "",
                    (params.get("cardno") or "").strip(),
                )
            )

    if infobox is None:
        return []

    reprint_count = 1  # default: solo originale
    for key, value in infobox.items():
        match = re.fullmatch(r"reprint(\d+)", key)
        if match:
            reprint_count = max(reprint_count, int(match.group(1)) + 1)
        elif key == "reprint":
            try:
                reprint_count = max(reprint_count, int(value))
            except ValueError:
                pass

    variants = []
    for index in range(reprint_count):
        suffix = "" if index == 0 else str(index)
        image = infobox.get(("reprint" + suffix) if suffix else "image", "")
        if not image:
            continue
        variants.append(
            {
                "index": index,
                "image": image,
                "set_name": infobox.get(("set" + suffix) if suffix else "set0", ""),
                "cardno": infobox.get(("cardno" + suffix) if suffix else "cardno0", ""),
                "caption": infobox.get(
                    ("recaption" + suffix) if suffix else "caption", ""
                ),
                "row": rows[index] if index < len(rows) else ("", ""),
            }
        )
    return variants


def caption_artists(caption):
    """Nomi mostrati nei wikilink della caption ([[Nome|mostrato]] -> mostrato)."""
    artists = []
    for match in re.finditer(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", caption or ""):
        artists.append((match.group(2) or match.group(1)).strip())
    return artists


def number_of(cardno):
    """Numero della carta da "001/226", "023/P-A", "-2/027"..."""
    match = re.match(r"\s*(-?\d+)", cardno or "")
    return int(match.group(1)) if match else None


def variant_candidates(variant):
    """
    Coppie (codice, numero, fonte) ricavate da una variante, senza duplicati
    e in ordine di priorita': infobox, riga Expansion, nome del file.
    """
    candidates = []
    seen = set()

    def add(set_name, number, source):
        code = expansion_code(set_name)
        if not code or number is None:
            return
        if (code, number) in seen:
            return
        seen.add((code, number))
        candidates.append((code, number, source))

    add(variant["set_name"], number_of(variant["cardno"]), "infobox")
    add(variant["row"][0], number_of(variant["row"][1]), "riga Expansion")
    parsed = parse_image_name(variant["image"])
    if parsed:
        add(parsed[0], parsed[1], "nome file")
    return candidates


def resolve_variant(variant, dump, page_name):
    """
    Trova nel dump la carta corrispondente alla variante.

    Restituisce (codice, numero, fonte, artisti, avviso): "artisti" e' la lista
    dei nomi (vuota se la carta non si trova) e "avviso" una nota da stampare.
    """
    candidates = variant_candidates(variant)
    found = [item for item in candidates if (item[0], item[1]) in dump]

    if not found:
        listed = ", ".join(f"{code} {number}" for code, number, _ in candidates)
        missing = "carta non trovata nel dump"
        if listed:
            missing += f" ({listed})"
        else:
            missing += " (nessun candidato)"
        return None, None, None, [], missing

    warning = None
    if len(found) == 1:
        chosen = found[0]
        if len(candidates) > 1:
            warning = f"altre fonti scartate, valida solo {chosen[0]} {chosen[1]}"
    else:
        # Fonti discordanti: la carta giusta e' quella con il nome della carta
        # (il prefisso del nome file, oppure il titolo della pagina per
        # l'originale), poi quella con l'artista indicato nella caption.
        parsed = parse_image_name(variant["image"])
        expected = parsed[2] if parsed else page_name
        named = [
            item
            for item in found
            if normalize_name(dump[(item[0], item[1])]["name"])
            == normalize_name(expected)
        ]
        if len(named) == 1:
            chosen = named[0]
            warning = (
                f"fonti discordanti, scelto {chosen[0]} {chosen[1]} "
                f"(nome della carta)"
            )
        else:
            caption = [
                normalize_name(name) for name in caption_artists(variant["caption"])
            ]
            by_caption = []
            for item in found:
                illustrators = split_artists(dump[(item[0], item[1])]["illustrator"])
                if [normalize_name(name) for name in illustrators] == caption:
                    by_caption.append(item)
            if len(by_caption) == 1:
                chosen = by_caption[0]
                warning = (
                    f"fonti discordanti, scelto {chosen[0]} {chosen[1]} "
                    f"(artista in caption)"
                )
            else:
                chosen = found[0]
                warning = (
                    f"fonti discordanti, scelto {chosen[0]} {chosen[1]} "
                    f"(prima fonte)"
                )

    card = dump[(chosen[0], chosen[1])]
    artists = split_artists(card["illustrator"])
    if not artists:
        return chosen[0], chosen[1], chosen[2], [], "illustratore assente nel dump"
    return chosen[0], chosen[1], chosen[2], artists, warning


def variant_in_expansion(variant, expansion_name):
    """Vero se la variante appartiene all'espansione indicata (nome PCW)."""
    target = normalize_set(expansion_name)
    if variant["set_name"] and normalize_set(variant["set_name"]) == target:
        return True
    if variant["row"][0] and normalize_set(variant["row"][0]) == target:
        return True
    parsed = parse_image_name(variant["image"])
    if parsed and normalize_set(EXPANSION_NAMES[parsed[0]]) == target:
        return True
    return False


# ======================================================================
#  MODIFICA DEL TEMPLATE CREDITS
# ======================================================================


def credits_params(file_text):
    """Parametri del template {{credits}} della pagina File ({} se non c'e')."""
    match = re.search(r"\{\{credits\s*\|([^}]*)\}\}", file_text)
    if not match:
        return {}

    params = {}
    parts = re.split(
        r"\s*\|\s*(?=(?:[^\]]*\[\[[^\]]*\]\])*[^\]]*$)",
        match.group(1),
    )
    for part in parts:
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        params[key.strip().lower()] = value.strip()
    return params


def compiled_artists(params):
    """
    Artisti gia' scritti nel template, senza il suffisso " (illustratore)".

    Considera artist e artist2, come li compila lo script.
    """
    artists = []
    for key in ("artist", "artist2"):
        value = (params.get(key) or "").strip()
        if value:
            artists.append(re.sub(r"\s*\(illustratore\)$", "", value, flags=re.I))
    return artists


def _format_artist_insert(artist_names):
    """
    Costruisce la stringa dei parametri artist da inserire nel template credits.

    Per singolo artista: artist=Nome
    Per doppio artista:  artist=Nome1|artist2=Nome2
    """
    if len(artist_names) == 0:
        return "artist="
    elif len(artist_names) == 1:
        return f"artist={artist_names[0]}"
    else:
        return f"artist={artist_names[0]}|artist2={'|artist2='.join(artist_names[1:])}"


def update_credits_template(file_text, artist_names, artistalt=None):
    """
    Sostituisce il template {{credits}} nella pagina dell'immagine.

    artist_names e' una lista di nomi artisti (1 o 2 elementi).

    Per artista singolo:
      - Se esiste una pagina "Nome (illustratore)":
          |artist=Nome (illustratore)|artistalt=Nome|cardartist=tcgpocket
      - Altrimenti:
          |artist=Nome|cardartist=tcgpocket

    Per doppio artista:
      |artist=Nome1|artist2=Nome2|cardartist=tcgpocket

    Gestisce tre formati del template credits:
      A) {{credits|artist=...}} con artist vuoto -> riempie artist
      B) {{credits|artist=[[nome]]...}}          -> sostituisce il wikilink
      C) {{credits|...}} senza parametro artist  -> INSERISCE artist ex-novo
         (formato delle pagine File non ancora compilate, es. upload)

    Restituisce (nuovo_testo, errore).
    """
    if "{{credits" not in file_text:
        return None, "Template 'credits' non trovato nella pagina dell'immagine"

    num_artists = len(artist_names)

    if num_artists == 0:
        return None, "Nessun artista trovato nel dump"

    # Costruisce la stringa artist da inserire
    if num_artists == 1 and artistalt:
        artist_insert = f"artist={artist_names[0]}|artistalt={artistalt}"
    else:
        artist_insert = _format_artist_insert(artist_names)

    # --- Caso B: artist=[[nome]] gia' compilato con wikilink ---
    bracket_match = re.search(
        r"\{\{credits\s*\|artist\s*=\s*\[\[([^\]|]+)(?:\|[^\]]+)?\]\]",
        file_text,
    )
    if bracket_match:
        # Conserva i parametri di provenienza ancora in uso (other non lo e'
        # piu': non viene ne' copiato ne' aggiunto).
        extra_params = ""
        for param_name in ("sourcesite", "sourcelink", "sourcetext"):
            pattern = (
                r"\{\{credits\s*\|[^}]*\|"
                + re.escape(param_name)
                + r"\s*=\s*([^|}\n]+)"
            )
            m = re.search(pattern, file_text)
            if m:
                extra_params += f"|{param_name}={m.group(1).strip()}"

        replacement = (
            f"{{{{credits|{artist_insert}"
            f"|cardartist=tcgpocket"
            f"{extra_params}}}}}"
        )

        new_text = re.sub(
            r"\{\{credits\s*\|[^}]*\}\}",
            replacement,
            file_text,
            count=1,
        )
        return new_text, None

    # --- Caso A1: artist gia' compilato senza wikilink ---
    already = compiled_artists(credits_params(file_text))
    if already:
        return None, (
            f"Il parametro 'artist' e' gia' compilato (senza wikilink): "
            f"'{' / '.join(already)}'"
        )

    # --- Caso C: template SENZA parametro artist ---
    # Le pagine File non compilate possono avere solo sourcesite=/ep= (o altri
    # parametri): il parametro artist manca del tutto e va inserito subito
    # dopo {{credits|, conservando tutti i parametri esistenti.
    credits_match = re.search(r"\{\{credits\s*\|([^}]*)\}\}", file_text)
    if credits_match and not re.search(
        r"(?:^|\|)\s*artist\s*=", credits_match.group(1)
    ):
        new_text = re.sub(
            r"\{\{credits\s*\|",
            f"{{{{credits|{artist_insert}|cardartist=tcgpocket|",
            file_text,
            count=1,
        )
        return new_text, None

    # --- Caso A: artist vuoto, con o senza altri parametri ---
    # Forme presenti su PCW: {{credits|artist=}} e {{credits|artist=|sourcesite=...}}.
    found = re.search(r"\{\{credits\s*\|artist\s*=\s*(\||\}\})", file_text)
    if not found:
        return None, (
            "Formato del template 'credits' non riconosciuto "
            "(attesi: {{credits|artist=...}}, {{credits|artist=}} "
            "o {{credits|sourcesite=...}} senza artist)"
        )

    # Se dopo artist= c'e' un altro parametro il separatore resta,
    # altrimenti si chiude subito il template.
    tail = "|" if found.group(1) == "|" else "}}"
    new_text = (
        file_text[: found.start()]
        + f"{{{{credits|{artist_insert}|cardartist=tcgpocket{tail}"
        + file_text[found.end():]
    )

    return new_text, None


# ======================================================================
#  PAGINE CARTA ED ESPANSIONI
# ======================================================================


def extract_card_titles_from_expansion(expansion_text):
    """
    Dall'wikitext della pagina di un'espansione GCC Pocket, estrae i titoli
    delle pagine di TUTTE le carte elencate (regolari + segrete).

    Cerca i template {{setlist/entry|...}} nella sezione "Elenco delle carte".
    Per ogni entry:
      - il secondo parametro contiene {{GCC ID|Set|Nome|Numero}}
        che costruisce il titolo pagina come "Nome (Set Numero)"

    Restituisce una lista di titoli di pagine carta.
    """
    templates = pywikibot.textlib.extract_templates_and_params(expansion_text)

    card_titles = []

    for tmpl_name, params in templates:
        clean = tmpl_name.strip().lower()
        if clean.startswith("template:"):
            clean = clean[9:]

        if clean != "setlist/entry":
            continue

        gcc_raw = params.get("2", "").strip()
        if not gcc_raw:
            continue

        gcc_templates = pywikibot.textlib.extract_templates_and_params(gcc_raw)
        for gcc_name, gcc_params in gcc_templates:
            gcc_clean = gcc_name.strip().lower()
            if gcc_clean.startswith("template:"):
                gcc_clean = gcc_clean[9:]
            if gcc_clean not in ("gcc id", "gccid"):
                continue

            set_name = gcc_params.get("1", "").strip()
            card_name = gcc_params.get("2", "").strip()
            card_num = gcc_params.get("3", "").strip()

            if set_name and card_name and card_num:
                title = f"{card_name} ({set_name} {card_num})"
                card_titles.append(title)
            break

    return card_titles


def resolve_and_deduplicate(site, card_titles):
    """
    Segue i redirect di ogni titolo carta e deduplica per pagina risolta.

    Restituisce un dizionario: {resolved_title: [original_title, ...]}
    dove resolved_title e' il titolo della pagina effettiva (dopo redirect)
    e la lista contiene i titoli originali che puntano ad essa.
    """
    resolved_map = {}

    for title in card_titles:
        page = pywikibot.Page(site, title)

        if page.isRedirectPage():
            target = page.getRedirectTarget()
            resolved = target.title()
        else:
            resolved = title

        if resolved not in resolved_map:
            resolved_map[resolved] = []
        resolved_map[resolved].append(title)

    return resolved_map


def process_card_page(site, card_title, dump, expansion_name=None):
    """
    Elabora una singola pagina carta: per ogni variante ricava l'artista dal
    dump e restituisce una lista di modifiche da applicare.

    Per artista singolo: se l'artista ha una pagina "Nome (illustratore)" su PCW,
    compila il template con artist=Nome (illustratore) e artistalt=Nome.

    Per doppio artista: compila con artist=Nome1|artist2=Nome2 (senza artistalt).
    """
    card_page = pywikibot.Page(site, card_title)
    if not card_page.exists():
        return [], [f"Pagina '{card_title}' non esiste."]

    variants = extract_variants(card_page.text)
    if not variants:
        return [], [f"Nessuna immagine trovata nell'infobox di '{card_title}'."]

    if expansion_name:
        variants = [
            variant
            for variant in variants
            if variant_in_expansion(variant, expansion_name)
        ]
        if not variants:
            return [], [
                f"Nessuna immagine dell'espansione '{expansion_name}' "
                f"nell'infobox di '{card_title}'."
            ]

    page_name = card_title.split(" (")[0]
    modifiche = []
    warnings = []

    for variant in variants:
        img_file = variant["image"]

        code, number, source, artist_names, warning = resolve_variant(
            variant, dump, page_name
        )
        if warning:
            warnings.append(f"  [{card_title}] '{img_file}': {warning}.")
        if not artist_names:
            warnings.append(
                f"  [{card_title}] '{img_file}': artista non ricavabile dal dump."
            )
            continue

        file_page = pywikibot.FilePage(site, img_file)
        if not file_page.exists():
            warnings.append(
                f"  [{card_title}] '{img_file}': la pagina File: non esiste."
            )
            continue

        # Se il template e' gia' compilato (senza wikilink) non lo si tocca:
        # si segnala solo quando il nome scritto non e' quello del dump.
        current_params = credits_params(file_page.text)
        current = compiled_artists(current_params)
        if current and "[[" not in (current_params.get("artist") or ""):
            if [normalize_name(name) for name in current] != [
                normalize_name(name) for name in artist_names
            ]:
                warnings.append(
                    f"  [{card_title}] '{img_file}': artista gia' compilato "
                    f"'{' / '.join(current)}' diverso dal dump "
                    f"('{' / '.join(artist_names)}'), lasciato invariato."
                )
            continue

        # Determina artistalt SOLO per singolo artista
        artistalt = None
        illustratore_suffix = " (illustratore)"
        final_artist_names = list(artist_names)  # copia

        if len(artist_names) == 1:
            name = artist_names[0]
            # Se il nome gia' termina con " (illustratore)"
            if name.lower().endswith(illustratore_suffix.lower()):
                base_name = name[: -len(illustratore_suffix)]
                artistalt = base_name
            else:
                page_ill = pywikibot.Page(site, name + illustratore_suffix)
                if page_ill.exists():
                    artistalt = name
                    final_artist_names[0] = name + illustratore_suffix

        new_text, error = update_credits_template(
            file_page.text, final_artist_names, artistalt
        )
        if error:
            warnings.append(f"  [{card_title}] '{img_file}': {error}")
            continue

        modifiche.append(
            (file_page, new_text, final_artist_names, artistalt, code, number, source)
        )

    return modifiche, warnings


# ======================================================================
#  MODALITA' DI VERIFICA (--check)
# ======================================================================


def check_credits_template(file_text, expected_artist_names, artistalt_expected=None):
    """
    Verifica che il template {{credits}} in una pagina File sia compilato
    correttamente, cioe' con i nomi degli artisti del dump.

    Per singolo artista atteso: verifica artist e opzionalmente artistalt.
    Per doppio artista atteso:  verifica artist e artist2.

    Restituisce:
      (True, messaggio_ok) se tutto corretto
      (False, messaggio_errore) altrimenti
    """
    if "{{credits" not in file_text:
        return False, "Template 'credits' non presente nella pagina File"

    params = credits_params(file_text)
    if not params:
        return False, "Template 'credits' non trovato (formato non riconosciuto)"

    num_expected = len(expected_artist_names)

    # Verifica artist
    artist_val = params.get('artist', '')
    if not artist_val:
        return False, "Parametro 'artist' assente o vuoto"

    # Verifica cardartist
    cardartist_val = params.get('cardartist', '').lower()
    if cardartist_val != 'tcgpocket':
        return False, (
            f"Parametro 'cardartist' assente o errato: "
            f"'{cardartist_val}' (atteso: tcgpocket)"
        )

    # Verifica che i nomi scritti siano quelli del dump (artist + artist2)
    compiled = compiled_artists(params)
    if [normalize_name(name) for name in compiled] != [
        normalize_name(name) for name in expected_artist_names
    ]:
        return False, (
            f"Artista errato: '{' / '.join(compiled)}' "
            f"(atteso dal dump: '{' / '.join(expected_artist_names)}')"
        )

    if num_expected == 1:
        # Verifica artistalt (opzionale se atteso)
        if artistalt_expected:
            artistalt_val = params.get('artistalt', '').strip()
            if not artistalt_val:
                return False, (
                    f"Parametro 'artistalt' assente "
                    f"(atteso: '{artistalt_expected}')"
                )
            if artistalt_val.lower() != artistalt_expected.lower():
                return False, (
                    f"Parametro 'artistalt' errato: '{artistalt_val}' "
                    f"(atteso: '{artistalt_expected}')"
                )

    return True, "OK: tutti i parametri compilati correttamente"


def check_card_page(site, card_title, dump, expansion_name=None):
    """
    Verifica che tutte le pagine File di una carta abbiano il template credits
    compilato con l'artista del dump.

    Restituisce (risultati, warnings) dove risultati e' una lista di tuple:
      (file_title, card_title, status, messaggio)
    con status=True/False.
    """
    card_page = pywikibot.Page(site, card_title)
    if not card_page.exists():
        return [], [f"Pagina '{card_title}' non esiste."]

    variants = extract_variants(card_page.text)
    if not variants:
        return [], [f"Nessuna immagine trovata nell'infobox di '{card_title}'."]

    if expansion_name:
        variants = [
            variant
            for variant in variants
            if variant_in_expansion(variant, expansion_name)
        ]
        if not variants:
            return [], [
                f"Nessuna immagine dell'espansione '{expansion_name}' "
                f"nell'infobox di '{card_title}'."
            ]

    page_name = card_title.split(" (")[0]
    risultati = []
    warnings = []

    for variant in variants:
        img_file = variant["image"]

        code, number, source, artist_names, warning = resolve_variant(
            variant, dump, page_name
        )
        if warning:
            warnings.append(f"  [{card_title}] '{img_file}': {warning}.")
        if not artist_names:
            warnings.append(
                f"  [{card_title}] '{img_file}': artista non ricavabile dal dump."
            )
            risultati.append(
                (img_file, card_title, False, "Artista non ricavabile dal dump")
            )
            continue

        file_page = pywikibot.FilePage(site, img_file)
        if not file_page.exists():
            warnings.append(
                f"  [{card_title}] '{img_file}': la pagina File: non esiste."
            )
            risultati.append(
                (img_file, card_title, False, "Pagina File non esistente")
            )
            continue

        # Determina se ci si aspetta artistalt (solo per singolo artista)
        artistalt_expected = None
        if len(artist_names) == 1:
            page_ill = pywikibot.Page(site, artist_names[0] + " (illustratore)")
            if page_ill.exists():
                artistalt_expected = artist_names[0]

        ok, msg = check_credits_template(
            file_page.text, artist_names, artistalt_expected
        )
        risultati.append((img_file, card_title, ok, msg))

    return risultati, warnings


# ======================================================================
#  MAIN
# ======================================================================


def main():
    # --- Parametri da riga di comando ---
    check_mode = False
    dump_dir = DUMP_DIR
    args = list(sys.argv[1:])

    rest = []
    position = 0
    while position < len(args):
        arg = args[position]
        if arg == "--check":
            check_mode = True
            position += 1
        elif arg == "--dump":
            if position + 1 >= len(args):
                print("ERRORE: --dump richiede una cartella.")
                sys.exit(1)
            dump_dir = args[position + 1]
            position += 2
        elif arg in ("-h", "--help"):
            print(__doc__)
            return
        else:
            rest.append(arg)
            position += 1

    # --- Input interattivo o da riga di comando ---
    if len(rest) == 3:
        fam, lang, input_title = rest
    else:
        fam = input("Famiglia (fam): ").strip()
        lang = input("Lingua (lang): ").strip()
        input_title = input("Pagina della carta o nome espansione: ").strip()

    if not fam or not lang or not input_title:
        print("ERRORE: tutti i parametri (fam, lang, titolo) sono obbligatori.")
        sys.exit(1)

    # --- Connessione al sito ---
    site = pywikibot.Site(lang, fam)
    if not check_mode:
        # pywikibot ha rinominato setDelays in set_delays (10.3.0)
        set_delays = getattr(site.throttle, "set_delays", None)
        if set_delays:
            set_delays(writedelay=1.0)
        else:
            site.throttle.setDelays(writedelay=1.0)
    print(f"Connesso a: {site}")

    # --- Codici delle espansioni (dal modulo del wiki) e dump di gioco ---
    load_expansion_names(site)
    dump = load_dump(dump_dir)
    print(f"Dump: {len(dump)} carte lette da {dump_dir}")

    # --- Auto-riconoscimento: carta singola o espansione? ---
    is_single_card = bool(re.search(r"\([^)]+ \d+\)$", input_title))

    if is_single_card:
        print(f"Modalita': carta singola -> {input_title}")
        expansion_name = None
        resolved_map = {input_title: [input_title]}
    else:
        expansion_name = input_title
        expansion_page_title = f"{input_title} (GCC Pocket)"
        print(f"Modalita': espansione -> {expansion_page_title}")

        expansion_page = pywikibot.Page(site, expansion_page_title)
        if not expansion_page.exists():
            print(
                f"ERRORE: la pagina dell'espansione "
                f"'{expansion_page_title}' non esiste."
            )
            sys.exit(1)

        card_titles = extract_card_titles_from_expansion(expansion_page.text)
        if not card_titles:
            print("ERRORE: nessuna carta trovata nell'elenco dell'espansione.")
            sys.exit(1)

        print(
            f"Trovate {len(card_titles)} carte nell'elenco "
            f"(regolari + segrete)."
        )

        resolved_map = resolve_and_deduplicate(site, card_titles)
        redirect_count = len(card_titles) - len(resolved_map)
        if redirect_count > 0:
            print(
                f"Dopo risoluzione redirect: {len(resolved_map)} pagine uniche "
                f"({redirect_count} redirect assorbiti)."
            )

    # ================================================================
    #  MODALITA' DI VERIFICA
    # ================================================================
    if check_mode:
        print("\n" + "=" * 60)
        print("MODALITA' DI VERIFICA (nessuna scrittura)")
        print("=" * 60)

        total_pages = len(resolved_map)
        processed = 0
        all_risultati = []
        all_warnings = []

        for resolved_title, original_titles in resolved_map.items():
            processed += 1

            if not is_single_card and len(original_titles) > 1:
                print(
                    f"[{processed}/{total_pages}] -> '{resolved_title}' "
                    f"(raggiunta da {len(original_titles)} voci setlist)"
                )
            else:
                print(
                    f"\r[{processed}/{total_pages}] '{resolved_title}'...",
                    end=""
                )

            risultati, warnings = check_card_page(
                site, resolved_title, dump, expansion_name
            )
            all_risultati.extend(risultati)
            all_warnings.extend(warnings)

        print()

        # --- Riepilogo ---
        print("\n" + "=" * 60)
        print("RIEPILOGO VERIFICA")
        print("=" * 60)

        ok_files = [r for r in all_risultati if r[2]]
        ko_files = [r for r in all_risultati if not r[2]]

        print(f"\nFile verificati: {len(all_risultati)}")
        print(f"  [OK] Compilati correttamente: {len(ok_files)}")
        print(f"  [KO] Non compilati o errati: {len(ko_files)}")

        if ko_files:
            print("\n--- DETTAGLIO FILE NON COMPILATI ---")
            for img_file, card_title, ok, msg in ko_files:
                print(f"\n  File: {img_file}")
                print(f"  Carta: {card_title}")
                print(f"  Problema: {msg}")

        if ok_files and not ko_files:
            print("\n[OK] TUTTE LE CARTE SONO COMPILATE CORRETTAMENTE!")
            print("  Nessun intervento necessario.")

        if all_warnings:
            print(f"\n[!] {len(all_warnings)} avvisi:")
            for w in all_warnings:
                print(w)

        return

    # ================================================================
    #  MODALITA' DI SCRITTURA
    # ================================================================
    all_modifiche = []
    all_warnings = []
    processed = 0
    total_pages = len(resolved_map)

    for resolved_title, original_titles in resolved_map.items():
        processed += 1

        if not is_single_card and len(original_titles) > 1:
            print(
                f"[{processed}/{total_pages}] -> '{resolved_title}' "
                f"elaborata una volta "
                f"(raggiunta da {len(original_titles)} voci setlist)"
            )
        else:
            print(
                f"\r[{processed}/{total_pages}] elaborazione in corso...",
                end=""
            )

        modifiche, warnings = process_card_page(
            site, resolved_title, dump, expansion_name
        )
        all_modifiche.extend(modifiche)
        all_warnings.extend(warnings)

    print()

    if not all_modifiche:
        print("Nessuna modifica da fare.")
        if all_warnings:
            print(f"\n[!] {len(all_warnings)} avvisi:")
            for w in all_warnings:
                print(w)
        return

    # --- Anteprima ---
    print("\n" + "=" * 60)
    print(f"ANTEPRIMA MODIFICHE")
    print("=" * 60)

    for i, modifica in enumerate(all_modifiche):
        file_page, new_text, artist_names, artistalt, code, number, source = modifica
        if i > 0:
            print()
        print(f"--- {file_page.title()} ---")
        if len(artist_names) == 1:
            if artistalt:
                print(f"    Artista: {artist_names[0]}  (artistalt: {artistalt})")
            else:
                print(f"    Artista: {artist_names[0]}")
        else:
            print(f"    Artisti: {' + '.join(artist_names)}")
        print(f"    Carta nel dump: {code} {number} (da {source})")
        print(new_text)

    print("=" * 60)

    # --- Avvisi ---
    if all_warnings:
        print(f"\n[!] {len(all_warnings)} avvisi:")
        for w in all_warnings:
            print(w)

    # --- Riepilogo e conferma ---
    print(
        f"\nRiepilogo: {total_pages} pagine elaborate, "
        f"{len(all_modifiche)} file da aggiornare."
    )
    confirm = input("\nSalvare tutte le modifiche? (s/n): ").strip().lower()
    if confirm != "s":
        print("Operazione annullata.")
        return

    # --- Salvataggio ---
    for modifica in all_modifiche:
        file_page, new_text, artist_names, artistalt, code, number, source = modifica
        file_page.text = new_text
        if len(artist_names) == 1:
            if artistalt:
                summary_artist = artistalt
            else:
                summary_artist = artist_names[0].replace(" (illustratore)", "")
        else:
            summary_artist = " e ".join(
                a.replace(" (illustratore)", "") for a in artist_names
            )
        file_page.save(
            summary=(
                f"Bot: Aggiunto artista ({summary_artist}) "
                f"e cardartist=tcgpocket"
            )
        )
        print(f"  [OK] {file_page.title()} salvata.")

    print(f"\n[OK] {len(all_modifiche)} pagine aggiornate con successo!")


if __name__ == "__main__":
    main()
