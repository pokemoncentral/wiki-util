#!/usr/bin/env python3
"""
Contatore di rarità per espansioni GCC Pocket su Pokémon Central Wiki.

Dipendenze: pywikibot (pip install pywikibot)

Utilizza pywikibot per collegarsi a PCW, legge la sezione "Elenco delle carte"
di un'espansione e conta le carte per ciascuna rarità (5° parametro del
template {{setlist/entry}}). Verifica che la somma corrisponda al totale
dichiarato nell'infobox.

Esempio di utilizzo: python conta_rarita.py pcw it "Assalto dei Paradossi"
"""

import re
import sys
from collections import OrderedDict

import pywikibot
from pywikibot import Page, Site

# ── Rarità in ordine canonico ──────────────────────────────────────────────
RARITIES = [
    "Diamante 1", "Diamante 2", "Diamante 3", "Diamante 4",
    "Stella 1", "Stella 2", "Stella 3",
    "Cromatico 1", "Cromatico 2",
    "Corona 1",
]


# ── Parsing wikitext ───────────────────────────────────────────────────────

def extract_section(text: str, section_title: str) -> str | None:
    """Estrae il corpo di una sezione dal wikitext (intestazione esclusa)."""
    pattern = re.compile(
        r'^(={2,})\s*' + re.escape(section_title) + r'\s*\1\s*$',
        re.MULTILINE
    )
    match = pattern.search(text)
    if not match:
        return None

    start = match.end()
    level = len(match.group(1))

    next_section = re.compile(
        r'^={1,' + str(level) + r'}\s*[^=].*\s*={1,' + str(level) + r'}\s*$',
        re.MULTILINE
    )
    next_match = next_section.search(text, start)
    end = next_match.start() if next_match else len(text)

    return text[start:end].strip()


def parse_positional_params(inner: str) -> list[str]:
    """Spezza `inner` sui pipe di primo livello (rispetta le graffe nidificate)."""
    params = []
    current = ""
    depth = 0
    for char in inner:
        if char == '{':
            depth += 1
            current += char
        elif char == '}':
            depth -= 1
            current += char
        elif char == '|' and depth == 0:
            params.append(current.strip())
            current = ""
        else:
            current += char
    params.append(current.strip())
    return params


def extract_setlist_entries(text: str) -> list[str]:
    """Restituisce tutti i template {{setlist/entry|...}} completi (graffe bilanciate)."""
    entries = []
    prefix = '{{setlist/entry|'
    plen = len(prefix)
    pos = 0

    while True:
        start = text.find(prefix, pos)
        if start == -1:
            break

        depth = 1
        i = start + plen
        while i < len(text) and depth > 0:
            two = text[i:i + 2]
            if two == '{{':
                depth += 1
                i += 2
            elif two == '}}':
                depth -= 1
                i += 2
            else:
                i += 1

        if depth == 0:
            entries.append(text[start:i])
        pos = i

    return entries


# ── Conteggio ──────────────────────────────────────────────────────────────

def count_rarities(section_text: str) -> tuple[OrderedDict, int, list[str]]:
    entries = extract_setlist_entries(section_text)
    counts = OrderedDict((r, 0) for r in RARITIES)
    unknown = []

    for entry in entries:
        inner = entry[len('{{setlist/entry|'):-2]
        params = parse_positional_params(inner)

        if len(params) < 5:
            print(f"[!]  Template con {len(params)} parametri invece di >=5: {params[0] if params else '?'}")
            continue

        rarity = params[4].strip()
        if rarity in counts:
            counts[rarity] += 1
        else:
            unknown.append(rarity)

    total = sum(counts.values())
    return counts, total, unknown


# ── Recupero del totale dall'infobox ────────────────────────────────────────

def extract_total_from_infobox(text: str) -> int | None:
    match = re.search(r'\{\{GCCSetSingoloInfobox.*?\}\}', text, re.DOTALL)
    if not match:
        return None

    infobox = match.group(0)
    card_match = re.search(r'\|cards\s*=\s*(\d+)', infobox)
    if card_match:
        return int(card_match.group(1))
    return None


# ── Output ─────────────────────────────────────────────────────────────────

def print_results(counts: OrderedDict, total: int, expected: int | None,
                  unknown: list[str]) -> None:
    print("\n" + "=" * 50)
    print("RISULTATI DEL CONTEGGIO")
    print("=" * 50)

    for rarity, count in counts.items():
        print(f"  {rarity:15s}: {count:3d}")

    print("-" * 50)
    print(f"  {'TOTALE':15s}: {total:3d}")

    if expected is not None:
        if total == expected:
            print(f"\n[OK] La somma ({total}) corrisponde al totale dichiarato ({expected}).")
        else:
            print(f"\n[ERR] ERRORE: la somma ({total}) NON corrisponde al totale dichiarato ({expected})!")
            print(f"   Differenza: {expected - total:+d}")

    if unknown:
        print(f"\n[!]  Rarita sconosciute incontrate: {set(unknown)}")

    parts = [f"{counts[r]} {{{{rar|{r}}}}}" for r in RARITIES]
    print("\n" + "-" * 50)
    print("RIGA FORMATTATA:")
    print(", ".join(parts))
    print("=" * 50)


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== Contatore Rarita GCC Pocket ===")
    print("Questo script analizza l'elenco delle carte di un'espansione\n"
          "del GCC Pocket su Pokemon Central Wiki.\n")

    # ── Input: da riga di comando (3+ args) o interattivo ─────────────
    if len(sys.argv) >= 4:
        family = sys.argv[1].strip()
        lang = sys.argv[2].strip()
        expansion = sys.argv[3].strip()
        print(f"Parametri da riga di comando: family={family}, lang={lang}, expansion={expansion}\n")
    else:
        family = input("Nome della family (es. 'pcw'): ").strip()
        lang = input("Lingua (es. 'it'): ").strip()
        expansion = input("Nome dell'espansione (es. 'Assalto dei Paradossi'): ").strip()

    # ── Connessione ────────────────────────────────────────────────────
    try:
        site = Site(lang, family)
    except Exception as exc:
        print(f"[ERR] Impossibile connettersi al sito: {exc}")
        sys.exit(1)

    print(f"[OK] Connesso a: {site}")

    # ── Pagina ─────────────────────────────────────────────────────────
    page_title = f"{expansion} (GCC Pocket)"
    page = Page(site, page_title)

    if not page.exists():
        print(f"[ERR] La pagina '{page_title}' non esiste!")
        sys.exit(1)

    print(f"[PAG] Pagina: {page.title()}")

    # ── Estrai sezione ─────────────────────────────────────────────────
    text = page.text
    section = extract_section(text, "Elenco delle carte")

    if section is None:
        print("[ERR] Sezione 'Elenco delle carte' non trovata!")
        sys.exit(1)

    print(f"[SEZ] Sezione 'Elenco delle carte' trovata ({len(section)} byte)")

    # ── Conteggio ──────────────────────────────────────────────────────
    counts, total, unknown = count_rarities(section)

    # ── Totale atteso ──────────────────────────────────────────────────
    expected = extract_total_from_infobox(text)

    # ── Output ─────────────────────────────────────────────────────────
    print_results(counts, total, expected, unknown)


if __name__ == "__main__":
    main()
