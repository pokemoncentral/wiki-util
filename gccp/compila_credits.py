#!/usr/bin/env python3
"""
Compila il template {{credits}} nella pagina File: di una carta PCW.
Riceve in input fam, lang e:
  a) il titolo di una pagina carta (Pokémon o Allenatore) -> elabora quella carta
  b) il nome di un'espansione GCC Pocket -> elabora TUTTE le carte
     dell'espansione (regolari + segrete).

Per ogni carta estrae immagine e artista di TUTTE le varianti (originale + ristampe)
dal template PokemoncardInfobox o GCCCartaTrainerInfobox, e compila i parametri
artist e cardartist in ciascuna pagina File: corrispondente.

Supporta carte con DOPPIO ARTISTA: se la caption contiene "[[Nome1]]/[[Nome2]]",
compila il credits come |artist=Nome1|artist2=Nome2.

In modalita' espansione, le carte segrete vengono risolte seguendo i redirect:
  - redirect nella STESSA espansione -> ignorato (la carta base ha gia' il reprint)
  - redirect in un'ALTRA espansione -> il file viene cercato tra i reprint
    dell'infobox della carta target, filtrando per nome espansione

L'auto-riconoscimento della modalita' avviene tramite pattern: se il titolo
contiene "(NomeSet Numero)" viene trattato come carta singola, altrimenti
come nome espansione (la pagina cercata sara' "NomeEspansione (GCC Pocket)").

Gestisce il template credits in TUTTI i formati presenti su PCW:
  - {{credits|other=...}}                     -> inserisce artist e cardartist
                                                 (parametro artist assente)
  - {{credits|artist=|other=...}}             -> aggiunge artist e cardartist
  - {{credits|artist=[[nome]]}}               -> sostituisce con nome pulito
  - {{credits|artist=Nome|cardartist=...}}    -> gia' compilato, non tocca

Doppio artista                                -> |artist=Nome1|artist2=Nome2

Se l'artista ha una pagina PCW "Nome (illustratore)", il template viene compilato con
artist=Nome (illustratore) e artistalt=Nome (solo per singolo artista).

MODALITA' DI VERIFICA (--check):
  Invece di scrivere, controlla che i template {{credits}} delle carte
  siano compilati correttamente (artist + cardartist, ed eventualmente artist2).
  Stampa un riepilogo con l'elenco delle carte OK e di quelle non compilate.

DIPENDENZE:
  - Python 3.6+
  - pywikibot (pip install pywikibot)
  - user-config.py configurato per pokemoncentral (it)

ESEMPI D'USO
  Interattivo:
      $ python compila_credits.py

  Carta singola (doppio artista):
      $ python compila_credits.py pokemoncentral it "Camelia (Giorni Giocondi 66)"

  Espansione:
      $ python compila_credits.py pokemoncentral it "Giorni Giocondi"

  Verifica carta singola:
      $ python compila_credits.py --check pokemoncentral it "Camelia (Giorni Giocondi 66)"

  Verifica espansione:
      $ python compila_credits.py --check pokemoncentral it "Giorni Giocondi"
"""

import pywikibot
import re
import sys


# Template infobox riconosciuti (case-insensitive)
INFOBOX_NAMES = {
    "pokémoncardinfobox",
    "pokemoncardinfobox",
    "gcccartatrainerinfobox",
}


