#!/usr/bin/env python3
"""
Compila il template {{credits}} nella pagina File: di una carta PCW.
Riceve in input fam, lang e:
  a) il titolo di una pagina carta (Pokémon o Allenatore) -> elabora quella carta
  b) il nome di un'espansione GCC Pocket -> elabora TUTTE le carte
     dell'espansione (regolari + segrete/ultrarare).

Per ogni carta estrae immagine e artista di TUTTE le varianti (originale + ristampe)
dal template PokemoncardInfobox o GCCCartaTrainerInfobox, e compila i parametri
artist e cardartist in ciascuna pagina File: corrispondente.

In modalita' espansione, le carte segrete vengono risolte seguendo i redirect:
  - redirect nella STESSA espansione -> ignorato (la carta base ha gia' il reprint)
  - redirect in un'ALTRA espansione -> il file viene cercato tra i reprint
    dell'infobox della carta target, filtrando per nome espansione

L'auto-riconoscimento della modalita' avviene tramite pattern: se il titolo
contiene "(NomeSet Numero)" viene trattato come carta singola, altrimenti
come nome espansione (la pagina cercata sara' "NomeEspansione (GCC Pocket)").

Gestisce due casi nel template credits:
  a) {{credits|artist=|other=...}}   ->  aggiunge artist e cardartist, mantiene other
  b) {{credits|artist=[[nome]]}}     ->  sostituisce artist con nome pulito,
                                         aggiunge cardartist, mantiene other se presente

DIPENDENZE:
  - Python 3.6+
  - pywikibot (pip install pywikibot)
  - user-config.py configurato per pokemoncentral (it)

ESEMPI D'USO
  Interattivo (i parametri vengono chiesti a schermo):
      $ python compila_credits.py

  Carta singola (da riga di comando):
      $ python compila_credits.py pokemoncentral it "Surskit (Assalto dei Paradossi 1)"
      $ python compila_credits.py pokemoncentral it "Lunaruggente (Assalto dei Paradossi 47)"
      $ python compila_credits.py pokemoncentral it "Professor Turum (Assalto dei Paradossi 73)"

  Espansione (da riga di comando):
      $ python compila_credits.py pokemoncentral it "Assalto dei Paradossi"
      $ python compila_credits.py pokemoncentral it "Aura Pulsante"
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
    (image_file, artist_name) per l'originale e tutte le ristampe.

    Restituisce una lista di tuple: [(image_file, artist_name), ...]
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
            artist_name = None
            for key, val in params.items():
                k = key.strip().lower()
                v = val.strip()
                if k == "image":
                    image_file = v
                elif k == "caption":
                    m = re.search(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", v)
                    if m:
                        artist_name = m.group(1).strip()

            if image_file:
                pairs.append((image_file, artist_name or ""))

            for i in range(1, reprint_count):
                r_image = None
                r_artist = None
                r_key_img = f"reprint{i}"
                r_key_cap = f"recaption{i}"
                for key, val in params.items():
                    k = key.strip().lower()
                    v = val.strip()
                    if k == r_key_img:
                        r_image = v
                    elif k == r_key_cap:
                        m = re.search(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", v)
                        if m:
                            r_artist = m.group(1).strip()

                if r_image:
                    pairs.append((r_image, r_artist or ""))

            break

    return pairs


def update_credits_template(file_text, artist_name):
    """
    Sostituisce il template {{credits}} nella pagina dell'immagine.

    Due casi:
      a) artist e' vuoto (artist=|) e c'e' other=...
         -> aggiunge artist e cardartist, conserva other
         -> "{{credits|artist=NOME|cardartist=tcgpocket|other=...}}"

      b) artist contiene un wikilink (artist=[[nome]])
         -> sostituisce artist con il nome pulito, aggiunge cardartist,
           conserva other (se presente) con il suo valore originale
         -> "{{credits|artist=NOME|cardartist=tcgpocket}}"           (senza other)
         -> "{{credits|artist=NOME|cardartist=tcgpocket|other=XXX}}" (con other)

    Restituisce (nuovo_testo, errore).
    """
    if "{{credits" not in file_text:
        return None, "Template 'credits' non trovato nella pagina dell'immagine"

    bracket_match = re.search(
        r"\{\{credits\s*\|artist\s*=\s*\[\[([^\]|]+)(?:\|[^\]]+)?\]\]",
        file_text,
    )
    if bracket_match:
        other_match = re.search(
            r"\{\{credits\s*\|[^}]*\|other\s*=\s*([^|}\n]+)",
            file_text,
        )
        if other_match:
            other_val = other_match.group(1).strip()
            replacement = (
                f"{{{{credits|artist={artist_name}"
                f"|cardartist=tcgpocket"
                f"|other={other_val}}}}}"
            )
        else:
            replacement = (
                f"{{{{credits|artist={artist_name}"
                f"|cardartist=tcgpocket}}}}"
            )

        new_text = re.sub(
            r"\{\{credits\s*\|[^}]*\}\}",
            replacement,
            file_text,
            count=1,
        )
        return new_text, None

    already = re.search(r"\{\{credits\s*\|[^}]*\|artist=([^|}\n]+)", file_text)
    if already and already.group(1).strip():
        return None, (
            f"Il parametro 'artist' e' gia' compilato (senza wikilink): "
            f"'{already.group(1).strip()}'"
        )

    pattern = r"\{\{credits\s*\|artist\s*=\s*\|"
    if not re.search(pattern, file_text):
        return None, (
            "Formato del template 'credits' non riconosciuto "
            "(atteso: {{credits|artist=|other=...}})"
        )

    new_text = re.sub(
        pattern,
        f"{{{{credits|artist={artist_name}|cardartist=tcgpocket|",
        file_text,
        count=1,
    )

    return new_text, None


def extract_card_titles_from_expansion(expansion_text):
    """
    Dall'wikitext della pagina di un'espansione GCC Pocket, estrae i titoli
    delle pagine di TUTTE le carte elencate (regolari + segrete/ultrarare).

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
    Filtra le coppie (image_file, artist_name) mantenendo solo quelle
    il cui nome file contiene il nome dell'espansione (senza spazi).

    Es. expansion_name="Assalto dei Paradossi" -> cerca "AssaltodeiParadossi"
    """
    expansion_key = expansion_name.replace(" ", "")
    return [
        (img, art)
        for img, art in pairs
        if expansion_key.lower() in img.lower()
    ]


def process_card_page(site, card_title, expansion_name=None):
    """
    Elabora una singola pagina carta: estrae le coppie (immagine, artista)
    e restituisce una lista di modifiche da applicare.

    Se expansion_name e' specificato, filtra le coppie per espansione.

    Restituisce (modifiche, warnings).
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

    for img_file, artist_name in pairs:
        if not artist_name:
            warnings.append(
                f"  [{card_title}] '{img_file}': artista non trovato nel caption."
            )
            continue

        file_page = pywikibot.FilePage(site, img_file)
        if not file_page.exists():
            warnings.append(
                f"  [{card_title}] '{img_file}': la pagina File: non esiste."
            )
            continue

        new_text, error = update_credits_template(file_page.text, artist_name)
        if error:
            warnings.append(f"  [{card_title}] '{img_file}': {error}")
            continue

        modifiche.append((file_page, new_text, artist_name))

    return modifiche, warnings


