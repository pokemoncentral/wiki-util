#!/usr/bin/env python3
"""
TCG Pocket Expansion Data Scraper
==================================
Prende in input il nome inglese di un'espansione del GCC Pocket,
si collega a una wiki (di default Bulbapedia EN) via Pywikibot,
e compila un file TXT con i dati giapponesi di tutte le carte,
incluse ristampe e secret rare, nell'ordine del set.

I redirect vengono risolti con getRedirectTarget() prima di
estrarre i dati dalla pagina effettiva.

Utilizzo:
    python tcgp_scraper.py "Paradox Drive"
    python tcgp_scraper.py "Deluxe Pack: ex"
    python tcgp_scraper.py "Paradox Drive" -o ./output/
    python tcgp_scraper.py "Paradox Drive" -fam pcw -lang it

Dipendenze:
    - pywikibot (family e lingua configurate)
"""

import sys
import os
import re
import argparse
import pywikibot
from pywikibot import textlib
from pywikibot.exceptions import NoPageError


EXPANSION_PAGE_SUFFIX = ' (TCG Pocket)'

INFOBOX_POKEMON = 'TCG Card Infobox/Pokémon/Pocket'
INFOBOX_TRAINER = 'TCG Card Infobox/Trainer/Pocket'
TPL_ABILITY    = 'Cardtext/Ability/Pocket'
TPL_ATTACK     = 'Cardtext/Attack/Pocket'
TPL_CARDDEX    = 'Carddex/Pocket'

# Caratteri vietati nei nomi file Windows: < > : " / \ | ? *
_INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def get_site(family, lang):
    return pywikibot.Site(lang, family)


def get_expansion_page(site, expansion_name):
    title = expansion_name + EXPANSION_PAGE_SUFFIX
    page = pywikibot.Page(site, title)
    if not page.exists():
        search_results = list(site.search(title, total=5))
        if search_results:
            raise ValueError(
                f"Pagina '{title}' non trovata.\n"
                f"Forse intendevi una di queste?\n  " +
                "\n  ".join(search_results)
            )
        raise ValueError(f"Pagina '{title}' non trovata.")
    return page


def extract_templates(text, template_name):
    all_templates = textlib.extract_templates_and_params(text)
    results = []
    for tmpl in all_templates:
        name = tmpl[0].strip()
        if name == template_name:
            params = {}
            for key, value in tmpl[1].items():
                params[key.strip()] = value.strip()
            results.append(params)
    return results


def extract_card_list_from_page(wikitext, expansion_name):
    """
    Estrae la lista COMPLETA delle carte dall'INTERA pagina.
    Cerca TUTTE le occorrenze, tiene la prima per numero, ordina.
    """
    escaped_exp = re.escape(expansion_name)
    pattern = re.compile(
        r'\{\{TCG\s+ID\|' + escaped_exp + r'\|([^}|]+)\|(\d+)'
    )

    seen = set()
    cards = []

    for m in pattern.finditer(wikitext):
        card_name = m.group(1).strip()
        number = int(m.group(2))

        if number in seen:
            continue
        seen.add(number)

        page_title = f"{card_name} ({expansion_name} {number})"
        cards.append((number, page_title, card_name))

    cards.sort(key=lambda entry: entry[0])
    return cards


def get_param_value(params, key):
    if key in params:
        val = params[key]
        return val if val else None
    return None


def clean_en_name(raw_name):
    if not raw_name:
        return None
    cleaned = re.sub(r'\{\{[^}]+\}\}', '', raw_name)
    return cleaned.strip()


_MAX_REDIRECT_DEPTH = 10