def extract_card_info(card_text):
    """
    Dal wikitext di una pagina carta (Pokemon o Allenatore), estrae le coppie
    (image_file, artist_names) per l'originale e tutte le ristampe.

    artist_names e' una LISTA di nomi (1 o 2 elementi):
      - 1 elemento: artista singolo (es. ['Ken Sugimori'])
      - 2 elementi: doppio artista (es. ['Nobusawa', 'Mochipuyo'])

    Restituisce una lista di tuple: [(image_file, [artist_names...]), ...]
    dove il primo elemento e' l'originale (da image/caption),
    gli eventuali successivi sono le ristampe (da reprint{i}/recaption{i}).

    Il parametro reprint=N indica N varianti totali (originale + N-1 ristampe).
    Le ristampe hanno chiavi reprint1, recaption1, reprint2, recaption2, ecc.
    """
    templates = pywikibot.textlib.extract_templates_and_params(card_text)

    pairs = []
    reprint_count = 1  # default: solo originale

    for tmpl_name, params in templates:
        clean = tmpl_name.strip().lower()
        if clean.startswith("template:"):
            clean = clean[9:]

        if clean in INFOBOX_NAMES:
            for key, val in params.items():
                if key.strip().lower() == "reprint":
                    try:
                        reprint_count = int(val.strip())
                    except ValueError:
                        pass
                    break

            image_file = None
            artist_names = []
            for key, val in params.items():
                k = key.strip().lower()
                v = val.strip()
                if k == "image":
                    image_file = v
                elif k == "caption":
                    # Estrai TUTTI i wikilink dal caption
                    # Formato singolo: Ill. [[Nome]]
                    # Formato doppio:  Ill. [[Nome1]]/[[Nome2]]
                    names = re.findall(
                        r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", v
                    )
                    artist_names = [n.strip() for n in names]

            if image_file:
                pairs.append((image_file, artist_names))

            for i in range(1, reprint_count):
                r_image = None
                r_artists = []
                r_key_img = f"reprint{i}"
                r_key_cap = f"recaption{i}"
                for key, val in params.items():
                    k = key.strip().lower()
                    v = val.strip()
                    if k == r_key_img:
                        r_image = v
                    elif k == r_key_cap:
                        names = re.findall(
                            r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", v
                        )
                        r_artists = [n.strip() for n in names]

                if r_image:
                    pairs.append((r_image, r_artists))

            break

    return pairs


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
      A) {{credits|artist=|other=...}}        -> riempie artist (vuoto)
      B) {{credits|artist=[[nome]]...}}       -> sostituisce il wikilink
      C) {{credits|other=...}}                -> INSERISCE artist ex-novo
         (formato delle pagine File non ancora compilate, es. upload)

    Restituisce (nuovo_testo, errore).
    """
    if "{{credits" not in file_text:
        return None, "Template 'credits' non trovato nella pagina dell'immagine"

    num_artists = len(artist_names)

    if num_artists == 0:
        return None, "Nessun artista trovato nella caption"

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
        # Estrae eventuali parametri aggiuntivi dal template originale
        extra_params = ""
        for param_name in ("other", "sourcesite", "sourcelink", "sourcetext"):
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
    already = re.search(r"\{\{credits\s*\|[^}]*\|artist=([^|}\n]+)", file_text)
    if already and already.group(1).strip():
        return None, (
            f"Il parametro 'artist' e' gia' compilato (senza wikilink): "
            f"'{already.group(1).strip()}'"
        )

    # --- Caso C: template SENZA parametro artist (es. {{credits|other=...}}) ---
    # Le pagine File non compilate hanno solo {{credits|other=...}} (o
    # sourcesite=/ep=): il parametro artist manca del tutto e va inserito
    # subito dopo {{credits|, conservando tutti i parametri esistenti.
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

    # --- Caso A: artist vuoto (artist=|) con other=... ---
    pattern = r"\{\{credits\s*\|artist\s*=\s*\|"
    if not re.search(pattern, file_text):
        return None, (
            "Formato del template 'credits' non riconosciuto "
            "(attesi: {{credits|other=...}}, {{credits|artist=|other=...}} "
            "o {{credits|artist=[[nome]]}})"
        )

    new_text = re.sub(
        pattern,
        f"{{{{credits|{artist_insert}|cardartist=tcgpocket|",
        file_text,
        count=1,
    )

    return new_text, None


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


def filter_pairs_by_expansion(pairs, expansion_name):
    """
    Filtra le coppie (image_file, artist_names) mantenendo solo quelle
    il cui nome file contiene il nome dell'espansione (senza spazi e apostrofi).

    Es. expansion_name="L'Isola Misteriosa" -> cerca "LIsolaMisteriosa"
        expansion_name="Assalto dei Paradossi" -> cerca "AssaltodeiParadossi"
    """
    expansion_key = expansion_name.replace(" ", "").replace("'", "")
    return [
        (img, artists)
        for img, artists in pairs
        if expansion_key.lower() in img.lower()
    ]


def process_card_page(site, card_title, expansion_name=None):
    """
    Elabora una singola pagina carta: estrae le coppie (immagine, artisti)
    e restituisce una lista di modifiche da applicare.

    Per artista singolo: se l'artista ha una pagina "Nome (illustratore)" su PCW,
    compila il template con artist=Nome (illustratore) e artistalt=Nome.

    Per doppio artista: compila con artist=Nome1|artist2=Nome2 (senza artistalt).
    """
    card_page = pywikibot.Page(site, card_title)
    if not card_page.exists():
        return [], [f"Pagina '{card_title}' non esiste."]

    pairs = extract_card_info(card_page.text)
    if not pairs:
        return [], [f"Nessuna immagine trovata nell'infobox di '{card_title}'."]

    if expansion_name:
        pairs = filter_pairs_by_expansion(pairs, expansion_name)
        if not pairs:
            return [], [
                f"Nessuna immagine dell'espansione '{expansion_name}' "
                f"nell'infobox di '{card_title}'."
            ]

    modifiche = []
    warnings = []

    for img_file, artist_names in pairs:
        if not artist_names or len(artist_names) == 0:
            warnings.append(
                f"  [{card_title}] '{img_file}': artista/i non trovati nel caption."
            )
            continue

        file_page = pywikibot.FilePage(site, img_file)
        if not file_page.exists():
            warnings.append(
                f"  [{card_title}] '{img_file}': la pagina File: non esiste."
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
                base_name = name[:-len(illustratore_suffix)]
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

        modifiche.append((file_page, new_text, final_artist_names, artistalt))

    return modifiche, warnings


# ======================================================================
#  MODALITA' DI VERIFICA (--check)
# ======================================================================

def check_credits_template(file_text, expected_artist_names, artistalt_expected=None):
    """
    Verifica che il template {{credits}} in una pagina File sia compilato
    correttamente.

    Per singolo artista atteso: verifica artist e opzionalmente artistalt.
    Per doppio artista atteso:  verifica artist e artist2.

    Restituisce:
      (True, messaggio_ok) se tutto corretto
      (False, messaggio_errore) altrimenti
    """
    if "{{credits" not in file_text:
        return False, "Template 'credits' non presente nella pagina File"

    m = re.search(r"\{\{credits\s*\|([^}]*)\}\}", file_text)
    if not m:
        return False, "Template 'credits' non trovato (formato non riconosciuto)"

    params_text = m.group(1)

    # Estrai parametri dividendo sui | non annidati dentro [[ ]]
    params = {}
    parts = re.split(
        r'\s*\|\s*(?=(?:[^\]]*\[\[[^\]]*\]\])*[^\]]*$)',
        params_text
    )
    for part in parts:
        if '=' not in part:
            continue
        key, _, val = part.partition('=')
        key = key.strip().lower()
        val = val.strip()
        params[key] = val

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

    if num_expected == 1:
        # Verifica che artist2 NON sia presente (non atteso per singolo artista)
        artist2_val = params.get('artist2', '')
        if artist2_val:
            return False, (
                f"Parametro 'artist2' presente ma non atteso "
                f"(carta con artista singolo): artist2={artist2_val}"
            )

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

    elif num_expected == 2:
        # Verifica artist2
        artist2_val = params.get('artist2', '')
        if not artist2_val:
            return False, (
                f"Parametro 'artist2' assente o vuoto "
                f"(atteso secondo artista: '{expected_artist_names[1]}')"
            )

    return True, "OK: tutti i parametri compilati correttamente"


def check_card_page(site, card_title, expansion_name=None):
    """
    Verifica che tutte le pagine File di una carta abbiano il template credits
    compilato correttamente.

    Restituisce (risultati, warnings) dove risultati e' una lista di tuple:
      (file_title, card_title, status, messaggio)
    con status=True/False.
    """
    card_page = pywikibot.Page(site, card_title)
    if not card_page.exists():
        return [], [f"Pagina '{card_title}' non esiste."]

    pairs = extract_card_info(card_page.text)
    if not pairs:
        return [], [f"Nessuna immagine trovata nell'infobox di '{card_title}'."]

    if expansion_name:
        pairs = filter_pairs_by_expansion(pairs, expansion_name)
        if not pairs:
            return [], [
                f"Nessuna immagine dell'espansione '{expansion_name}' "
                f"nell'infobox di '{card_title}'."
            ]

    risultati = []
    warnings = []

    for img_file, artist_names in pairs:
        if not artist_names or len(artist_names) == 0:
            warnings.append(
                f"  [{card_title}] '{img_file}': artista/i non trovato nel caption."
            )
            risultati.append(
                (img_file, card_title, False, "Artista/i non trovato nel caption")
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
    # --- Riconoscimento parametro --check ---
    check_mode = False
    args = list(sys.argv)

    if '--check' in args:
        check_mode = True
        args.remove('--check')

    # --- Input interattivo o da riga di comando ---
    if len(args) == 4:
        fam = args[1]
        lang = args[2]
        input_title = args[3]
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
        site.throttle.setDelays(writedelay=1.0)
    print(f"Connesso a: {site}")

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
                site, resolved_title, expansion_name
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
            site, resolved_title, expansion_name
        )
        all_modifiche.extend(modifiche)
        all_warnings.extend(warnings)

    print()

    if not all_modifiche:
        print("Nessuna modifica da fare.")
        return

    # --- Anteprima ---
    print("\n" + "=" * 60)
    print(f"ANTEPRIMA MODIFICHE")
    print("=" * 60)

    for i, (file_page, new_text, artist_names, artistalt) in enumerate(
        all_modifiche
    ):
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
    for file_page, new_text, artist_names, artistalt in all_modifiche:
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