def main():
    # --- Input interattivo o da riga di comando ---
    if len(sys.argv) == 4:
        fam = sys.argv[1]
        lang = sys.argv[2]
        input_title = sys.argv[3]
    else:
        fam = input("Famiglia (fam): ").strip()
        lang = input("Lingua (lang): ").strip()
        input_title = input("Pagina della carta o nome espansione: ").strip()

    if not fam or not lang or not input_title:
        print("ERRORE: tutti i parametri (fam, lang, titolo) sono obbligatori.")
        sys.exit(1)

    # --- Connessione al sito ---
    site = pywikibot.Site(lang, fam)
    site.throttle.setDelays(writedelay=3.0)  # 3 secondi tra un edit e l'altro
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
                f"ERRORE: la pagina dell'espansione '{expansion_page_title}' "
                f"non esiste."
            )
            sys.exit(1)

        card_titles = extract_card_titles_from_expansion(expansion_page.text)
        if not card_titles:
            print("ERRORE: nessuna carta trovata nell'elenco dell'espansione.")
            sys.exit(1)

        print(
            f"Trovate {len(card_titles)} carte nell'elenco "
            f"(regolari + segrete/ultrarare)."
        )

        resolved_map = resolve_and_deduplicate(site, card_titles)
        redirect_count = len(card_titles) - len(resolved_map)
        if redirect_count > 0:
            print(
                f"Dopo risoluzione redirect: {len(resolved_map)} pagine uniche "
                f"({redirect_count} redirect assorbiti)."
            )

    # --- Elabora tutte le carte, mostrando dettagli durante il processo ---
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
            print(f"\r[{processed}/{total_pages}] elaborazione in corso...", end="")

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

    for i, (file_page, new_text, artist_name) in enumerate(all_modifiche):
        if i > 0:
            print()
        print(f"--- {file_page.title()} ---")
        print(f"    Artista: {artist_name}")
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
    for file_page, new_text, artist_name in all_modifiche:
        file_page.text = new_text
        file_page.save(
            summary=f"Bot: Aggiunto artista ({artist_name}) e cardartist=tcgpocket"
        )
        print(f"  [OK] {file_page.title()} salvata.")

    print(f"\n[OK] {len(all_modifiche)} pagine aggiornate con successo!")


if __name__ == "__main__":
    main()
