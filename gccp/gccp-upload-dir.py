"""
Script that uploads the pages of a directory to PCW.

The directory must contain one text file for each page, named after the page
title (the .txt extension is removed). Pages whose text is already the same are
skipped.

Examples:
    python gccp-upload-dir.py C:\\...\\gccp\\it -summary:"Bot: aggiornamento GCC Pocket"

Usage:
    python gccp-upload-dir.py [DIRECTORY]

Arguments:
    DIRECTORY       the directory with the .txt files of the pages

Options:
    -summary:<text> the edit summary of every page (required)
    -pt:<seconds>   seconds between two saves (default: 1; pywikibot alone
                    would use 10, which makes a bulk upload take hours)
    -simulate       shows the pages to upload without writing anything
    -help           show this help text
"""

import os
import sys
import time

import pywikibot
from pywikibot import pagegenerators

PAGE_SUFFIX = ".txt"
# secondi fra due salvataggi (pywikibot di default ne usa 10)
DEFAULT_PUT_THROTTLE = 1
# quante pagine chiedere al server per volta, per confrontare il testo attuale
PRELOAD_SIZE = 50
# i nomi dei file hanno i caratteri non validi sostituiti con "_" (vedi
# utils.fix_file_name): qui si riportano al titolo vero
TITLE_FIXES = {"Type_ Null": "Type: Null"}


# titolo della pagina dal nome del file, senza estensione
def page_title(file_name):
    title = file_name[: -len(PAGE_SUFFIX)]
    for wrong, right in TITLE_FIXES.items():
        title = title.replace(wrong, right)
    return title


# titolo e percorso dei file di pagina della cartella, in ordine
def page_files(directory):
    return [
        (page_title(name), os.path.join(directory, name))
        for name in sorted(os.listdir(directory))
        if name.endswith(PAGE_SUFFIX)
    ]


# main function
def main():
    # pywikibot aspetta put_throttle secondi fra due salvataggi; il suo default
    # rende un caricamento in blocco interminabile, quindi qui vale 1 s se non
    # e' stato chiesto altro con -pt: / -put_throttle:. Va impostato PRIMA di
    # handle_args(): quel metodo crea il Site, e il Site si porta dietro il
    # valore letto in quel momento.
    throttle_given = any(arg.startswith(("-pt:", "-put_throttle:"))
                         for arg in sys.argv[1:])
    if not throttle_given:
        pywikibot.config.put_throttle = DEFAULT_PUT_THROTTLE
    local_args = pywikibot.handle_args()
    named_args = {"summary": None}
    pos_args = []
    for arg in local_args:
        if arg.startswith("-"):
            arg_name, _, arg_value = arg[1:].partition(":")
            named_args[arg_name] = arg_value.strip() or True
        else:
            pos_args.append(arg.strip())
    if named_args.get("help") or not pos_args:
        print(__doc__)
        return
    summary = named_args["summary"]
    if not summary or summary is True:
        print("Manca -summary:<testo>: e' l'oggetto di tutte le modifiche.")
        return
    directory = pos_args[0]
    if not os.path.isdir(directory):
        print(f"La cartella {directory} non esiste")
        return
    site = pywikibot.Site()
    files = page_files(directory)
    pages = []
    texts = {}
    for title, path in files:
        page = pywikibot.Page(site, title)
        pages.append(page)
        with open(path, encoding="utf-8") as file:
            texts[page.title()] = file.read()
    print(f"{len(files)} pagine in {directory} ({site})", flush=True)
    started = time.perf_counter()
    # il testo attuale si chiede al server a gruppi, non una pagina per volta
    todo = []
    to_create = 0
    for page in pagegenerators.PreloadingGenerator(
        pages, groupsize=PRELOAD_SIZE, quiet=True
    ):
        text = texts[page.title()]
        try:
            current = page.text
        except pywikibot.exceptions.NoPageError:
            current = None
            to_create += 1
        if current is not None and current.strip() == text.strip():
            continue
        todo.append((page, text))
    print(
        f"{len(todo)} pagine da aggiornare ({to_create} da creare),"
        f" {len(files) - len(todo)} gia' a posto",
        flush=True,
    )
    # tempo di salvataggio: il throttle piu' la richiesta al server
    throttle = pywikibot.config.put_throttle
    if len(todo) > 1:
        print(
            f"Salvataggio a {throttle:g} s per pagina"
            f" (circa {len(todo) * (throttle + 0.3) / 60:.0f} minuti in tutto);"
            f" -pt:0.2 per accelerare.",
            flush=True,
        )
    if pywikibot.config.simulate:
        print("Prova generale (-simulate): non viene scritto nulla", flush=True)
        for page, _ in todo[:20]:
            print(f"  {page.title()}")
        if len(todo) > 20:
            print(f"  ... e altre {len(todo) - 20}")
        return
    saved = failed = 0
    for page, text in todo:
        page.text = text
        try:
            page.save(summary=str(summary), minor=False, force=True)
            saved += 1
        except pywikibot.exceptions.PywikibotException as exc:
            failed += 1
            print(f"ERRORE su {page.title()}: {exc}")
    seconds = time.perf_counter() - started
    print(f"Salvate {saved} pagine, {failed} errori in {seconds:.1f} s")


# invoke main function
if __name__ == "__main__":
    main()