def resolve_page(site, page_title):
    """
    Risolve redirect (anche catene multiple) e restituisce (pagina_effettiva, wikitext).

    Segue la catena di redirect tramite page.isRedirectPage() + getRedirectTarget(),
    rimuovendo esplicitamente eventuali anchor (#Section) dal titolo target.
    Gestisce loop di redirect e un massimo di _MAX_REDIRECT_DEPTH livelli.
    """
    visited = set()
    page = pywikibot.Page(site, page_title)

    for _ in range(_MAX_REDIRECT_DEPTH):
        title = page.title()
        if title in visited:
            return None, None   # loop di redirect
        visited.add(title)

        try:
            wikitext = page.get(get_redirect=True)
        except NoPageError:
            return None, None
        except Exception:
            return None, None

        if page.isRedirectPage():
            try:
                target_page = page.getRedirectTarget()
                # Rimuovi eventuali anchor dal titolo
                target_title = target_page.title()
                if '#' in target_title:
                    target_title = target_title.split('#', 1)[0].strip()
                page = pywikibot.Page(site, target_title)
                continue
            except Exception:
                return None, None

        # Pagina reale trovata
        return page, wikitext

    # Superato il limite di redirect
    return None, None


def process_card_page(site, page_title):
    """
    Processa una carta, risolvendo redirect. Torna la tupla a 8 campi.
    """
    page, wikitext = resolve_page(site, page_title)
    if page is None or wikitext is None:
        return None

    infobox_pkmn = extract_templates(wikitext, INFOBOX_POKEMON)
    infobox_trainer = extract_templates(wikitext, INFOBOX_TRAINER)

    is_trainer = False
    if infobox_pkmn:
        infobox = infobox_pkmn[0]
    elif infobox_trainer:
        infobox = infobox_trainer[0]
        is_trainer = True
    else:
        return None

    en_name = clean_en_name(get_param_value(infobox, 'en name'))
    if not en_name:
        en_name = page_title.split(' (')[0]

    if is_trainer:
        return (en_name, '', '', '', '', '', '', '')

    # Abilità
    ability_name = ability_jname = ability_jtrans = None
    ability_templates = extract_templates(wikitext, TPL_ABILITY)
    if ability_templates:
        ab = ability_templates[0]
        ability_name = get_param_value(ab, 'name')
        ability_jname = get_param_value(ab, 'jname')
        ability_jtrans = get_param_value(ab, 'jtrans')

    # Primo attacco
    attack_name = attack_jname = attack_jtrans = None
    attack_templates = extract_templates(wikitext, TPL_ATTACK)
    if attack_templates:
        atk = attack_templates[0]
        attack_name = get_param_value(atk, 'name')
        attack_jname = get_param_value(atk, 'jname')
        attack_jtrans = get_param_value(atk, 'jtrans')

    # Jdex
    jdex = None
    carddex_templates = extract_templates(wikitext, TPL_CARDDEX)
    if carddex_templates:
        dex = carddex_templates[0]
        jdex = get_param_value(dex, 'jdex')

    return (
        en_name or '',
        ability_name or '',
        ability_jname or '',
        ability_jtrans or '',
        attack_name or '',
        attack_jname or '',
        attack_jtrans or '',
        jdex or ''
    )


def format_output_line(data):
    parts = [str(x) if x else '' for x in data]
    return ' | '.join(parts)


def sanitize_filename(name):
    """
    Rimuove i caratteri vietati nei nomi file Windows.
    Sostituisce ogni carattere illegale con '' (rimozione pulita).
    """
    for ch in _INVALID_FILENAME_CHARS:
        name = name.replace(ch, '')
    return name


