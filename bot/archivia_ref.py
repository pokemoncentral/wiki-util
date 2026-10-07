#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archivia_ref.py  ·  v0.3  —  programma unico

Trova su Pokémon Central Wiki le note scritte con il template {{ref}} che
contengono un link, controlla se ne esiste una copia archiviata su Internet
Archive, chiede l'archiviazione di ciò che manca e applica le modifiche alle
voci.

Perimetro attuale: SOLO le note scritte con {{ref|...}}, non i tag
<ref>...</ref> né le chiamate {{#tag:ref|...}}.

────────────────────────────────────────────────────────────────────────────
UN COMANDO PER TUTTO
    python3 archivia_ref.py run --consenti
        elenca → scarica → analizza → verifica → archivia → prepara → scrive
        (comprese le modifiche alle voci: non serve altro)

    La stessa cosa senza --consenti è la prova generale: esegue ogni passo in
    sola lettura e mostra cosa farebbe, senza archiviare né scrivere nulla.

COMANDI SINGOLI, se serve intervenire su un passo solo
    pagine    elenca le pagine col template → pagine.txt
    fetch     scarica/aggiorna il wikitext in cache/
    scan      analizza: note con link, già archiviate o no
    check     chiede a Internet Archive se lo snapshot c'è
    archive   archivia ciò che manca          (scrive su IA: --consenti)
    patches   scrive patches.json
    proposte  raggruppa le modifiche per pagina → proposte.json
    salva     applica proposte.json alle voci (scrive sul wiki: --consenti)

────────────────────────────────────────────────────────────────────────────
ACCESSO ALLA WIKI
La wiki è dietro Cloudflare: con un User-Agent "generico" risponde con una
pagina di challenge, mentre con un UA che contiene "Pywikibot/1.0" le API dei
contenuti rispondono normalmente. Da qui la scelta dell'UA qui sotto, e la
possibilità di scaricare il wikitext a lotti (50 titoli per richiesta) invece
di copiarlo a mano.

SCRITTURA SUL WIKI
Aiuto:Regole per l'utilizzo di strumenti machine-assisted riserva «le modifiche
di massa o strutturali (interventi che toccano molte pagine […] sostituzioni
estese)» allo staff e ai bot da esso gestiti, e indica come utilizzo preferibile
proprio uno strumento che imposta la regola, eseguita poi in modo uniforme.
Questo programma è quella regola: l'esecuzione (`salva`) richiede credenziali
(bot password) e l'assenso di chi ha i permessi. Le credenziali si leggono
dall'ambiente e non vengono mai chieste né salvate.

    Linux / macOS (bash)
        export PCW_BOT_USER='Utente@nomebot'
        export PCW_BOT_PASS='…'
        python3 archivia_ref.py run --consenti

    Windows (PowerShell)
        $env:PCW_BOT_USER = 'Utente@nomebot'
        $env:PCW_BOT_PASS = '…'
        python archivia_ref.py run --consenti

Su Windows il programma funziona senza modifiche: i nomi dei file di cache
vengono ripuliti dai caratteri che Windows non ammette (: / \\ * ? " < > |) e
abbreviati quando sono troppo lunghi, e l'output è forzato in UTF-8 per non far
crashare i simboli (→, ✓).
"""

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

NOME = "PCW-archivia-ref/0.3"
UA = "Pywikibot/1.0 (%s; contatto: amministratore)" % NOME

WIKI_API = "https://wiki.pokemoncentral.it/api.php"
IA_CDX = "https://web.archive.org/cdx/search/cdx?url={}&output=json&limit=1&fl=timestamp&filter=statuscode:200&sort=reverse"
# archive.today (archive.is / archive.ph / archive.today / archive.li): nessuna
# API pubblica. Per consultare le copie c'è «newest», per presentarne una nuova
# il modulo di invio. Attenzione: blocca gli indirizzi dei datacenter, quindi da
# un server può risultare irraggiungibile pur essendo attivo.
AIS_BASE = "https://archive.ph"
AIS_NEWEST = AIS_BASE + "/newest/{}"
AIS_SUBMIT = AIS_BASE + "/submit/"
# megalodon.jp (ウェブ魚拓, «calco di rete» giapponese): l'invio richiede un
# token preso da una pagina di conferma, in una sessione con cookie.
MEGA_BASE = "https://megalodon.jp"
MEGA_MAIN = MEGA_BASE + "/pc/main?url={}"
MEGA_DECIDE = MEGA_BASE + "/pc/get_simple/decide"
IA_AVAIL = "https://archive.org/wayback/available?url={}"
IA_SAVE = "https://web.archive.org/save/{}"

CACHE_DIR = "cache"
ELENCO = "pagine.txt"
STATO = "stato_archivia_ref.json"
INDICE = "_indice.json"
PATCHES = "patches.json"
PROPOSTE = "proposte.json"
LOTTO = 50                                   # titoli per richiesta (limite MediaWiki)

RIASSUNTO = "Bot: Aggiunta la copia archiviata alle note esistenti"

MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
        'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']

# Servizi di archiviazione riconosciuti dentro una nota. Se una nota ne linka
# già uno, viene saltata: non c'è niente da archiviare. Comprende tutti i domini
# della famiglia archive.today, che sono lo stesso servizio.
ARCHIVI = ("web.archive.org", "archive.is", "archive.today", "archive.ph",
           "archive.li", "archive.md", "archive.vn", "archive.fo", "archive.ec",
           "megalodon.jp", "perma.cc", "ghostarchive.org", "archivebox.io")

# Sessione HTTP con i cookie conservati fra una richiesta e l'altra. È
# indispensabile: i token di MediaWiki (login e modifica) sono legati alla
# sessione, quindi senza cookie il login fallisce con «sessione scaduta».
SESSIONE = http.cookiejar.CookieJar()
APRI = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(SESSIONE))

# ── HTTP e API ───────────────────────────────────────────────────────────────

def http(url, timeout=30, data=None, tentativi=3, attesa=2):
    """GET (o POST se data) con UA dichiarato e ritentativi sui guasti temporanei."""
    intestazioni = {"User-Agent": UA, "Accept": "*/*",
                    "Accept-Language": "it,en;q=0.8"}
    if data is not None:
        intestazioni["Content-Type"] = "application/x-www-form-urlencoded"
    ultimo = None
    for n in range(tentativi):
        req = urllib.request.Request(url, data=data, headers=intestazioni)
        try:
            with APRI.open(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace"), r.geturl()
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code in (429, 500, 502, 503, 504) and n < tentativi - 1:
                attesa_retry = int(e.headers.get("Retry-After") or attesa * (n + 1))
                time.sleep(min(attesa_retry, 60))
                continue
            raise
        except Exception as e:                          # timeout, DNS, …
            ultimo = e
            if n < tentativi - 1:
                time.sleep(attesa * (n + 1))
                continue
            raise
    raise ultimo


def api(params, timeout=60):
    """GET all'API della wiki, con maxlag e formato JSON."""
    p = dict(params)
    p.setdefault("format", "json")
    p.setdefault("formatversion", "2")
    p.setdefault("maxlag", "5")
    _, corpo, _ = http(WIKI_API + "?" + urllib.parse.urlencode(p), timeout=timeout)
    d = json.loads(corpo)
    if "error" in d:
        raise RuntimeError("API: %s" % d["error"].get("info", d["error"]))
    return d


def api_post(params, timeout=60):
    """POST all'API (lo richiedono login e modifica)."""
    p = dict(params)
    p.setdefault("format", "json")
    p.setdefault("formatversion", "2")
    _, corpo, _ = http(WIKI_API, timeout=timeout,
                       data=urllib.parse.urlencode(p).encode(), tentativi=2)
    return json.loads(corpo)


# ── utilità ──────────────────────────────────────────────────────────────────

def data_it(gg_mm_aaaa):
    """01-09-2022 → 1º settembre 2022 (ordinale sul primo del mese)."""
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", gg_mm_aaaa or "")
    if not m:
        return gg_mm_aaaa
    g, me, a = int(m.group(1)), int(m.group(2)), m.group(3)
    if not (1 <= me <= 12):
        return gg_mm_aaaa
    return ("1º" if g == 1 else str(g)) + " " + MESI[me - 1] + " " + a


# caratteri che Windows non ammette nei nomi di file, e loro sostituti
DIVIETATI = str.maketrans({":": " -", "/": "-", "\\": "-", "*": "-", "?": "-",
                           '"': "-", "<": "-", ">": "-", "|": "-"})


def file_di(titolo, cache_dir):
    r"""Il file di cache di una pagina, con un nome valido anche su Windows.

    Windows non ammette : / \ * ? " < > | nei nomi, e i percorsi sono limitati
    in lunghezza: i primi vengono sostituiti, i titoli lunghissimi abbreviati
    con un'impronta del titolo originale (che così resta ricostruibile).
    """
    nome = titolo.translate(DIVIETATI)
    nome = re.sub(r"\s+", " ", nome).strip().rstrip(".")
    if len(nome) > 120:
        nome = nome[:100].rstrip() + " " + hashlib.md5(titolo.encode("utf-8")).hexdigest()[:8]
    return os.path.join(cache_dir, nome + ".wiki")


# ── 1. elenco delle pagine ───────────────────────────────────────────────────

def elenca(limite=None):
    """Tutte le pagine che usano {{ref}}, paginando la ricerca."""
    titoli, offset, visti = [], 0, 0
    while True:
        d = api({"action": "query", "list": "search",
                 "srsearch": 'hastemplate:"Ref"', "srnamespace": "0",
                 "srlimit": "500", "sroffset": str(offset),
                 "srinfo": "totalhits"}, timeout=40)
        q = d.get("query", {})
        titoli += [v["title"] for v in q.get("search", [])]
        visti = len(titoli)
        cont = d.get("continue", {}).get("sroffset")
        if not cont or (limite and visti >= limite):
            break
        offset = cont
        time.sleep(1)
    return titoli[:limite] if limite else titoli


def cmd_pagine(args):
    titoli = elenca(args.limite)
    with open(ELENCO, "w", encoding="utf-8") as f:
        f.write("\n".join(titoli) + "\n")
    print("Pagine che usano {{ref}}: %d (elenco in %s)" % (len(titoli), ELENCO))
    for t in titoli:
        print("  - %s" % t)
    return 0


# ── 2. scarico del wikitext ──────────────────────────────────────────────────

def leggi_indice(cache_dir):
    p = os.path.join(cache_dir, INDICE)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def scrivi_indice(cache_dir, indice):
    with open(os.path.join(cache_dir, INDICE), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=1, sort_keys=True)


def scarica(titoli, cache_dir, forza=False, pausa=1.0):
    """Scarica il wikitext a lotti, saltando le pagine già in cache e non cambiate."""
    os.makedirs(cache_dir, exist_ok=True)
    indice = leggi_indice(cache_dir)
    fatti, saltati, errori = 0, 0, []

    for i in range(0, len(titoli), LOTTO):
        lotto = titoli[i:i + LOTTO]
        d = api({"action": "query", "prop": "revisions", "titles": "|".join(lotto),
                 "rvprop": "content|ids|timestamp", "rvslots": "main"}, timeout=90)
        for p in d.get("query", {}).get("pages", []):
            titolo = p.get("title")
            if p.get("missing"):
                errori.append((titolo, "pagina inesistente"))
                continue
            rev = (p.get("revisions") or [{}])[0]
            revid = rev.get("revid")
            percorso = file_di(titolo, cache_dir)
            if (not forza and indice.get(titolo, {}).get("revid") == revid
                    and os.path.exists(percorso)):
                saltati += 1
                continue
            testo = ((rev.get("slots") or {}).get("main", {}) or {}).get("content")
            if testo is None:
                errori.append((titolo, "contenuto assente"))
                continue
            with open(percorso, "w", encoding="utf-8") as f:
                f.write(testo)
            indice[titolo] = {"pageid": p.get("pageid"), "revid": revid,
                              "timestamp": rev.get("timestamp")}
            fatti += 1
        if i + LOTTO < len(titoli):
            time.sleep(pausa)

    scrivi_indice(cache_dir, indice)
    return fatti, saltati, errori


def cmd_fetch(args):
    titoli = []
    if os.path.exists(ELENCO):
        with open(ELENCO, encoding="utf-8") as f:
            titoli = [r.strip() for r in f if r.strip()]
    if not titoli:
        titoli = elenca(args.limite)
        with open(ELENCO, "w", encoding="utf-8") as f:
            f.write("\n".join(titoli) + "\n")
    fatti, saltati, errori = scarica(titoli, args.cache, forza=args.forza)
    print("scaricati: %d | invariati (già in cache): %d | problemi: %d"
          % (fatti, saltati, len(errori)))
    for t, perche in errori:
        print("  ! %s: %s" % (t, perche))
    return 0


# ── analisi del wikitext ─────────────────────────────────────────────────────

def pagine_in_cache(cache_dir):
    """Le pagine della cache: (titolo reale, wikitext).

    Il titolo NON si ricava dal nome del file: i nomi sono ripuliti per Windows
    (i due punti di «Leggende Pokémon: Arceus» diventano « -»), quindi dal file
    si otterrebbe un titolo inesistente. Il titolo vero sta nell'indice, scritto
    al momento dello scarico.
    """
    indice = leggi_indice(cache_dir)
    per_file = {os.path.normcase(os.path.abspath(file_di(t, cache_dir))): t
                for t in indice}
    fuori, senza_titolo = [], []
    for nome in sorted(os.listdir(cache_dir)):
        if not nome.endswith(".wiki"):
            continue
        percorso = os.path.join(cache_dir, nome)
        chiave = os.path.normcase(os.path.abspath(percorso))
        titolo = per_file.get(chiave)
        if not titolo:
            titolo = nome[:-5]
            senza_titolo.append(titolo)
        with open(percorso, encoding="utf-8") as f:
            fuori.append((titolo, f.read()))
    if senza_titolo:
        print("Attenzione: %d file di cache senza titolo nell'indice (uso il nome del "
              "file, potrebbe non corrispondere): %s"
              % (len(senza_titolo), ", ".join(senza_titolo)))
    return fuori


def chiamate_ref(testo):
    """Tutte le {{ref|...}} del testo, con bilanciamento delle graffe ({{!}} incluso)."""
    trovate, pos = [], 0
    while True:
        j = testo.find("{{ref", pos)
        if j < 0:
            break
        k = j + len("{{ref")
        if k < len(testo) and testo[k] not in "|}":      # "{{refx" non è il template
            pos = k
            continue
        prof, p, fine = 0, j, None
        while p < len(testo):
            if testo.startswith("{{", p):
                prof += 1
                p += 2
            elif testo.startswith("}}", p):
                prof -= 1
                p += 2
                if prof == 0:
                    fine = p
                    break
            else:
                p += 1
        if fine is None:
            break
        trovate.append({"inizio": j, "fine": fine, "testo": testo[j:fine]})
        pos = fine
    return trovate


def parametri(chiamata):
    """Parametri della chiamata: dict dei nominati + lista dei posizionali."""
    corpo = chiamata["testo"][2:-2][len("ref"):]
    if corpo.startswith("|"):
        corpo = corpo[1:]
    parti, buf, prof, p = [], [], 0, 0
    while p < len(corpo):
        if corpo.startswith("{{", p):
            prof += 1
            buf.append("{{")
            p += 2
            continue
        if corpo.startswith("}}", p):
            prof -= 1
            buf.append("}}")
            p += 2
            continue
        if corpo[p] == "|" and prof == 0:
            parti.append("".join(buf))
            buf = []
        else:
            buf.append(corpo[p])
        p += 1
    parti.append("".join(buf))

    nominati, posizionali = {}, []
    for pezzo in parti:
        m = re.match(r"^\s*([A-Za-z_]+)\s*=(.*)$", pezzo, re.S)
        if m:
            nominati[m.group(1).strip().lower()] = m.group(2).strip()
        else:
            posizionali.append(pezzo.strip())
    return nominati, posizionali


def primo_http(testo):
    m = re.search(r"https?://[^\s\]|<>\"}]+", testo or "")
    return m.group(0) if m else None


def url_della_nota(nom, pos):
    """L'indirizzo della fonte citata, ricostruito dalle stesse regole del modulo."""
    for chiave in ("sito", "press", "stampa", "ufficiale"):
        if nom.get(chiave):
            return primo_http(nom[chiave]), chiave
    if nom.get("video"):
        v = nom["video"]
        u = primo_http(v)
        if u:
            return u, "video"
        if re.match(r"^[\w-]{6,}$", v):
            return "https://www.youtube.com/watch?v=" + v, "video"
    if nom.get("tweet") or nom.get("x"):
        t = nom.get("tweet") or nom.get("x")
        u = primo_http(t)
        if u:
            return u, "tweet"
        if re.match(r"^\d+$", t):
            return "https://x.com/i/status/" + t, "tweet"
    for p in pos:
        u = primo_http(p)
        if u:
            return u, "testo"
    return None, None


def nota_da_analizzare(chiamata):
    """Classifica una chiamata {{ref}}: (esito, url, tipo)."""
    nom, pos = parametri(chiamata)
    # un parametro archivio= vuoto non è un archivio: il modulo lo ignora
    for chiave in ("archivio", "archiviato"):
        if (nom.get(chiave) or "").strip():
            return "ha_archivio", primo_http(nom[chiave]), "archivio"
    if any(a in chiamata["testo"] for a in ARCHIVI):
        return "ha_archivio", None, "archivio"
    url, tipo = url_della_nota(nom, pos)
    if not url:
        return "senza_link", None, None
    return "da_controllare", url, tipo


def scan(cache_dir):
    """Le note da controllare, pagina per pagina."""
    result = []
    for titolo, testo in pagine_in_cache(cache_dir):
        for ch in chiamate_ref(testo):
            esito, url, tipo = nota_da_analizzare(ch)
            result.append({"pagina": titolo, "esito": esito, "url": url,
                           "tipo": tipo, "nota": ch["testo"]})
    return result


def cmd_servizi(args):
    """Verifica quali servizi di archiviazione sono raggiungibili da qui.

    Serve perché archive.is blocca gli indirizzi dei datacenter: da un server
    può risultare irraggiungibile anche quando dal computer di casa funziona.
    """
    print("Internet Archive (CDX)")
    try:
        _, corpo, _ = http(IA_CDX.format("example.com"), timeout=25)
        righe = json.loads(corpo or "[]")
        print("  raggiungibile — example.com ha %d copie" % max(0, len(righe) - 1))
    except Exception as e:
        print("  NON raggiungibile: %s" % e)

    print("archive.is (archive.ph)")
    ok, dettaglio = _ais_raggiungibile(timeout=15)
    print("  %s — %s" % ("raggiungibile" if ok else "NON raggiungibile", dettaglio))
    if not ok:
        print("  Nota: archive.today blocca gli indirizzi dei datacenter. Da un computer")
        print("  di casa di norma funziona; il programma userà comunque Internet")
        print("  Archive come primo tentativo.")

    print("megalodon.jp (ウェブ魚拓)")
    ok, dettaglio = megalodon_disponibile(timeout=15)
    print("  %s — %s" % ("raggiungibile" if ok else "NON raggiungibile", dettaglio))

    if getattr(args, "prova", None):
        print("\nProva di consultazione su %s" % args.prova)
        copia, esito, dettaglio = archiveis_copia(args.prova)
        print("  esito: %s (%s)%s" % (esito, dettaglio,
                                      " → " + copia if copia else ""))
        if getattr(args, "consenti", False):
            print("\nProva di presentazione su archive.is (--consenti)")
            esito, dettaglio, copia = archiveis_salva(args.prova)
            print("  esito: %s (%s)%s" % (esito, dettaglio,
                                          " → " + copia if copia else ""))
            print("\nProva di presentazione su megalodon.jp (--consenti)")
            esito, dettaglio, copia = megalodon_salva(args.prova)
            print("  esito: %s (%s)%s" % (esito, dettaglio,
                                          " → " + copia if copia else ""))
        else:
            print("\n(per provare anche la presentazione, aggiungi --consenti)")
    return 0


def cmd_scan(args):
    for r in scan(args.cache):
        print("%-46s %-14s %s" % (r["pagina"][:46], r["esito"], r["url"] or r["nota"][:60]))
    return 0


# ── Internet Archive ─────────────────────────────────────────────────────────

def varianti(url):
    """Le forme equivalenti di un indirizzo, da provare in ordine."""
    fuori = [url]
    if url.endswith("/"):
        fuori.append(url.rstrip("/"))
    else:
        fuori.append(url + "/")
    return fuori


def timestamp_da_cdx(url, timeout=40):
    """Lo snapshot più recente secondo il CDX: (timestamp, esito, dettaglio).

    esito vale "trovato", "assente" o "errore". Non si deduce dal testo del
    messaggio: un errore e un'assenza vanno distinti in modo affidabile, perché
    da quella differenza dipende se chiedere o no una nuova archiviazione.

    Il CDX è affidabile; l'API «wayback/available» invece risponde a volte con
    un elenco vuoto anche per indirizzi che hanno decine di copie (verificato),
    ed è per questo che non va usata da sola: si finirebbe per archiviare di
    nuovo ciò che esiste già.
    """
    for v in varianti(url):
        indirizzo = IA_CDX.format(urllib.parse.quote(v, safe=""))
        try:
            _, corpo, _ = http(indirizzo, timeout=timeout)
        except Exception as e:
            return None, "errore", "CDX: %s" % e
        corpo = corpo.strip()
        if not corpo:
            continue
        try:
            righe = json.loads(corpo)
        except ValueError:
            continue
        if len(righe) > 1 and righe[1] and righe[1][0]:
            return righe[1][0], "trovato", "CDX"
    return None, "assente", "CDX"


def ia_snapshot(url, timeout=12):
    """Lo snapshot più recente: (url_snapshot, timestamp, esito, dettaglio).

    esito: "trovato" | "assente" | "errore".
    Prima il CDX, che è la fonte affidabile; se il CDX proprio non risponde si
    tenta l'API «available», sapendo che può rispondere «niente» anche quando
    le copie esistono. In caso di dubbio l'esito è "errore", mai "assente":
    così non si chiede una nuova archiviazione al buio.
    """
    ts, esito, dettaglio = timestamp_da_cdx(url, timeout=max(timeout, 40))
    if esito == "trovato":
        return ("https://web.archive.org/web/%s/%s" % (ts, url), ts, "trovato",
                "200 (CDX)")
    if esito == "assente":
        return None, None, "assente", "nessuno snapshot (CDX)"
    # CDX irraggiungibile: l'altra API, ma un suo «niente» non è una prova
    u, ts2, stato = ia_availability(url, timeout=timeout)
    if u:
        return u, ts2, "trovato", "%s (available)" % (stato or "")
    return None, None, "errore", "CDX irraggiungibile (%s)" % dettaglio


def _ais_raggiungibile(timeout=10):
    """Prova minima di contatto con archive.is."""
    try:
        stato, _, _ = http(AIS_BASE + "/", timeout=timeout, tentativi=1)
        return True, "HTTP %s" % stato
    except Exception as e:
        return False, str(e)


def archiveis_copia(url, timeout=25):
    """Esiste una copia su archive.is? (indirizzo, esito, dettaglio).

    Si usa «/newest/<indirizzo>»: se c'è una copia il servizio reindirizza alla
    più recente, altrimenti risponde 404.
    """
    try:
        stato, _, finale = http(AIS_NEWEST.format(url), timeout=timeout, tentativi=1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "assente", "nessuna copia (archive.is)"
        return None, "errore", "archive.is: HTTP %s" % e.code
    except Exception as e:
        return None, "errore", "archive.is: %s" % e
    # dopo il reindirizzamento l'indirizzo finale è quello della copia
    if "/newest/" in finale:
        return None, "assente", "nessuna copia (archive.is)"
    return finale, "trovato", "archive.is"


def archiveis_salva(url, timeout=90):
    """Chiede ad archive.is di archiviare l'indirizzo: (esito, dettaglio, copia).

    Non esiste un'API ufficiale, quindi si invia il modulo. Il servizio è
    protetto e limita molto le richieste: qualunque risposta che non sia una
    copia viene considerata un tentativo non riuscito, mai un successo.
    """
    dati = urllib.parse.urlencode({"url": url, "anyway": "1"}).encode()
    try:
        stato, corpo, finale = http(AIS_SUBMIT, timeout=timeout, data=dati, tentativi=1)
    except urllib.error.HTTPError as e:
        return "errore", "archive.is: HTTP %s" % e.code, None
    except Exception as e:
        return "errore", "archive.is: %s" % e, None
    # 1. se il servizio ha reindirizzato a una copia, quella è fatta
    if "/newest/" not in finale and AIS_BASE.split("//")[1] in finale:
        return "trovato", "archive.is", finale
    # 2. altrimenti la copia potrebbe essere in lavorazione o dichiarata nel corpo
    if "wip" in corpo.lower() or "in corso" in corpo.lower():
        return "errore", "archive.is: copia ancora in lavorazione, riprovare", None
    if "captcha" in corpo.lower() or "robot" in corpo.lower():
        return "errore", "archive.is: chiede di superare un controllo anti-robot", None
    # 3. verifica finale: il servizio la copia ce l'ha?
    copia, esito, dettaglio = archiveis_copia(url, timeout=25)
    if esito == "trovato":
        return "trovato", "archive.is", copia
    return "errore", "archive.is: presentazione non confermata (HTTP %s)" % stato, None


def megalodon_salva(url, timeout=120):
    """Chiede a megalodon.jp di archiviare l'indirizzo: (esito, dettaglio, copia).

    Procedura (non documentata, ricavata dalle pagine):
      1. GET /pc/main?url=<indirizzo> apre una sessione con cookie e restituisce
         il modulo di conferma, con dentro un csrf_token e l'indirizzo;
      2. POST /pc/get_simple/decide con csrf_token e url, nella stessa sessione.

    Il servizio rifiuta le richieste che considera automatiche, e in quel caso lo
    dice esplicitamente.
    """
    _, corpo, _ = http(MEGA_MAIN.format(urllib.parse.quote(url, safe="")),
                       timeout=timeout, tentativi=1)
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', corpo or "")
    url_modulo = re.search(r'name="url"\s+value="([^"]+)"', corpo or "")
    if not (token and url_modulo):
        return "errore", "megalodon.jp: pagina di conferma senza token", None

    try:
        _, risposta, finale = http(MEGA_DECIDE, timeout=timeout, tentativi=1,
                                   data=urllib.parse.urlencode(
                                       {"csrf_token": token.group(1),
                                        "url": url_modulo.group(1)}).encode())
    except urllib.error.HTTPError as e:
        return "errore", "megalodon.jp: HTTP %s" % e.code, None
    except Exception as e:
        return "errore", "megalodon.jp: %s" % e, None

    # rifiuto esplicito delle richieste automatiche
    if "取得出来ませんでした" in risposta or "ロボット" in risposta:
        return ("errore",
                "megalodon.jp rifiuta la richiesta: la considera un'operazione "
                "automatica", None)
    # la copia appena creata compare nella risposta
    copia = re.search(r'(https://megalodon\.jp/\d{4}-\d{2}-\d{2}-\d+[^"\s<]*)', risposta)
    if copia:
        return "trovato", "megalodon.jp", copia.group(1)
    return "errore", "megalodon.jp: esito non riconosciuto (HTTP 200)", None


def megalodon_disponibile(timeout=15):
    """megalodon.jp risponde?"""
    try:
        stato, _, _ = http(MEGA_BASE + "/", timeout=timeout, tentativi=1)
        return True, "HTTP %s" % stato
    except Exception as e:
        return False, str(e)


def ia_availability(url, timeout=12):
    """L'API «available»: meno affidabile del CDX, usata solo come ripiego."""
    try:
        _, corpo, _ = http(IA_AVAIL.format(urllib.parse.quote(url, safe="")), timeout=timeout)
        d = json.loads(corpo)
    except Exception as e:
        return None, None, "errore: %s" % e
    snap = (d.get("archived_snapshots") or {}).get("closest")
    if not snap:
        return None, None, "nessuno snapshot"        # IA ha risposto: davvero assente
    u = (snap.get("url") or "").replace("http://web.archive.org", "https://web.archive.org")
    return u, snap.get("timestamp"), snap.get("status")


def ia_save(url, timeout=120):
    """Chiede a Save Page Now di archiviare l'indirizzo. (stato, url_finale)."""
    try:
        stato, _, finale = http(IA_SAVE.format(url), timeout=timeout, tentativi=1)
        return stato, finale
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def cerca_copia(url, timeout=12):
    """Cerca una copia della pagina, prima su Internet Archive e poi su archive.is.

    Restituisce (indirizzo_copia, timestamp, esito, dettaglio, servizio).
    esito: "trovato" | "assente" | "errore". "assente" si restituisce solo se
    entrambi i servizi hanno risposto di non avere nulla.
    """
    snap, ts, esito, dettaglio = ia_snapshot(url, timeout=timeout)
    if esito == "trovato":
        return snap, ts, "trovato", dettaglio, "IA"
    # archive.is, che ha copie sue: può averle anche dove IA non le ha
    copia, esito_ais, dettaglio_ais = archiveis_copia(url, timeout=max(timeout * 2, 25))
    if esito_ais == "trovato":
        return copia, None, "trovato", "archive.is", "archive.is"
    if esito == "assente" and esito_ais == "assente":
        return None, None, "assente", "nessuna copia (IA e archive.is)", None
    if esito == "assente":
        return None, None, "errore", "IA: nessuna copia; %s" % dettaglio_ais, None
    if esito_ais == "assente":
        return None, None, "errore", "%s; archive.is: nessuna copia" % dettaglio, None
    return None, None, "errore", "%s; %s" % (dettaglio, dettaglio_ais), None


def da_timestamp(ts):
    """20250302123928 → ('02-03-2025', '20250302123928')."""
    if not ts or len(ts) < 8:
        return None, None
    return "%s-%s-%s" % (ts[6:8], ts[4:6], ts[0:4]), ts


# ── stato ────────────────────────────────────────────────────────────────────

def leggi_stato():
    if os.path.exists(STATO):
        with open(STATO, encoding="utf-8") as f:
            return json.load(f)
    return {"snapshot": {}, "tentativi": {}}


def scrivi_stato(s):
    with open(STATO, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


# ── 3. controllo e archiviazione ─────────────────────────────────────────────

def cmd_check(args):
    stato = leggi_stato()
    for r in scan(args.cache):
        if r["esito"] != "da_controllare":
            continue
        snap, ts, esito, dettaglio, servizio = cerca_copia(r["url"], timeout=args.timeout)
        stato["snapshot"][r["url"]] = {"url": snap, "timestamp": ts, "esito": esito,
                                       "stato": dettaglio, "servizio": servizio}
        print("%-64s %-9s %-11s %s" % (r["url"][:64], esito, servizio or "—",
                                       ts or dettaglio))
        time.sleep(1)
    scrivi_stato(stato)
    return 0


def cmd_archive(args):
    stato = leggi_stato()
    for r in scan(args.cache):
        if r["esito"] != "da_controllare":
            continue
        s = stato["snapshot"].get(r["url"])
        if s and s.get("url"):
            continue                                  # esiste già: non si archivia
        esito = (s or {}).get("esito")
        if esito != "assente":
            # "errore" (compreso il caso non ancora controllato): non si archivia,
            # perché senza una risposta certa si rischia di duplicare una copia
            # che esiste già
            print("[saltato] %s — %s"
                  % (r["url"], (s or {}).get("stato") or "controllo non ancora eseguito"))
            continue
        if not args.consenti:
            print("[dry-run] archivierei: %s" % r["url"])
            continue
        print("archivio: %s" % r["url"])
        # 1. Internet Archive
        codice, finale = ia_save(r["url"])
        print("  IA → HTTP %s %s" % (codice, finale or ""))
        stato["tentativi"][r["url"]] = {"quando": int(time.time()), "http": codice}
        riuscito = bool(codice and 200 <= int(codice) < 400)
        servizio = "IA" if riuscito else None
        # 2. se è andata male (X/Twitter, ad esempio), si tenta archive.is
        if not riuscito:
            print("  IA non riuscita: provo archive.is…")
            esito_ais, dettaglio_ais, copia = archiveis_salva(
                r["url"], timeout=max(args.timeout * 6, 90))
            print("  archive.is → %s (%s)" % (esito_ais, dettaglio_ais))
            stato["tentativi"][r["url"]]["archive_is"] = esito_ais
            if esito_ais == "trovato":
                riuscito, servizio = True, "archive.is"
                stato["snapshot"][r["url"]] = {"url": copia, "timestamp": None,
                                               "esito": "trovato",
                                               "stato": "salvato su archive.is",
                                               "servizio": "archive.is"}
        # 3. ultimo tentativo: megalodon.jp
        if not riuscito:
            print("  provo megalodon.jp…")
            esito_m, dettaglio_m, copia_m = megalodon_salva(
                r["url"], timeout=max(args.timeout * 8, 120))
            print("  megalodon.jp → %s (%s)" % (esito_m, dettaglio_m))
            stato["tentativi"][r["url"]]["megalodon"] = esito_m
            if esito_m == "trovato":
                riuscito, servizio = True, "megalodon.jp"
                stato["snapshot"][r["url"]] = {"url": copia_m, "timestamp": None,
                                               "esito": "trovato",
                                               "stato": "salvato su megalodon.jp",
                                               "servizio": "megalodon.jp"}
        if riuscito:
            if servizio == "IA":
                snap, ts, esito2, dettaglio2 = cerca_copia(r["url"], timeout=args.timeout)
                stato["snapshot"][r["url"]] = {"url": snap, "timestamp": ts,
                                               "esito": esito2, "stato": "salvato",
                                               "servizio": servizio}
            print("  ✓ copia su %s" % servizio)
        time.sleep(args.intervallo)
    scrivi_stato(stato)
    return 0


# ── 4. preparazione delle modifiche ──────────────────────────────────────────

def cmd_patches(args):
    """Le sostituzioni: aggiunge archivio= alle note che ne sono prive."""
    stato = leggi_stato()
    fuori = []
    for r in scan(args.cache):
        if r["esito"] != "da_controllare":
            continue
        s = stato["snapshot"].get(r["url"]) or {}
        if not s.get("url"):
            continue
        ggmm, _ = da_timestamp(s.get("timestamp"))
        agg = "|archivio=%s" % s["url"]
        # per archive.is non c'è una data nella marca dell'indirizzo: si omette
        if ggmm:
            agg += "|dataarchivio=%s" % ggmm
        fuori.append({"pagina": r["pagina"], "url": r["url"],
                      "find": r["nota"], "replace": r["nota"][:-2] + agg + "}}",
                      "archivio": s["url"], "dataarchivio": ggmm,
                      "data_it": data_it(ggmm)})
    with open(args.file, "w", encoding="utf-8") as f:
        json.dump(fuori, f, ensure_ascii=False, indent=2)
    print("%d sostituzioni scritte in %s" % (len(fuori), args.file))
    for x in fuori:
        print("\n%s\n  prima:  %s\n  dopo:   %s"
              % (x["pagina"], x["find"][:110], x["replace"][:150]))
    return 0


def cmd_proposte(args):
    """Da patches.json alle modifiche raggruppate per pagina."""
    if not os.path.exists(args.file):
        print("Manca %s: prima esegui 'patches'." % args.file)
        return 1
    with open(args.file, encoding="utf-8") as f:
        patches = json.load(f)
    per_pagina = {}
    for x in patches:
        per_pagina.setdefault(x["pagina"], []).append(
            {"find": x["find"], "replace": x["replace"]})
    fuori = [{"pagina": p, "sostituzioni": v} for p, v in sorted(per_pagina.items())]
    with open(args.proposte, "w", encoding="utf-8") as f:
        json.dump(fuori, f, ensure_ascii=False, indent=2)
    print("%d pagine da modificare, %d sostituzioni in tutto → %s"
          % (len(fuori), len(patches), args.proposte))
    for b in fuori:
        print("\n%s  (%d)" % (b["pagina"], len(b["sostituzioni"])))
        for x in b["sostituzioni"]:
            print("   + %s" % x["replace"][-90:])
    return 0


# ── credenziali ──────────────────────────────────────────────────────────────
#
# Le credenziali si cercano, nell'ordine:
#   1. dalle variabili PCW_BOT_USER / PCW_BOT_PASS, se già impostate (override)
#   2. da pywikibot: la cartella si trova grazie al profilo PowerShell
#      (Documents\WindowsPowerShell\Profile.ps1, che di norma imposta una
#      variabile con il percorso di pywikibot), dalle variabili d'ambiente note,
#      oppure da --pywikibot DIR
#   3. dai suoi file: user-config.py (nome utente e il file delle password) e
#      user-password.py
#
# Su Windows i casi che fregano sono tre, e vengono tutti gestiti:
#   · il Blocco note salva il file come "user-password.py.txt" (l'estensione
#     .txt resta nascosta in Esplora file, quindi sembra a posto);
#   · PYWIKIBOT_DIR punta alla cartella del *pacchetto* pywikibot, mentre
#     user-config.py e user-password.py stanno in quella superiore;
#   · il nome è scritto con maiuscole diverse (User-Password.py).
# Per questo la ricerca guarda anche nelle cartelle superiori, fra i nomi noti,
# e in profondità per due livelli.
#
# La password non viene mai stampata: nei messaggi compare solo mascherata.

VARIABILI_PYWIKIBOT = ("PYWIKIBOT_DIR", "PYWIKIBOT_DIR_PWB", "PYWIKIBOT_HOME",
                       "PYWIKIBOT_PATH", "PWB_DIR", "PYWIKIBOT")

CARTELLE_DA_SALTARE = (".git", "cache", "__pycache__", "logs", "throttle", ".venv", "venv")


def profili_possibili():
    """I profili PowerShell in cui cercare il percorso di pywikibot."""
    casa = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    documenti = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer") or ""
    basi = [os.path.join(casa, "Documents"), os.path.join(casa, "Documenti"),
            os.path.join(casa, ".config", "powershell")]
    if documenti:
        basi += [os.path.join(documenti, "Documents"), os.path.join(documenti, "Documenti")]
    fuori = []
    for base in basi:
        fuori += [os.path.join(base, "WindowsPowerShell", "Profile.ps1"),
                  os.path.join(base, "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
                  os.path.join(base, "PowerShell", "Microsoft.PowerShell_profile.ps1"),
                  os.path.join(base, "PowerShell", "Profile.ps1")]
    return fuori


def variabili_dal_profilo(percorso):
    """Le assegnazioni $env:NOME = 'valore' contenute in un profilo PowerShell."""
    trovate = {}
    try:
        with open(percorso, encoding="utf-8-sig", errors="replace") as f:
            testo = f.read()
    except OSError:
        return trovate
    for nome, valore in re.findall(
            r"\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]([^'\"]+)['\"]", testo):
        trovate[nome] = valore
    return trovate


def sembra_pywikibot(percorso):
    """Vero se la cartella contiene una configurazione o il pacchetto pywikibot."""
    if not percorso or not os.path.isdir(percorso):
        return False
    for base in livelli(percorso, 2):
        if os.path.exists(os.path.join(base, "user-config.py")):
            return True
        if os.path.isdir(os.path.join(base, "pywikibot")):
            return True
    return False


def livelli(percorso, quanti=3):
    """La cartella indicata e quelle superiori (per cercarci dentro)."""
    fuori, p = [], os.path.abspath(percorso)
    for _ in range(quanti):
        if p and p not in fuori:
            fuori.append(p)
        superiore = os.path.dirname(p)
        if superiore == p:
            break
        p = superiore
    return fuori


def trova_cartella_pywikibot(esplicita=None, profilo=None):
    """La cartella di pywikibot e la provenienza: (percorso, spiegazione)."""
    if esplicita:
        return (esplicita, "indicata a mano") if os.path.isdir(esplicita) else (None, "inesistente")
    for nome in VARIABILI_PYWIKIBOT:
        v = os.environ.get(nome)
        if v and os.path.isdir(v):
            return v, "variabile d'ambiente %s" % nome
    candidati = [profilo] if profilo else profili_possibili()
    for p in candidati:
        if not p or not os.path.exists(p):
            continue
        for nome, valore in variabili_dal_profilo(p).items():
            if nome not in ("PATH", "PSModulePath") and sembra_pywikibot(valore):
                return valore, "profilo %s ($env:%s)" % (os.path.basename(p), nome)
    return None, "non trovata"


def _stringhe(riga):
    """Le stringhe fra apici di una riga, ignorando i commenti."""
    return re.findall(r'[uUrRbB]{0,2}["\']([^"\']*)["\']', riga.split("#", 1)[0])


def trova_config(cartella):
    """La cartella di base e il percorso di user-config.py: (base, percorso)."""
    for base in livelli(cartella, 2):
        for voce in (os.listdir(base) if os.path.isdir(base) else []):
            if voce.lower() == "user-config.py":
                return base, os.path.join(base, voce)
    return cartella, None


def e_file_password(nome):
    """Riconosce user-password.py, user-password.py.txt, passwords.py e simili."""
    n = nome.lower()
    return (n.startswith("user-password") or n in ("passwords.py", "password.py")) \
        and n.endswith((".py", ".txt"))


def cerca_password(cartella, password_file=None):
    """Trova il file delle password: (percorso, elenco dei tentativi)."""
    tentativi = []
    basi = livelli(cartella, 2)
    # 1. il percorso dichiarato in user-config.py
    if password_file:
        if os.path.isabs(password_file) and os.path.exists(password_file):
            return password_file, tentativi
        for base in basi:
            c = os.path.join(base, password_file)
            tentativi.append(c)
            if os.path.exists(c):
                return c, tentativi
    # 2. i nomi noti nelle cartelle vicine, senza badare a maiuscole ed estensione
    for base in basi:
        try:
            voci = os.listdir(base)
        except OSError:
            continue
        for voce in sorted(voci):
            if e_file_password(voce):
                return os.path.join(base, voce), tentativi
    # 3. ricerca in profondità, due livelli, saltando le cartelle di servizio
    for base in basi[:1]:
        for radice, cartelle, files in os.walk(base):
            cartelle[:] = [d for d in cartelle if d.lower() not in CARTELLE_DA_SALTARE]
            if len(radice) - len(base) > 0 and radice.count(os.sep) - base.count(os.sep) >= 2:
                cartelle[:] = []
            for f in sorted(files):
                if e_file_password(f):
                    c = os.path.join(radice, f)
                    tentativi.append(c)
                    return c, tentativi
    return None, tentativi


def percorsissimo(p):
    """Il percorso normale, o None."""
    return os.path.abspath(p) if p else None


def leggi_config_pywikibot(percorso_config):
    """Da user-config.py: nome utente, famiglia, lingua, file delle password."""
    info = {"utente": None, "famiglia": None, "lingua": None,
            "password_file": None, "percorso_config": percorsissimo(percorso_config)}
    if not percorso_config or not os.path.exists(percorso_config):
        return info
    with open(percorso_config, encoding="utf-8-sig", errors="replace") as f:
        testo = f.read()
    for riga in testo.splitlines():
        m = re.search(r"""password_file\w*\s*=\s*[uUrR]{0,2}["']([^"']+)["']""", riga)
        if m and not info["password_file"]:
            info["password_file"] = m.group(1)
        m = re.search(r"""usernames\s*\[\s*["'](\w+)["']\s*\]\s*\[\s*["'](\w+)["']\s*\]\s*=\s*[uUrR]{0,2}["']([^"']+)["']""", riga)
        if m:
            famiglia, codice, nome = m.group(1), m.group(2), m.group(3)
            if info["utente"] is None or "pokemoncentral" in famiglia.lower():
                info["utente"], info["famiglia"], info["lingua"] = nome, famiglia, codice
        m = re.search(r"""myLang\s*=\s*[uUrR]{0,2}["'](\w+)["']""", riga, re.I)
        if m and not info["lingua"]:
            info["lingua"] = m.group(1)
    return info


def leggi_password_pywikibot(percorso):
    """Le coppie utente/password di user-password.py, in ordine di comparsa."""
    coppie = []
    if not percorso or not os.path.exists(percorso):
        return coppie
    with open(percorso, encoding="utf-8-sig", errors="replace") as f:
        for riga in f:
            pezzi = _stringhe(riga)
            if len(pezzi) == 4:                      # (famiglia, codice, utente, password)
                coppie.append((pezzi[2], pezzi[3]))
            elif len(pezzi) >= 2:                    # (utente, password)
                coppie.append((pezzi[0], pezzi[1]))
    return coppie


def voci_di(percorso, quanti=14):
    """I primi nomi di file in una cartella, per la diagnostica."""
    try:
        return sorted(os.listdir(percorso))[:quanti]
    except OSError:
        return []


def fonti_possibili(args):
    """Le cartelle candidate, in ordine di priorità, con la loro provenienza.

    L'ordine conta: --pywikibot vince su tutto (è una richiesta esplicita),
    poi il profilo indicato a mano, poi le variabili d'ambiente, poi i profili
    trovati da sé. Ogni voce è (percorso, provenienza).
    """
    fuori = []
    esplicita = getattr(args, "pywikibot", None)
    if esplicita:
        fuori.append((esplicita, "indicata a mano (--pywikibot)"))
    profilo = getattr(args, "profilo", None)
    profili = [profilo] if profilo else profili_possibili()
    if profilo:
        for nome, valore in variabili_dal_profilo(profilo).items():
            if nome not in ("PATH", "PSModulePath"):
                fuori.append((valore, "profilo %s ($env:%s)" % (os.path.basename(profilo), nome)))
    for nome in VARIABILI_PYWIKIBOT:
        v = os.environ.get(nome)
        if v:
            fuori.append((v, "variabile d'ambiente %s" % nome))
    if not profilo:
        for p in profili:
            if not p or not os.path.exists(p):
                continue
            for nome, valore in variabili_dal_profilo(p).items():
                if nome not in ("PATH", "PSModulePath"):
                    fuori.append((valore, "profilo %s ($env:%s)" % (os.path.basename(p), nome)))
    visti, unici = set(), []
    for percorso, provenienza in fuori:
        chiave = os.path.normcase(os.path.abspath(percorso))
        if chiave in visti:
            continue
        visti.add(chiave)
        unici.append((percorso, provenienza))
    return unici


def credenziali_da(cartella):
    """Le credenziali di una cartella: (utente, password, dettagli) o (None, None, motivo)."""
    base, config = trova_config(cartella)
    info = leggi_config_pywikibot(config)
    percorso, tentativi = cerca_password(base or cartella, info["password_file"])
    if not percorso:
        prova = "\n".join("      %s" % t for t in tentativi[:6]) or "      (nessun percorso esplicito)"
        visto = ", ".join(voci_di(base or cartella)) or "cartella vuota o illeggibile"
        return None, None, (
            "file delle password non trovato in %s\n"
            "    provato:\n%s\n"
            "    nella cartella vedo: %s"
            % (base or cartella, prova, visto))

    coppie = leggi_password_pywikibot(percorso)
    if not coppie:
        return None, None, ("«%s» non contiene credenziali leggibili"
                            % os.path.basename(percorso))

    utente = info["utente"]
    scelta = None
    if utente:
        scelta = next((c for c in coppie if c[0].split("@")[0].lower() == utente.lower()), None)
        scelta = scelta or next((c for c in coppie if utente.lower() in c[0].lower()), None)
    scelta = scelta or (coppie[0] if len(coppie) == 1 else None)
    if not scelta:
        nomi = ", ".join(c[0] for c in coppie)
        return None, None, ("nessuna credenziale corrisponde a «%s» (disponibili: %s)"
                            % (utente, nomi))
    return scelta[0], scelta[1], "· %s" % os.path.basename(percorso)


def risolvi_credenziali(args):
    """(utente, password, spiegazione) oppure (None, None, motivo).

    Prova le fonti in ordine e si ferma alla prima che dà credenziali: così una
    variabile d'ambiente rimasta vecchia non blocca il caso in cui il profilo
    PowerShell (o un'altra cartella) sia invece a posto.
    """
    utente_env = os.environ.get("PCW_BOT_USER")
    password_env = os.environ.get("PCW_BOT_PASS")
    if utente_env and password_env:
        return utente_env, password_env, "variabili PCW_BOT_USER / PCW_BOT_PASS"

    fonti = fonti_possibili(args)
    if not fonti:
        return None, None, ("pywikibot non trovato: servono PCW_BOT_USER / PCW_BOT_PASS, "
                            "oppure --pywikibot DIR")

    motivi = []
    for percorso, provenienza in fonti:
        if not os.path.isdir(percorso):
            motivi.append("%s: cartella inesistente (%s)" % (provenienza, percorso))
            continue
        utente, password, dettaglio = credenziali_da(percorso)
        if utente:
            return utente, password, "%s (%s)" % (provenienza, dettaglio)
        motivi.append("%s: %s" % (provenienza, dettaglio))
    return None, None, "\n  ".join(motivi)


def nome_profilo(percorso):
    """Come si chiama, in PowerShell, il file di profilo trovato.

    I profili di PowerShell sono quattro e hanno nomi diversi:
      $PROFILE                        Microsoft.PowerShell_profile.ps1
      $PROFILE.CurrentUserAllHosts    Profile.ps1
      $PROFILE.AllUsersCurrentHost    Microsoft.PowerShell_profile.ps1 (in $PSHOME)
      $PROFILE.AllUsersAllHosts       Profile.ps1 (in $PSHOME)
    """
    nome = os.path.basename(percorso).lower()
    if nome == "profile.ps1":
        return ". $PROFILE.CurrentUserAllHosts"
    if nome == "microsoft.powershell_profile.ps1":
        return ". $PROFILE"
    return '. "%s"' % percorso


def quando_modificato(percorso):
    """La data di modifica di un file, leggibile."""
    try:
        return time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(percorso)))
    except OSError:
        return "?"


def cmd_credenziali(args):
    """Mostra tutte le fonti trovate e da quale verrebbero prese le credenziali."""
    fonti = fonti_possibili(args)
    profilo = getattr(args, "profilo", None)
    profili = [profilo] if profilo else profili_possibili()
    print("Profili PowerShell controllati:")
    trovati = 0
    for p in profili:
        if os.path.exists(p):
            trovati += 1
            print("  %s (modificato il %s)" % (p, quando_modificato(p)))
    if not trovati:
        print("  nessuno (percorsi cercati: %s)" % ", ".join(profili[:2]))

    print("\nFonti in ordine di priorità:")
    if not fonti:
        print("  nessuna: né --pywikibot, né variabili d'ambiente, né profili con un percorso")
    for percorso, provenienza in fonti:
        if not os.path.isdir(percorso):
            print("  [ ] %s → %s (cartella inesistente)" % (provenienza, percorso))
            continue
        utente, password, dettaglio = credenziali_da(percorso)
        print("  [%s] %s → %s" % ("OK" if utente else "  ", provenienza, percorso))
        if not utente:
            for riga in str(dettaglio).splitlines():
                print("        %s" % riga)

    utente, password, spiegazione = risolvi_credenziali(args)
    print()
    if not utente:
        print("credenziali: NON disponibili — %s" % spiegazione)
        return 1
    print("credenziali: utente «%s», password presente (%d caratteri)" % (utente, len(password)))
    print("provenienza: %s" % spiegazione)

    # il caso che genera confusione: la sessione PowerShell ha un valore vecchio
    env = next((os.environ.get(n) for n in VARIABILI_PYWIKIBOT if os.environ.get(n)), None)
    if env and not profilo:
        # quale file di profilo contiene un percorso diverso da quello della sessione?
        da_profilo = []
        for p in profili:
            if not os.path.exists(p):
                continue
            for n, v in variabili_dal_profilo(p).items():
                if n in ("PATH", "PSModulePath"):
                    continue
                if os.path.normcase(os.path.abspath(v)) != os.path.normcase(os.path.abspath(env)):
                    da_profilo.append((p, v))
        if da_profilo:
            p, v = da_profilo[0]
            print("\nATTENZIONE: la variabile d'ambiente di questa sessione vale")
            print("  %s" % env)
            print("mentre il file di profilo %s indica" % p)
            print("  %s" % v)
            print("Il valore della sessione ha la precedenza: la finestra aperta ha ancora")
            print("quello vecchio. Aggiornala con")
            print("  %s" % nome_profilo(p))
            print('oppure con   . "%s"' % p)
            print("oppure apri una nuova finestra PowerShell.")
    return 0


# ── 5. scrittura sul wiki ────────────────────────────────────────────────────

SPIEGAZIONI = {
    "WrongPass": "nome utente o password errati. Per una bot password il nome va "
                 "nella forma Utente@NomeBot (es. Cruifer@CruiferBot)",
    "NotExists": "l'utente indicato non esiste su questo wiki",
    "WrongToken": "token di sessione non valido",
    "NeedToken": "il wiki chiede un token di login (flusso non completato)",
    "Throttled": "troppi tentativi di accesso: attendi qualche minuto",
    "Blocked": "utenza bloccata",
    "Aborted": "accesso interrotto dal wiki",
    "AbortedNeedMac": "la bot password non ha i permessi necessari (grant insufficienti)",
    "Failed": "accesso non riuscito",
}


def login(utente, password):
    """Accesso con bot password. Restituisce (esito, motivo in chiaro).

    Il flusso corretto, con la sessione condivisa:
      1. token per il login  (action=query&meta=tokens&type=login)
      2. action=login con quel token
      3. verifica con meta=userinfo
    Il passo 1 sostituisce il vecchio «token dalla risposta di action=login»,
    che MediaWiki segnala come deprecato.
    """
    d = api({"action": "query", "meta": "tokens", "type": "login"})
    token = ((d.get("query") or {}).get("tokens") or {}).get("logintoken")

    risposta = api_post({"action": "login", "lgname": utente, "lgpassword": password,
                         "lgtoken": token})
    esito = (risposta.get("login") or {}).get("result")

    if esito == "NeedToken":          # il wiki ne fornisce un altro: si riprova
        token = risposta["login"].get("token")
        risposta = api_post({"action": "login", "lgname": utente, "lgpassword": password,
                             "lgtoken": token})
        esito = (risposta.get("login") or {}).get("result")

    if esito == "Success":
        # controllo finale: chi siamo davvero?
        try:
            u = api({"action": "query", "meta": "userinfo"})
            nome = ((u.get("query") or {}).get("userinfo") or {}).get("name")
            if nome:
                return True, "ok (%s)" % nome
        except Exception:
            pass
        return True, "ok"

    motivo = SPIEGAZIONI.get(esito, esito or "errore sconosciuto")
    if esito == "Failed":
        # distingue i due "Failed" più comuni, dal testo del wiki
        testo = ((risposta.get("login") or {}).get("reason") or "")
        if "session" in testo.lower():
            motivo = "sessione non mantenuta fra le richieste (cookie)"
        elif "password" in testo.lower() or "username" in testo.lower():
            motivo = SPIEGAZIONI["WrongPass"]
    return False, motivo


def gruppi_utente():
    """I gruppi dell'utenza collegata: serve per sapere se può marcare le
    modifiche come 'bot' (i bot hanno il gruppo «bot»)."""
    try:
        u = api({"action": "query", "meta": "userinfo", "uiprop": "groups"})
        return ((u.get("query") or {}).get("userinfo") or {}).get("groups") or []
    except Exception:
        return []


def testo_pagina(titolo):
    """Il wikitext attuale della pagina: (testo, revid)."""
    d = api({"action": "query", "prop": "revisions", "titles": titolo,
             "rvprop": "content|ids", "rvslots": "main"})
    p = (d.get("query") or {}).get("pages", [{}])[0]
    if p.get("missing"):
        return None, None
    rev = (p.get("revisions") or [{}])[0]
    return ((rev.get("slots") or {}).get("main", {}) or {}).get("content"), rev.get("revid")


def applica(testo, sostituzioni):
    """Applica le sostituzioni. Ritorna (nuovo testo, applicate, non trovate)."""
    applicate, mancanti = 0, []
    for s in sostituzioni:
        if s["find"] in testo:
            testo = testo.replace(s["find"], s["replace"], 1)
            applicate += 1
        else:
            mancanti.append(s["find"][:70])
    return testo, applicate, mancanti


def cmd_salva(args):
    """Applica TUTTE le proposte in una sola esecuzione."""
    utente, password, spiegazione = risolvi_credenziali(args)
    if not utente:
        print("Credenziali non disponibili: %s" % spiegazione)
        print("Configura pywikibot (user-config.py e user-password.py) oppure imposta")
        print("PCW_BOT_USER / PCW_BOT_PASS. Con 'credenziali' vedi cosa trova.")
        return 1
    print("Credenziali: utente «%s» (%s)" % (utente, spiegazione))
    if not os.path.exists(args.proposte):
        print("Manca %s: prima esegui 'patches' e 'proposte'." % args.proposte)
        return 1

    with open(args.proposte, encoding="utf-8") as f:
        proposte = json.load(f)
    print("%d pagine da modificare. Oggetto: %s" % (len(proposte), args.riassunto))
    if not args.consenti:
        print("MODALITÀ PROVA: non verrà scritto nulla (aggiungi --consenti per scrivere).\n")
    else:
        ok, motivo = login(utente, password)
        if not ok:
            print("Accesso non riuscito: %s" % motivo)
            if "@" not in utente:
                print("Nota: per una bot password il nome utente deve essere nella forma")
                print("      Utente@NomeBot. In user-password.py la prima voce dev'essere")
                print('      per esempio ("Utente@CruiferBot", "…").')
            return 1
        print("Accesso effettuato: %s" % motivo)
        gruppi = gruppi_utente()
        usa_bot = args.bot if args.bot is not None else ("bot" in gruppi)
        if usa_bot and "bot" not in gruppi:
            print("Nota: --bot richiesto, ma l'utenza non ha il flag bot: il wiki")
            print("      potrebbe rifiutare la modifica o ignorare il parametro.")
        # la decisione va salvata qui: è questa che la richiesta di modifica usa
        args.bot = usa_bot
        print("Modifiche marcate come bot: %s\n" % ("sì" if usa_bot else "no"))
        # stessa sessione del login: se i cookie non ci fossero, l'edit fallirebbe
        token = api({"action": "query", "meta": "tokens",
                     "type": "csrf"})["query"]["tokens"]["csrftoken"]

    fatte, fallite, saltate = 0, 0, 0
    for i, b in enumerate(proposte):
        testo, revid = testo_pagina(b["pagina"])
        if testo is None:
            print("  ! %s: pagina inesistente" % b["pagina"])
            fallite += 1
            continue
        nuovo, applicate, mancanti = applica(testo, b["sostituzioni"])
        if not applicate:
            print("  = %s: nessuna sostituzione applicabile, salto" % b["pagina"])
            saltate += 1
            continue
        for m in mancanti:
            print("    non trovato in %s: %s…" % (b["pagina"], m))
        if not args.consenti:
            print("  · %s: %d sostituzioni applicabili" % (b["pagina"], applicate))
            continue
        richiesta = {"action": "edit", "title": b["pagina"], "text": nuovo,
                     "summary": args.riassunto, "token": token,
                     "baserevid": str(revid), "maxlag": "5",
                     # valori ammessi: nochange, preferences, unwatch, watch
                     "watchlist": "nochange"}
        if args.bot:
            richiesta["bot"] = "1"
        if getattr(args, "tag", None):
            richiesta["tags"] = args.tag
        d = api_post(richiesta)
        errore = d.get("error")
        esito = d.get("edit", {})
        if errore:
            print("  ✗ %s: %s — %s" % (b["pagina"], errore.get("code"),
                                       errore.get("info", "")[:160]))
            fallite += 1
        elif esito.get("result") == "Success":
            print("  ✓ %s: %d sostituzioni (rev %s)"
                  % (b["pagina"], applicate, esito.get("newrevid")))
            fatte += 1
        else:
            print("  ✗ %s: risposta inattesa: %s" % (b["pagina"], esito))
            fallite += 1
        if i + 1 < len(proposte):
            time.sleep(args.pausa)

    print("\nmodificate: %d | fallite: %d | saltate: %d" % (fatte, fallite, saltate))
    return 0


# ── orchestrazione ───────────────────────────────────────────────────────────

def cmd_run(args):
    """La sequenza completa, con un solo comando."""
    if not args.no_fetch:
        print("== fetch (scarico le pagine che usano {{ref}}) ==")
        cmd_fetch(args)
    print("\n== scan ==")
    cmd_scan(args)
    print("\n== check (Internet Archive) ==")
    cmd_check(args)
    print("\n== archive ==")
    cmd_archive(args)
    print("\n== patches ==")
    cmd_patches(args)
    print("\n== proposte ==")
    cmd_proposte(args)
    print("\n== salva (scrittura sul wiki) ==")
    return cmd_salva(args)


def main():
    ap = argparse.ArgumentParser(
        description="Copie archiviate per le note {{ref}}: prepara e applica le modifiche",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Esempi:\n"
               "  python3 archivia_ref.py run --consenti   (fa tutto, compreso salvare)\n"
               "  python3 archivia_ref.py run              (prova generale: non modifica nulla)\n"
               "  python3 archivia_ref.py run --no-fetch --consenti  (salta lo scarico)\n")
    ap.add_argument("comando", choices=["pagine", "fetch", "scan", "check", "archive",
                                        "patches", "proposte", "salva",
                                        "credenziali", "servizi", "run"])
    ap.add_argument("--cache", default=CACHE_DIR)
    ap.add_argument("--file", default=PATCHES, help="file delle sostituzioni")
    ap.add_argument("--proposte", default=PROPOSTE, help="file delle modifiche per pagina")
    ap.add_argument("--riassunto", default=RIASSUNTO, help="oggetto delle modifiche")
    gruppo_bot = ap.add_mutually_exclusive_group()
    gruppo_bot.add_argument("--bot", dest="bot", action="store_true", default=None,
                            help="marca le modifiche come bot (predefinito: sì, se "
                                 "l'utenza ha il flag bot)")
    gruppo_bot.add_argument("--no-bot", dest="bot", action="store_false",
                            help="non marcare le modifiche come bot")
    ap.add_argument("--tag", metavar="NOME[,NOME]",
                    help="tag da applicare alle modifiche (serve il permesso; es. mcp)")
    ap.add_argument("--pausa", type=int, default=5, help="secondi fra due modifiche al wiki")
    ap.add_argument("--prova", metavar="URL",
                    help="con 'servizi', prova consultazione e presentazione su questo indirizzo")
    ap.add_argument("--pywikibot", metavar="DIR",
                    help="cartella di pywikibot (se non la si trova da sé)")
    ap.add_argument("--profilo", metavar="FILE",
                    help="profilo PowerShell da cui leggere il percorso di pywikibot")
    ap.add_argument("--limite", type=int, help="numero massimo di pagine (per prove)")
    ap.add_argument("--forza", action="store_true",
                    help="con 'fetch', riscarica anche le pagine non cambiate")
    ap.add_argument("--no-fetch", action="store_true", help="con 'run', non riscaricare")
    ap.add_argument("--timeout", type=int, default=12,
                    help="secondi di attesa per le chiamate a Internet Archive")
    ap.add_argument("--intervallo", type=int, default=15,
                    help="secondi fra due richieste di archiviazione")
    ap.add_argument("--consenti", action="store_true",
                    help="autorizza le operazioni che modificano qualcosa: "
                         "l'archiviazione su Internet Archive e la scrittura sul wiki")
    args = ap.parse_args()
    try:                       # console Windows: non far crashare i simboli →, ✓, —
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return {"pagine": cmd_pagine, "fetch": cmd_fetch, "scan": cmd_scan,
            "check": cmd_check, "archive": cmd_archive, "patches": cmd_patches,
            "proposte": cmd_proposte, "salva": cmd_salva,
            "credenziali": cmd_credenziali, "servizi": cmd_servizi,
            "run": cmd_run}[args.comando](args)


if __name__ == "__main__":
    sys.exit(main())