def resolve_output_path(output_arg, expansion_name):
    """
    Risolve il percorso di output.
    Il nome file viene sanificato per rimuovere caratteri non consentiti
    su Windows (es. ':' in "Deluxe Pack: ex").
    """
    default_filename = sanitize_filename(expansion_name.replace(' ', '_')) + '.txt'

    if output_arg is None:
        return default_filename

    output_arg = os.path.expanduser(output_arg)

    if output_arg.endswith(('/', '\\')) or os.path.isdir(output_arg):
        return os.path.join(output_arg, default_filename)

    dir_part = os.path.dirname(output_arg)
    if dir_part and not os.path.exists(dir_part):
        os.makedirs(dir_part, exist_ok=True)

    _, ext = os.path.splitext(output_arg)
    if ext == '':
        os.makedirs(output_arg, exist_ok=True)
        return os.path.join(output_arg, default_filename)

    # Sanifica anche il nome file personalizzato
    base = os.path.basename(output_arg)
    base_sanitized = sanitize_filename(base)
    return os.path.join(dir_part or '.', base_sanitized)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Scarica i dati giapponesi di TUTTE le carte di un'espansione "
            "del GCC Pocket (incluse ristampe e secret rare) da una wiki MediaWiki."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Esempi:\n"
            "  python tcgp_scraper.py \"Paradox Drive\"\n"
            "  python tcgp_scraper.py \"Deluxe Pack: ex\"\n"
            "  python tcgp_scraper.py \"Paradox Drive\" -o ./output/\n"
            "  python tcgp_scraper.py \"Paradox Drive\" -fam pcw -lang it"
        ),
    )
    parser.add_argument('expansion',
                        help='Nome inglese dell\'espansione (es. "Paradox Drive")')
    parser.add_argument('-o', '--output', default=None,
                        help='Percorso di output: directory o file completo')
    parser.add_argument('-fam', '--family', default='bulbapedia',
                        help='Family wiki Pywikibot (default: bulbapedia)')
    parser.add_argument('-lang', '--language', default='en',
                        help='Codice lingua wiki (default: en)')
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    expansion_name = args.expansion
    output_path_arg = args.output
    family = args.family
    lang = args.language

    print("=" * 60)
    print("  TCG Pocket Expansion Data Scraper")
    print(f"  Espansione : {expansion_name}")
    print(f"  Wiki       : {family}:{lang}")
    print(f"  Output     : {output_path_arg or '(default)'}")
    print(f"  Redirect   : getRedirectTarget() + get() su target")
    print("=" * 60)
    print()

    print(f"[1/4] Connessione a {family}:{lang}...")
    site = get_site(family, lang)
    try:
        site.login()
    except Exception:
        pass

    print(f"[2/4] Recupero pagina: {expansion_name}{EXPANSION_PAGE_SUFFIX}")
    exp_page = get_expansion_page(site, expansion_name)
    exp_wikitext = exp_page.get()
    print(f"      OK ({len(exp_wikitext)} byte)")

    print("[3/4] Estrazione lista carte...")
    cards = extract_card_list_from_page(exp_wikitext, expansion_name)

    numbers = [c[0] for c in cards]
    if numbers != sorted(numbers):
        print(f"  ⚠ ERRORE: ordine non crescente!")
        sys.exit(1)

    print(f"      {len(cards)} carte trovate.")
    print(f"      Intervallo: #{min(numbers):03d} – #{max(numbers):03d}")
    print()

    print("[4/4] Download dati carte (con risoluzione redirect):\n")
    results = []
    errors = []
    total = len(cards)

    for i, (number, page_title, card_name) in enumerate(cards, 1):
        status = 'OK'
        try:
            data = process_card_page(site, page_title)
            if data:
                results.append(data)
            else:
                status = 'NO DATA'
                errors.append(f"#{number:03d} {page_title}")
        except Exception as e:
            status = f'ERR: {e}'
            errors.append(f"#{number:03d} {page_title}")

        print(f"  [{i:>3}/{total}] #{number:03d} {page_title:<55} {status}")

    output_path = resolve_output_path(output_path_arg, expansion_name)
    print(f"\nSalvataggio in '{output_path}'...")
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for data in results:
            f.write(format_output_line(data) + '\n')

    print(f"\n{'=' * 60}")
    print(f"  COMPLETATO")
    print(f"  Carte processate: {len(results)}/{total}")
    if errors:
        print(f"  Non processate ({len(errors)}):")
        for e in errors:
            print(f"    - {e}")
    print(f"  File: {output_path}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()