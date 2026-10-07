#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refmigrate.py — converte le note legacy di Pokémon Central Wiki nel template {{ref}}.

Note legacy riconosciute e conversione
--------------------------------------
    <ref>testo</ref>                       →  {{ref|testo}}
    <ref name="X">testo</ref>              →  {{ref|testo|name=X}}
    <ref name="X" />                       →  {{ref|name=X}}
    <ref name=X>testo</ref>                →  {{ref|testo|name=X}}
    <ref>T=est</ref> (contiene «=»)         →  {{ref|1=T=est}}   (posizionale esplicito)
    {{#tag:ref|testo}}                     →  {{ref|testo}}
    {{#tag: ref|testo}}                    →  {{ref|testo}}
    {{#tag: ref | testo | name="X"}}       →  {{ref|testo|name=X}}
    {{#tag:ref||name=X}}                   →  {{ref|name=X}}    (richiamo di nota)
    {{#tag:ref|testo|group="Nota"}}        →  {{ref|testo|group=Nota}}
    <ref group="Citazione" name="X" />     →  {{ref|name=X|group=Citazione}}

Regole imparate dai casi reali (tutte verificate con il parser del wiki)
-----------------------------------------------------------------------
1. In un parametro di template il primo «=» che non sta dentro {{...}} o [[...]]
   rende il testo un parametro con nome; dentro un link esterno ([https://…/?a=b T])
   NON è protetto. Se quindi il testo della nota contiene «=» si scrive «1=testo».
   In {{#tag:ref|…}} invece il testo può contenere «=» liberamente, quindi «1=» va
   aggiunto solo quando serve.
2. Il testo della nota non può contenere «|» fuori da {{...}}, [[...]], commenti e
   <nowiki>: la conversione è impossibile e la nota viene segnalata senza essere
   toccata (--pipe nowiki per aggirarla). NB: un «|» dentro un link esterno
   ([https://… Testo | Altro]) conta come di primo livello, verificato in anteprima.
3. In {{#tag:ref|…|nome="valore"}} le virgolette sono sintassi degli attributi del
   tag e vanno tolte: name="{{{name|}}}" → name={{{name|}}}.
4. Dentro <nowiki>, <syntaxhighlight>, <pre> e simili, e dentro i commenti, non si
   tocca nulla (leggendaria compresa la documentazione dei template).
5. <references … /> non è una nota e resta com'è (viene solo contato).
6. Le note con group= (104 pagine con "Nota", 5 con "nota", "Citazione") diventano
   {{ref|…|group=X}}: Template:Ref inoltra «group» a Modulo:Citazione. Il nome del
   gruppo si conserva com'è (maiuscole comprese), perché deve coincidere con quello
   di <references group="…" />. Con --gruppo tieni restano invariate.
7. «<ref name="X />» (virgolette non chiuse, 4 pagine) è wikitext rotto: la pagina
   mostra un errore di citazione. Con --ripara-nomi diventa il richiamo {{ref|name=X}}.
8. Text «|» di primo livello nel testo della nota, anche dentro un link esterno
   (diverse pagine): con --pipe nowiki diventa <nowiki>|</nowiki>, l'unica forma che
   regge sia nel testo sia dentro i link ({{!}} no: verificato in anteprima).

Uso
---
    python3 refmigrate.py analizza corpus/                     # censimento e anomalie
    python3 refmigrate.py converti Pagina.wiki --diff          # conversione di un file
    python3 refmigrate.py piano --corpus corpus --out piano.json
    python3 refmigrate.py titolo "Nome pagina" --diff          # scarica dall'API e converte
    python3 refmigrate.py estrai-note --titolo "Nome pagina"    # elenco note per il confronto
    python3 refmigrate.py run --prova                           # prepara tutto, non scrive
    python3 refmigrate.py run                                   # prepara e salva su PCW
    python3 refmigrate.py run --max-salvataggi 50               # a scaglioni
"""

import argparse
import ast
import difflib
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

API = "https://wiki.pokemoncentral.it/api.php"
UA = "Pywikibot/1.0"
_OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(CookieJar()))

# Tag il cui contenuto non è wikitext e va saltato in blocco.
VERBATIM_TAGS = {
    "nowiki", "pre", "syntaxhighlight", "source", "math", "chem", "hiero",
    "score", "timeline", "graph", "mapframe", "imagemap",
    # <gallery> non è qui di proposito: le didascalie sono wikitext e possono
    # contenere note (verificato: sia <ref> sia {{ref|…}} funzionano).
}
# Alias dei parametri di #tag:ref.
PARAM_TAG = {
    "name": "nome", "nome": "nome",
    "group": "gruppo", "gruppo": "gruppo",
}
TAG_RE = re.compile(r"<([A-Za-z][\w:-]*)")
TAGTAG_RE = re.compile(r"\{\{\s*#tag:\s*ref(?=\s|\||\})", re.I)
CHIUDI_REF_RE = re.compile(r"</ref\s*>", re.I)
ATTR_RE = re.compile(r"""([A-Za-z_][\w-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s'"]+))""")
# «<ref name="X />»: virgolette mai chiuse. Va riconosciuto *prima* della lettura
# degli attributi, altrimenti la virgoletta aperta inghiotte il testo successivo
# fino alle virgolette della nota seguente.
ROTTO_RE = re.compile(r'<ref\s+name\s*=\s*"([^"<>]*?)\s*/>', re.I)


# ────────────────────────────────────────────────────────────────────────────
# strutture
# ────────────────────────────────────────────────────────────────────────────

class Nota:
    """Una nota legacy trovata nel wikitext."""

    def __init__(self, tipo, inizio, fine, testo, nome=None, gruppo=None,
                 attr=None, problemi=None, riga=0):
        self.tipo = tipo            # 'tag' (<ref>) o 'tagtag' ({{#tag:ref}})
        self.inizio = inizio        # offset del primo carattere
        self.fine = fine            # offset dopo l'ultimo carattere
        self.testo = testo          # contenuto della nota
        self.nome = nome            # name=/nome= (None se assente)
        self.gruppo = gruppo        # group=
        self.attr = attr or {}      # altri attributi trovati
        self.problemi = list(problemi or [])
        self.riga = riga            # numero di riga (1-based), per il report

    @property
    def convertibile(self):
        return not self.problemi

    def __repr__(self):
        return (f"<Nota {self.tipo} riga {self.riga} nome={self.nome!r} "
                f"gruppo={self.gruppo!r} problemi={self.problemi}>")


# ────────────────────────────────────────────────────────────────────────────
# scansione del wikitext
# ────────────────────────────────────────────────────────────────────────────

def _fine_tag(testo, i):
    """Indice dopo il «>» che chiude il tag aperto in i (rispetta le virgolette)."""
    j, n, apice = i + 1, len(testo), None
    while j < n:
        c = testo[j]
        if apice:
            if c == apice:
                apice = None
        elif c in "\"'":
            apice = c
        elif c == ">":
            return j + 1
        elif testo.startswith("{{", j):
            k = _fine_graffe(testo, j)
            j = n if k is None else k
            continue
        j += 1
    return None


def _fine_graffe(testo, i):
    """Indice dopo il «}}» che chiude il «{{» aperto in i (annidamento compreso)."""
    liv, j, n = 0, i, len(testo)
    while j < n:
        if testo.startswith("<!--", j):
            k = testo.find("-->", j + 4)
            j = n if k < 0 else k + 3
            continue
        if testo.startswith("{{", j):
            liv += 1
            j += 2
            continue
        if testo.startswith("}}", j):
            liv -= 1
            j += 2
            if liv == 0:
                return j
            continue
        if testo[j] == "<":
            m = TAG_RE.match(testo, j)
            if m and m.group(1).lower() in VERBATIM_TAGS:
                k = _fine_verbatim(testo, j, m.group(1).lower())
                j = n if k is None else k
                continue
        j += 1
    return None


def _fine_verbatim(testo, i, tag):
    """Indice dopo la regione racchiusa da un tag verbatim (o dopo il tag stesso)."""
    fine = _fine_tag(testo, i)
    if fine is None:
        return len(testo)
    if testo[i:fine].rstrip().endswith("/>"):
        return fine
    m = re.compile(r"</" + tag + r"\s*>", re.I).search(testo, fine)
    return len(testo) if m is None else m.end()


def _spezza_args(interno):
    """Divide una lista di argomenti sui «|» di primo livello.

    Non separano i «|» dentro {{...}}, [[...]], i commenti e i tag verbatim.
    Attenzione, verificato in anteprima: i «|» dentro un link esterno ([https://…
    Testo | Altro]) SEPARANO eccome, sia in {{ref|…}} sia in {{#tag:ref|…}}; per
    questo l'unico modo di tenerli è scriverli <nowiki>|</nowiki>.
    """
    pezzi, buf, j, n = [], [], 0, len(interno)
    while j < n:
        if interno.startswith("<!--", j):
            k = interno.find("-->", j + 4)
            k = n if k < 0 else k + 3
            buf.append(interno[j:k])
            j = k
            continue
        if interno.startswith("{{", j):
            k = _fine_graffe(interno, j)
            k = n if k is None else k
            buf.append(interno[j:k])
            j = k
            continue
        if interno.startswith("[[", j):
            k = interno.find("]]", j + 2)
            k = n if k < 0 else k + 2
            buf.append(interno[j:k])
            j = k
            continue
        if interno[j] == "<":
            m = TAG_RE.match(interno, j)
            if m and m.group(1).lower() in VERBATIM_TAGS:
                k = _fine_verbatim(interno, j, m.group(1).lower())
                buf.append(interno[j:k])
                j = n if k is None else k
                continue
        if interno[j] == "|":
            pezzi.append("".join(buf))
            buf = []
            j += 1
            continue
        buf.append(interno[j])
        j += 1
    pezzi.append("".join(buf))
    return pezzi


def _pipa_di_primo_livello(testo):
    """True se il testo contiene un «|» che spezzerebbe i parametri."""
    return len(_spezza_args(testo)) > 1


def _leggi_attr(stringa):
    """Legge gli attributi di un tag; restituisce (dizionario, problemi)."""
    attr, problemi = {}, []
    for m in ATTR_RE.finditer(stringa):
        valore = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4))
        attr[m.group(1).lower()] = valore
    resto = ATTR_RE.sub(" ", stringa)
    if resto.strip():
        problemi.append(f"attributi non riconosciuti: «{resto.strip()}»")
    return attr, problemi


def _leggi_ref(testo, i):
    """Legge una nota scritta come tag <ref>…</ref>."""
    riga = testo.count("\n", 0, i) + 1
    m = ROTTO_RE.match(testo, i)
    if m:      # marcatore rotto: <ref name="X /> invece di <ref name="X" />
        return Nota("tag", i, m.end(), "", m.group(1), None, {}, [
            'marcatore rotto «name="X />»: con --ripara-nomi diventa il richiamo '
            "{{ref|name=X}}"], riga), m.end()
    fine = _fine_tag(testo, i)
    if fine is None:
        n = Nota("tag", i, len(testo), "", riga=riga,
                 problemi=["tag <ref> senza «>» di chiusura"])
        return n, len(testo)
    attr_str = testo[i + 4:fine - 1]
    autocons = attr_str.strip().endswith("/")
    if autocons:
        attr_str = attr_str.rstrip()[:-1]
    attr, problemi = _leggi_attr(attr_str)
    nome, gruppo = attr.pop("name", None), attr.pop("group", None)
    for chiave in list(attr):
        problemi.append(f"attributo «{chiave}» non gestito")
    if autocons:
        return Nota("tag", i, fine, "", nome, gruppo, attr, problemi, riga), fine
    m = CHIUDI_REF_RE.search(testo, fine)
    if not m:
        problemi.append("manca </ref>")
        return Nota("tag", i, len(testo), testo[fine:], nome, gruppo, attr,
                    problemi, riga), len(testo)
    return Nota("tag", i, m.end(), testo[fine:m.start()], nome, gruppo, attr,
                problemi, riga), m.end()


def _leggi_tagtag(testo, i):
    """Legge una nota scritta come {{#tag:ref|…}}."""
    riga = testo.count("\n", 0, i) + 1
    m = TAGTAG_RE.match(testo, i)
    fine = _fine_graffe(testo, i)
    if fine is None:
        return Nota("tagtag", i, len(testo), "", riga=riga,
                    problemi=["chiamata #tag:ref senza «}}» di chiusura"]), len(testo)
    interno = testo[m.end():fine - 2].lstrip()
    if not interno.startswith("|"):
        return Nota("tagtag", i, fine, "", riga=riga,
                    problemi=["chiamata #tag:ref senza argomenti"]), fine
    pezzi = _spezza_args(interno[1:])
    contenuto = pezzi[0].strip()
    attr, problemi = {}, []
    for pezzo in pezzi[1:]:
        if not pezzo.strip():
            continue
        pm = re.match(r"\s*([A-Za-z_][\w-]*)\s*=\s*(.*)\Z", pezzo, re.S)
        if not pm:
            problemi.append(f"argomento posizionale inatteso: «{pezzo.strip()[:60]}»")
            continue
        chiave, valore = pm.group(1).lower(), pm.group(2).strip()
        if chiave not in PARAM_TAG:
            problemi.append(f"parametro «{chiave}=» non gestito")
            continue
        if len(valore) >= 2 and valore[0] == valore[-1] and valore[0] in "\"'":
            valore = valore[1:-1]      # le virgolette sono sintassi del tag, non testo
        attr[PARAM_TAG[chiave]] = valore
    return Nota("tagtag", i, fine, contenuto, attr.pop("nome", None),
                attr.pop("gruppo", None), attr, problemi, riga), fine


def trova_note(testo):
    """Elenca le note legacy presenti nel wikitext."""
    note = []
    i, n = 0, len(testo)
    while i < n:
        if testo.startswith("<!--", i):
            k = testo.find("-->", i + 4)
            i = n if k < 0 else k + 3
            continue
        if testo[i] == "<":
            m = TAG_RE.match(testo, i)
            if m:
                tag = m.group(1).lower()
                if tag in VERBATIM_TAGS:
                    k = _fine_verbatim(testo, i, tag)
                    i = n if k is None else k
                    continue
                if tag == "ref":
                    nota, i = _leggi_ref(testo, i)
                    note.append(nota)
                    continue
                if tag == "references":
                    k = _fine_tag(testo, i)
                    i = n if k is None else k
                    continue
        m = TAGTAG_RE.match(testo, i)
        if m:
            nota, i = _leggi_tagtag(testo, i)
            note.append(nota)
            continue
        i += 1
    return note


# ────────────────────────────────────────────────────────────────────────────
# conversione
# ────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────
# fonti strutturate
# ────────────────────────────────────────────────────────────────────────────
#
# Una nota della forma «[URL Titolo] coda» viene riscritta con i parametri di
# {{ref}} quando l'URL è di un tipo che il template conosce (YouTube, X/Twitter,
# sito ufficiale, press site, Internet Archive) e la coda contiene SOLO dati
# che il template sa rendere (lingua, data, copia archiviata). Se nella coda
# c'è qualunque altra cosa, la nota resta testuale: nessuna informazione va
# persa. Le note generiche con una copia archiviata o una lingua usano comunque
# |archivio= e |lingua= (decorazioni della nota testuale).

MESI_NUM = {m: i for i, m in enumerate(
    ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
     "agosto", "settembre", "ottobre", "novembre", "dicembre"], 1)}
LINGUE_NOTE = {"inglese", "giapponese", "francese", "tedesco", "spagnolo",
               "italiano", "coreano", "portoghese", "olandese", "cinese",
               "cinese tradizionale", "cinese semplificato", "polacco", "russo"}
_PIPE = r"(?:<nowiki>\|</nowiki>|\{\{!\}\}|&#124;)"
LINK_RE = re.compile(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]")
_CODA = [
    ("archivio", re.compile(r"\(\[(https?://[^\s\]]+)\s+archiviat[oa][^\]]*\]\)", re.I)),
    ("archivio", re.compile(r"archiviat[oa] (?:in|su) \[(https?://[^\s\]]+)\s+[^\]]*\]", re.I)),
    ("lingua", re.compile(r"<sup>\[([A-Za-zà ]+)\]</sup>")),
    ("lingua", re.compile(r"\(([A-Za-zà ]+)\)")),
    ("data", re.compile(r"(?:del\s+)?\(?(\d{1,2})º?\s+([A-Za-z]+)\s+(\d{4})\)?", re.I)),
    ("youtube", re.compile(r"da YouTube", re.I)),
    ("archiviato", re.compile(r"\(archiviat[oa]\)", re.I)),
]


def _host(url):
    h = (urllib.parse.urlsplit(url).hostname or "").lower()
    return re.sub(r"^(www|m|mobile)\.", "", h)


def tipo_url(url):
    """(parametro di {{ref}}, valore) per un URL riconosciuto, o None."""
    h = _host(url)
    if h in ("youtube.com", "youtu.be"):
        m = re.search(r"(?:[?&]v=|youtu\.be/)([\w-]{11})", url)
        return ("video", m.group(1)) if m else None
    if h in ("twitter.com", "x.com") and re.search(r"/status/\d+", url):
        return ("tweet", url)
    if h == "pokemon.gamespress.com":
        return ("press", url)
    if (h in ("pokemon.com", "pokemon.co.jp", "portal-pokemon.com")
            or h.endswith((".pokemon.com", ".pokemon.co.jp", ".portal-pokemon.com"))):
        return ("sito", url)
    return None


def _leggi_coda(coda):
    """Dati riconosciuti nella coda della nota, o None se c'è altro."""
    dati, resto = {}, coda
    while True:
        resto = resto.lstrip(" ,;.").rstrip()
        if resto in ("", "."):
            return dati
        for chiave, rx in _CODA:
            m = rx.match(resto)
            if not m:
                continue
            if chiave == "lingua":
                lingua = m.group(1).strip().lower()
                if lingua not in LINGUE_NOTE or "lingua" in dati:
                    continue
                dati["lingua"] = lingua[:1].upper() + lingua[1:]
            elif chiave == "data":
                mese = MESI_NUM.get(m.group(2).lower())
                if not mese or "data" in dati:
                    continue
                dati["data"] = f"{int(m.group(1)):02d}-{mese:02d}-{m.group(3)}"
            elif chiave == "archivio":
                if "archivio" in dati:
                    continue
                dati["archivio"] = m.group(1)
            elif chiave == "archiviato":
                dati["archiviato"] = True
            else:
                dati["youtube"] = True
            resto = resto[m.end():]
            break
        else:
            return None


def struttura(testo):
    """Parametri di {{ref}} (lista di «chiave=valore») per una nota testuale
    di forma riconosciuta, oppure None se va lasciata com'è."""
    m = LINK_RE.match(testo)
    if not m:
        return None
    url, titolo = m.group(1), m.group(2).strip()
    dati = _leggi_coda(testo[m.end():])
    if dati is None:
        return None

    # |archivio= solo se la nota ha DUE link: l'originale e, dopo, la copia
    # archiviata. Una nota che linka soltanto la copia (web.archive.org,
    # archive.is) resta una nota testuale con quel link.
    archivio = dati.get("archivio")
    if dati.get("archiviato"):
        return None              # «(archiviato)» senza un secondo link: resta testo
    if archivio and _host(url) in ("web.archive.org", "archive.is", "archive.ph",
                                   "archive.today"):
        return None              # due copie archiviate: resta testo
    originale = url
    tipo = tipo_url(originale)
    if dati.get("youtube") and (not tipo or tipo[0] != "video"):
        return None

    pezzi = []
    if tipo:
        chiave, valore = tipo
        if chiave == "tweet":
            a = re.match(r"Tweet di (.+?)(?:\s*" + _PIPE + r"\s*(?:Twitter|X)(?:\.com)?)?\.?$",
                         titolo)
            pezzi.append(f"tweet={valore}")
            pezzi.append(f"autore={a.group(1).strip()}" if a else f"titolo={titolo}")
        else:
            if chiave == "video":
                titolo = re.sub(r"\s*" + _PIPE + r"\s*YouTube(?:\.com)?$", "",
                                titolo, flags=re.I)
            pezzi += [f"{chiave}={valore}", f"titolo={titolo}"]
            if chiave == "video":
                t = re.search(r"[?&#]t=(\d+[hms\d]*)", originale)
                if t:
                    pezzi.append(f"minuto={t.group(1)}")
    elif archivio or dati.get("lingua") or dati.get("data"):
        corpo = f"[{url} {titolo}]"               # nota testuale decorata
        pezzi.append(("1=" if "=" in corpo else "") + corpo)
    else:
        return None                               # nulla da strutturare
    for chiave in ("data", "lingua"):
        if dati.get(chiave):
            pezzi.append(f"{chiave}={dati[chiave]}")
    if archivio:
        pezzi.append(f"archivio={archivio}")
    return pezzi


def componi(nota, gruppo="converti", pipe="nowiki", ripara_nomi=False,
        fonti="strutturate"):
    """Wikitext {{ref|…}} equivalente alla nota, oppure None se non convertibile."""
    if nota.problemi:
        if not (ripara_nomi and all("marcatore rotto" in p for p in nota.problemi)):
            return None
    if nota.attr:
        return None
    if nota.gruppo and gruppo == "tieni":
        return None
    testo = nota.testo.strip()
    if not testo and not nota.nome and not nota.gruppo:
        return None
    if testo and _pipa_di_primo_livello(testo):
        if pipe == "lascia":
            return None
        # <nowiki>|</nowiki> funziona sia per un «|» di testo sia per uno dentro un
        # link esterno; {{!}} invece non regge dentro i link (verificato).
        testo = "<nowiki>|</nowiki>".join(_spezza_args(testo))
    pezzi = []
    strutturata = struttura(testo) if testo and fonti == "strutturate" else None
    if strutturata:
        pezzi += strutturata
    elif testo:
        pezzi.append(("1=" if "=" in testo else "") + testo)
    if nota.nome:
        pezzi.append("name=" + nota.nome)
    if nota.gruppo and gruppo == "converti":
        pezzi.append("group=" + nota.gruppo)
    if not pezzi:
        return None
    return "{{ref|" + "|".join(pezzi) + "}}"


def converti(testo, gruppo="converti", pipe="nowiki", ripara_nomi=False,
        fonti="strutturate"):
    """Converte le note legacy di un wikitext.

    Restituisce (nuovo_testo, note_convertite, note_saltate, intervalli_nuovi),
    dove intervalli_nuovi sono gli (inizio, fine) dei {{ref|…}} inseriti.
    """
    note = trova_note(testo)
    convertite, saltate, intervalli = [], [], []
    pezzi, pos, cursore = [], 0, 0
    for nota in note:
        fuori = testo[pos:nota.inizio]
        inizio_nuovo = cursore + len(fuori)
        nuovo = componi(nota, gruppo, pipe, ripara_nomi, fonti)
        if nuovo is None:
            saltate.append(nota)
            nuovo = testo[nota.inizio:nota.fine]   # lasciata com'è
        else:
            convertite.append(nota)
        pezzi.append(fuori)
        pezzi.append(nuovo)
        cursore = inizio_nuovo + len(nuovo)
        intervalli.append((inizio_nuovo, cursore))
        pos = nota.fine
    pezzi.append(testo[pos:])
    return "".join(pezzi), convertite, saltate, intervalli


def verifica(vecchio, nuovo, intervalli=(), gruppo="converti", pipe="nowiki",
             ripara_nomi=False, fonti="strutturate"):
    """Controlla che la conversione non cambi nulla oltre alla forma delle note.

    ``intervalli`` sono gli (inizio, fine) in cui cadono le note nel testo nuovo
    (convertite o lasciate invariate), restituiti da converti: servono per
    confrontare il testo *fuori* dalle note fra le due versioni, dove il vecchio
    marcatore non c'è più.
    """
    problemi = []
    note_vecchie = trova_note(vecchio)
    note_nuove = trova_note(nuovo)

    def fuori(testo, esclusioni):
        out, pos = [], 0
        for inizio, fine in sorted(esclusioni):
            out.append(testo[pos:inizio])
            pos = fine
        out.append(testo[pos:])
        return "".join(out)

    attese = [n for n in note_vecchie
              if componi(n, gruppo, pipe, ripara_nomi, fonti) is not None]
    if len(note_nuove) != len(note_vecchie) - len(attese):
        problemi.append(
            f"note legacy rimaste: attese {len(note_vecchie) - len(attese)}, "
            f"trovate {len(note_nuove)}")
    if not intervalli:
        intervalli = [(n.inizio, n.fine) for n in note_nuove]
    if fuori(vecchio, [(n.inizio, n.fine) for n in note_vecchie]) != \
            fuori(nuovo, intervalli):
        problemi.append("il testo fuori dalle note è cambiato")
    return problemi


def note_lasciate(nuovo):
    """Note legacy rimaste nel testo nuovo, con il motivo (per il report)."""
    return [(n.riga, n.problemi or ([f"group={n.gruppo}"] if n.gruppo else []))
            for n in trova_note(nuovo)]


def elenco_note(testo, convertito=False, **opzioni):
    """Sequenza di note (originali o convertite) per il confronto in anteprima."""
    note = trova_note(testo)
    righe, gruppi = [], {}
    for n in note:
        if convertito:
            nuovo = componi(n, **opzioni)
            if nuovo is None:
                return None      # pagina da escludere dal confronto
            righe.append(nuovo)
        else:
            righe.append(testo[n.inizio:n.fine])
        if n.gruppo:
            gruppi[n.gruppo] = gruppi.get(n.gruppo, 0) + 1
    out = "\n".join(righe)
    for gruppo in gruppi:
        if gruppo == "Citazione":
            out += "\n{{references|cit=yes}}"
        else:
            out += f'\n<references group="{gruppo}" />'
    return out + "\n{{references}}\n"


# ────────────────────────────────────────────────────────────────────────────
# accesso al wiki (lettura)
# ────────────────────────────────────────────────────────────────────────────

def _api(params, post=False):
    dati = urllib.parse.urlencode(params).encode("utf-8")
    url = API if post else API + "?" + dati.decode("utf-8")
    req = urllib.request.Request(url, data=dati if post else None,
                                 headers={"User-Agent": UA})
    with _OPENER.open(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def scarica_pagina(titolo):
    """Wikitext corrente di una pagina."""
    d = _api({"action": "query", "prop": "revisions", "rvprop": "content|ids",
              "rvslots": "main", "titles": titolo, "format": "json",
              "formatversion": "2"})
    pag = d["query"]["pages"][0]
    if pag.get("missing"):
        raise SystemExit(f"pagina inesistente: {titolo}")
    return pag["revisions"][0]["slots"]["main"]["content"]


def scarica_blocco(titoli):
    """Wikitext di più pagine in una sola richiesta (max 50 titoli)."""
    d = _api({"action": "query", "prop": "revisions",
              "rvprop": "content|ids|timestamp", "rvslots": "main",
              "titles": "|".join(titoli), "format": "json",
              "formatversion": "2"})
    out = {}
    for pag in d["query"].get("pages", []):
        if pag.get("missing") or "revisions" not in pag:
            continue
        rev = pag["revisions"][0]
        out[pag["title"]] = {"revid": rev["revid"],
                             "timestamp": rev.get("timestamp"),
                             "text": rev["slots"]["main"]["content"]}
    return out


def elenca_pagine(probe, namespace="0", limite=None):
    """Titoli che soddisfano una ricerca insource."""
    titoli, offset = [], 0
    while True:
        d = _api({"action": "query", "list": "search", "srsearch": probe,
                  "srnamespace": namespace, "srlimit": "50", "sroffset": str(offset),
                  "format": "json", "formatversion": "2"})
        titoli += [p["title"] for p in d["query"]["search"]]
        if limite and len(titoli) >= limite:
            return titoli[:limite]
        if "continue" in d:
            offset = d["continue"]["sroffset"]
            time.sleep(0.5)
        else:
            return titoli


# ────────────────────────────────────────────────────────────────────────────
# comandi
# ────────────────────────────────────────────────────────────────────────────

def _righe_corpus(percorso):
    """Coppie (nome, wikitext) da un file o da una cartella (con index.json)."""
    if os.path.isdir(percorso):
        indice = os.path.join(percorso, "index.json")
        if os.path.exists(indice):
            dati = json.load(open(indice, encoding="utf-8"))
            for titolo, info in sorted(dati.items()):
                with open(os.path.join(percorso, info["file"]), encoding="utf-8") as f:
                    yield titolo, f.read()
            return
        for nome in sorted(os.listdir(percorso)):
            if nome.endswith(".wiki"):
                with open(os.path.join(percorso, nome), encoding="utf-8") as f:
                    yield nome[:-5], f.read()
        return
    with open(percorso, encoding="utf-8") as f:
        yield os.path.basename(percorso), f.read()


def _opz(args):
    return {"gruppo": args.gruppo, "pipe": args.pipe,
            "ripara_nomi": args.ripara_nomi, "fonti": args.fonti}


def cmd_scarica(args):
    """Scarica in locale le pagine con note legacy (corpus di lavoro)."""
    os.makedirs(args.dir, exist_ok=True)
    indice_path = os.path.join(args.dir, "index.json")
    indice = {}
    if os.path.exists(indice_path):
        indice = json.load(open(indice_path, encoding="utf-8"))
    titoli = {}
    for ns in args.namespaces.split(","):
        for probe in ('insource:"<ref"', 'insource:"#tag:"'):
            trovati = elenca_pagine(probe, ns.strip(), args.limite)
            print(f"ns={ns} {probe}: {len(trovati)} pagine", file=sys.stderr)
            for t in trovati:
                titoli[t] = ns.strip()
    da_fare = [t for t in sorted(titoli) if t not in indice]
    print(f"pagine uniche: {len(titoli)} (già in cache: {len(titoli) - len(da_fare)})",
          file=sys.stderr)
    for i in range(0, len(da_fare), 50):
        for titolo, info in scarica_blocco(da_fare[i:i + 50]).items():
            nome = re.sub(r"[^\w.()\- ]+", "_", titolo.replace("/", "_")) + ".wiki"
            with open(os.path.join(args.dir, nome), "w", encoding="utf-8") as f:
                f.write(info["text"])
            indice[titolo] = {"file": nome, "ns": titoli.get(titolo),
                              "revid": info["revid"],
                              "timestamp": info["timestamp"],
                              "bytes": len(info["text"].encode("utf-8"))}
        json.dump(indice, open(indice_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print(f"  scaricate {min(i + 50, len(da_fare))}/{len(da_fare)}", file=sys.stderr)
        time.sleep(0.5)
    print(f"indice: {indice_path} ({len(indice)} pagine)")
    return 0


def cmd_analizza(args):
    tot = {"pagine": 0, "pagine da convertire": 0, "note": 0, "convertibili": 0,
           "saltate": 0, "group": 0, "problemi": 0, "references": 0}
    forme, anomalie, per_gruppo = {}, [], {}
    disallineate = []
    for titolo, testo in _righe_corpus(args.percorsi[0]):
        tot["pagine"] += 1
        note = trova_note(testo)
        tot["note"] += len(note)
        tot["references"] += len(re.findall(r"<references\b", testo, re.I))
        # controllo di copertura: il parser deve vedere tutte le note presenti
        grezzo = (len(re.findall(r"<ref(?=[\s/>])", testo, re.I))
                  + len(TAGTAG_RE.findall(testo)))
        if grezzo != len(note):
            disallineate.append((titolo, grezzo, len(note)))
        convertibili = 0
        for n in note:
            forma = ("<ref …/>" if n.tipo == "tag" and not n.testo
                     else "<ref>…</ref>" if n.tipo == "tag" else "{{#tag:ref|…}}")
            forme[forma] = forme.get(forma, 0) + 1
            if n.gruppo:
                tot["group"] += 1
                per_gruppo.setdefault(n.gruppo, set()).add(titolo)
            if not n.convertibile:
                tot["problemi"] += 1
                anomalie.append((titolo, n.riga, n.tipo, n.problemi,
                                 n.testo.strip()[:80]))
                continue
            if componi(n, **_opz(args)) is None:
                if n.gruppo and args.gruppo == "tieni":
                    tot["saltate"] += 1
                else:
                    tot["saltate"] += 1
                    anomalie.append((titolo, n.riga, n.tipo,
                                     ["conversione non possibile (pipe o attributi)"],
                                     n.testo.strip()[:80]))
                continue
            tot["convertibili"] += 1
            convertibili += 1
        if convertibili:
            tot["pagine da convertire"] += 1
    print("=== censimento ===")
    for k, v in tot.items():
        print(f"  {k:22s} {v}")
    print("=== forme delle note ===")
    for k, v in sorted(forme.items(), key=lambda x: -x[1]):
        print(f"  {k:22s} {v}")
    if per_gruppo:
        print("=== group= ===")
        for k, v in sorted(per_gruppo.items(), key=lambda x: -len(x[1])):
            print(f"  {k:22s} pagine: {len(v)}")
    if disallineate:
        print(f"=== copertura del parser ({len(disallineate)} pagine) ===")
        for titolo, g, p in disallineate[:args.max_anomalie]:
            print(f"  {titolo}: nel testo {g} note grezze, il parser ne vede {p}"
                  f" (differenza di solito dentro <nowiki> o documentazione)")
    if anomalie:
        print(f"=== anomalie ({len(anomalie)}) ===")
        for titolo, riga, tipo, prob, testo in anomalie[:args.max_anomalie]:
            print(f"  {titolo} riga {riga} [{tipo}]: {'; '.join(prob)}")
            print(f"      {testo}")
        if len(anomalie) > args.max_anomalie:
            print(f"  … e altre {len(anomalie) - args.max_anomalie} anomalie")
    return 0


def _stampa_diff(vecchio, nuovo, fromfile, tofile):
    print("".join(difflib.unified_diff(
        vecchio.splitlines(keepends=True), nuovo.splitlines(keepends=True),
        fromfile=fromfile, tofile=tofile)), end="")


def cmd_converti(args):
    testo = open(args.file, encoding="utf-8").read()
    nuovo, convertite, saltate, intervalli = converti(testo, **_opz(args))
    if args.diff:
        _stampa_diff(testo, nuovo, args.file, args.file + " (convertito)")
    elif args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(nuovo)
    else:
        sys.stdout.write(nuovo)
    print(f"# note convertite: {len(convertite)}; lasciate invariate: {len(saltate)}",
          file=sys.stderr)
    for n in saltate:
        print(f"#   riga {n.riga}: {n.problemi or ['group=' + str(n.gruppo)]}",
              file=sys.stderr)
    problemi = verifica(testo, nuovo, intervalli, **_opz(args))
    for p in problemi:
        print(f"# VERIFICA: {p}", file=sys.stderr)
    return 0 if not problemi else 1


def cmd_piano(args):
    piano, con_problemi = {}, []
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
    for titolo, testo in _righe_corpus(args.corpus):
        nuovo, convertite, saltate, intervalli = converti(testo, **_opz(args))
        if not convertite:
            continue
        problemi = verifica(testo, nuovo, intervalli, **_opz(args))
        piano[titolo] = {
            "note_convertite": len(convertite),
            "note_lasciate": [{"riga": n.riga,
                               "motivo": n.problemi or (
                                   [f"group={n.gruppo}"] if n.gruppo else [])}
                              for n in saltate],
            "problemi_verifica": problemi,
            "nuovo_wikitext": nuovo,
        }
        if problemi:
            con_problemi.append(titolo)
        if args.outdir:
            nome = re.sub(r"[^\w.()\- ]+", "_", titolo.replace("/", "_")) + ".wiki"
            with open(os.path.join(args.outdir, nome), "w", encoding="utf-8") as f:
                f.write(nuovo)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(piano, f, ensure_ascii=False, indent=1)
    print(f"piano scritto in {args.out}: {len(piano)} pagine, "
          f"{sum(v['note_convertite'] for v in piano.values())} note da convertire; "
          f"pagine con problemi di verifica: {len(con_problemi)}")
    if args.outdir:
        print(f"wikitext convertito in {args.outdir}/ ({len(piano)} file)")
    for t in con_problemi[:20]:
        print(f"  ! {t}")
    return 0


def cmd_titolo(args):
    testo = scarica_pagina(args.titolo)
    nuovo, convertite, saltate, intervalli = converti(testo, **_opz(args))
    if args.diff:
        _stampa_diff(testo, nuovo, args.titolo, args.titolo + " (convertito)")
    else:
        sys.stdout.write(nuovo)
    print(f"# note convertite: {len(convertite)}; lasciate invariate: {len(saltate)}",
          file=sys.stderr)
    problemi = verifica(testo, nuovo, intervalli, **_opz(args))
    for p in problemi:
        print(f"# VERIFICA: {p}", file=sys.stderr)
    return 0 if not problemi else 1


def cmd_estrai_note(args):
    testo = scarica_pagina(args.titolo) if args.titolo else \
        open(args.file, encoding="utf-8").read()
    harness = elenco_note(testo, convertito=args.convertito, **_opz(args))
    if harness is None:
        raise SystemExit("pagina non adatta al confronto (note non convertibili)")
    sys.stdout.write(harness)
    return 0


# ────────────────────────────────────────────────────────────────────────────
# credenziali di Pywikibot
# ────────────────────────────────────────────────────────────────────────────
#
# Ordine di ricerca della cartella di Pywikibot (quella con user-config.py):
#   1. --pywikibot-dir
#   2. variabile d'ambiente PYWIKIBOT_DIR
#   3. profilo PowerShell (Documenti\PowerShell\Profile.ps1 e varianti):
#      $env:PYWIKIBOT_DIR = "…", SetEnvironmentVariable('PYWIKIBOT_DIR', …),
#      -dir:"…" in una funzione/alias, oppure un qualunque percorso citato nel
#      profilo che contenga user-config.py
#   4. %APPDATA%\Pywikibot, ~/.pywikibot, la cartella corrente
# Dalla cartella si leggono user-config.py (nome utente, password_file) e
# user-password.py (BotPassword o password), senza importare Pywikibot.

FAMIGLIA = "pokemoncentral"
LINGUA = "it"
_STRINGA_PS = r"""(?:"([^"]*)"|'([^']*)')"""


def _documenti():
    """Cartelle «Documenti» possibili: Windows (anche OneDrive), Linux, macOS."""
    basi = []
    for chiave in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(chiave):
            basi.append(Path(os.environ[chiave]))
    home = Path.home()
    basi += [home / "OneDrive", home]
    return [b / nome for b in basi for nome in ("Documents", "Documenti")]


def profili_powershell():
    """Profili PowerShell presenti (PowerShell 7 e Windows PowerShell)."""
    trovati, visti = [], set()
    for doc in _documenti():
        for sotto in ("PowerShell", "WindowsPowerShell"):
            for nome in ("Profile.ps1", "profile.ps1",
                         "Microsoft.PowerShell_profile.ps1"):
                p = doc / sotto / nome
                if not p.is_file():
                    continue
                chiave = str(p.resolve()).lower()
                if chiave not in visti:
                    visti.add(chiave)
                    trovati.append(p)
    return trovati


def _espandi_ps(valore, variabili):
    """Espande $env:X, ${env:X}, $HOME, $variabili del profilo e ~."""
    def env(m):
        nome = m.group(1)
        return os.environ.get(nome, variabili.get("env:" + nome.lower(), m.group(0)))

    v = re.sub(r"\$\{env:(\w+)\}", env, valore, flags=re.I)
    v = re.sub(r"\$env:(\w+)", env, v, flags=re.I)

    def var(m):
        nome = m.group(1).lower()
        if nome == "home":
            return str(Path.home())
        return variabili.get(nome, m.group(0))

    v = re.sub(r"\$(\w+)", var, v)
    if v.startswith("~"):
        v = str(Path.home()) + v[1:]
    return v


def _ha_config(percorso):
    """Cartella con user-config.py ricavata da un percorso (cartella o file)."""
    try:
        p = Path(percorso)
        if p.is_dir() and (p / "user-config.py").is_file():
            return p
        if p.is_file() and (p.parent / "user-config.py").is_file():
            return p.parent
    except (OSError, ValueError):
        pass
    return None


def cartella_da_profilo(percorso):
    """Cartella di Pywikibot indicata in un profilo PowerShell, o None."""
    testo = Path(percorso).read_text(encoding="utf-8-sig", errors="replace")
    variabili, prioritari, altri = {}, [], []

    def val(m, i):
        return m.group(i) if m.group(i) is not None else m.group(i + 1)

    for riga in testo.splitlines():
        r = riga.strip()
        if not r or r.startswith("#"):
            continue
        m = re.match(r"\$(env:)?(\w+)\s*=\s*" + _STRINGA_PS, r, re.I)
        if m:
            chiave = ("env:" if m.group(1) else "") + m.group(2).lower()
            valore = _espandi_ps(val(m, 3), variabili)
            variabili[chiave] = valore
            (prioritari if m.group(2).upper() == "PYWIKIBOT_DIR" else altri).append(valore)
        m = re.search(r"SetEnvironmentVariable\(\s*" + _STRINGA_PS + r"\s*,\s*"
                      + _STRINGA_PS, r, re.I)
        if m and val(m, 1).upper() == "PYWIKIBOT_DIR":
            prioritari.append(_espandi_ps(val(m, 3), variabili))
        m = re.search(r"env:PYWIKIBOT_DIR\W.*?-Value\s+" + _STRINGA_PS, r, re.I)
        if m:
            prioritari.append(_espandi_ps(val(m, 1), variabili))
        for m in re.finditer(r"-dir:" + _STRINGA_PS, r, re.I):
            prioritari.append(_espandi_ps(val(m, 1), variabili))
        for m in re.finditer(r"-dir:([^\s\"';]+)", r, re.I):
            prioritari.append(_espandi_ps(m.group(1), variabili))
        for m in re.finditer(_STRINGA_PS, r):
            altri.append(_espandi_ps(val(m, 1), variabili))
    for candidato in prioritari + altri:
        cartella = _ha_config(candidato)
        if cartella:
            return cartella
    return None


def cartella_pywikibot(esplicita=None):
    """(cartella, come è stata trovata) della configurazione di Pywikibot."""
    prove = []
    if esplicita:
        prove.append((esplicita, "--pywikibot-dir"))
    if os.environ.get("PYWIKIBOT_DIR"):
        prove.append((os.environ["PYWIKIBOT_DIR"], "variabile PYWIKIBOT_DIR"))
    for profilo in profili_powershell():
        c = cartella_da_profilo(profilo)
        if c:
            prove.append((c, f"profilo PowerShell {profilo}"))
    if os.environ.get("APPDATA"):
        prove.append((Path(os.environ["APPDATA"]) / "Pywikibot", "%APPDATA%"))
    prove.append((Path.home() / ".pywikibot", "~/.pywikibot"))
    prove.append((Path.cwd(), "cartella corrente"))
    for percorso, origine in prove:
        c = _ha_config(percorso)
        if c:
            return c, origine
    profili = profili_powershell()
    raise SystemExit(
        "cartella di Pywikibot non trovata (manca user-config.py).\n"
        f"  profili PowerShell esaminati: {[str(p) for p in profili] or 'nessuno'}\n"
        "  indicala con --pywikibot-dir o con la variabile PYWIKIBOT_DIR")


# ────────────────────────────────────────────────────────────────────────────
# scrittura sul wiki tramite Pywikibot
# ────────────────────────────────────────────────────────────────────────────
#
# Login, credenziali (user-config.py, user-password.py, BotPassword), famiglia,
# throttle e maxlag sono quelli di Pywikibot: refmigrate.py trova soltanto la
# cartella della configurazione (vedi cartella_pywikibot) e la passa a
# Pywikibot tramite PYWIKIBOT_DIR prima di importarlo.

def carica_pywikibot(cartella):
    """Importa Pywikibot usando la configurazione che sta in «cartella»."""
    if "pywikibot" in sys.modules:
        return sys.modules["pywikibot"]
    os.environ["PYWIKIBOT_DIR"] = str(cartella)
    try:
        import pywikibot
    except ImportError:
        raise SystemExit("Pywikibot non è installato: python -m pip install pywikibot")
    return pywikibot


def apri_sito(pywikibot, famiglia=None, lingua=None, utente=None):
    """Sito di Pokémon Central Wiki secondo la configurazione di Pywikibot."""
    cfg = pywikibot.config
    try:
        site = pywikibot.Site(lingua or cfg.mylang, famiglia or cfg.family,
                              user=utente)
    except pywikibot.exceptions.Error as e:
        raise SystemExit(f"Pywikibot non riesce ad aprire il sito: {e}")
    host = site.hostname()
    # il piano è tarato sulle revisioni di PCW: mai scrivere su un altro wiki
    if not host.endswith("pokemoncentral.it"):
        raise SystemExit(f"il sito configurato è {site} ({host}), non Pokémon "
                         "Central Wiki: indica --famiglia e --lingua")
    return site


def sessione_pulita(pywikibot, site):
    """Evita i cookie di sessione vecchi nel file pywikibot-<utente>.lwp.

    site.login() ricarica quel file. Se contiene un «wiki2_session» salvato in
    passato per un dominio diverso (es. host-only «wiki.pokemoncentral.it»
    accanto a «.wiki.pokemoncentral.it»), al server arrivano due sessioni, ne
    legge una sbagliata e risponde badtoken / «incorrect login token» a ogni
    richiesta. Dopo il caricamento si scartano quindi i cookie del wiki: il
    login ne crea di nuovi e Pywikibot salva un file .lwp pulito.
    """
    from pywikibot.comms import http as pwhttp
    jar = pwhttp.cookie_jar
    if getattr(jar, "_refmigrate", False):
        return
    dominio = site.hostname().split(".", 1)[-1]   # pokemoncentral.it
    carica = jar.load

    def load(*a, **kw):
        carica(*a, **kw)
        for c in list(jar):
            if c.domain.lstrip(".").endswith(dominio):
                jar.clear(c.domain, c.path, c.name)

    jar.load = load
    jar._refmigrate = True


def accedi(pywikibot, site):
    """Login con le credenziali di Pywikibot; restituisce le info dell'utente."""
    sessione_pulita(pywikibot, site)
    try:
        site.login()
    except pywikibot.exceptions.Error as e:
        raise SystemExit(f"accesso non riuscito per {site.username()}: {e}")
    if not site.logged_in():
        raise SystemExit(f"accesso non riuscito per {site.username()}")
    return site.userinfo


def cmd_credenziali(args):
    """Mostra configurazione e utente che Pywikibot userebbe; con --login
    prova l'accesso, senza salvare nulla."""
    cartella, origine = cartella_pywikibot(args.pywikibot_dir)
    print(f"cartella Pywikibot: {cartella} (trovata tramite {origine})")
    pywikibot = carica_pywikibot(cartella)
    site = apri_sito(pywikibot, args.famiglia, args.lingua, args.utente)
    print(f"  versione Pywikibot  {pywikibot.__version__}")
    print(f"  sito                {site} ({site.hostname()})")
    print(f"  utente              {site.username()}")
    print(f"  password_file       {pywikibot.config.password_file}")
    if args.login:
        info = accedi(pywikibot, site)
        print(f"accesso riuscito come {info.get('name')}; gruppi: "
              f"{', '.join(info.get('groups', []))}; "
              f"flag bot: {'sì' if site.has_right('bot') else 'no'}")
    return 0


def imposta_attesa(throttle, secondi):
    """Imposta la pausa fra i salvataggi su un throttle di Pywikibot.

    Compatibile con le versioni vecchie (setDelays/getDelay, fino alla 10.2)
    e nuove (set_delays/get_delay, dalla 10.3)."""
    imposta = getattr(throttle, "set_delays", None) or getattr(throttle, "setDelays", None)
    if imposta:
        imposta(writedelay=secondi)
    throttle.writedelay = secondi        # senza i limiti min/maxthrottle


def attesa_effettiva(throttle):
    """(pausa effettiva fra i salvataggi, numero di processi Pywikibot attivi)."""
    leggi = getattr(throttle, "get_delay", None) or getattr(throttle, "getDelay", None)
    processi = getattr(throttle, "process_multiplicity", 1) or 1
    if leggi:
        try:
            return float(leggi(write=True)), processi
        except TypeError:
            pass
    return float(throttle.writedelay) * processi, processi


def applica_piano(piano, args):
    """Salva su PCW le pagine del piano, una alla volta, con Pywikibot."""
    voci = [(t, v) for t, v in sorted(piano.items()) if not v["problemi_verifica"]]
    escluse = len(piano) - len(voci)
    if args.max_salvataggi:
        voci = voci[:args.max_salvataggi]
    if not voci:
        print("nessuna pagina da salvare")
        return 0

    cartella, origine = cartella_pywikibot(args.pywikibot_dir)
    pywikibot = carica_pywikibot(cartella)
    exc = pywikibot.exceptions
    # L'attesa va impostata PRIMA di creare il sito (il throttle copia
    # config.put_throttle quando nasce) e poi applicata anche al throttle già
    # esistente, nel caso il sito fosse stato creato in precedenza.
    if args.attesa is not None:
        pywikibot.config.put_throttle = args.attesa
    site = apri_sito(pywikibot, args.famiglia, args.lingua, args.utente)
    if args.attesa is not None:
        imposta_attesa(site.throttle, args.attesa)
    print(f"\nPywikibot: {cartella} (trovata tramite {origine})")
    print(f"sito:      {site} — utente {site.username()}")
    if not args.oggetto.lower().startswith("bot:"):
        args.oggetto = "Bot: " + args.oggetto
    print(f"oggetto:   «{args.oggetto}»")
    attesa, processi = attesa_effettiva(site.throttle)
    print(f"pausa fra i salvataggi: {attesa:g} s"
          + (f" (×{processi} processi Pywikibot attivi)" if processi > 1 else ""))
    if escluse:
        print(f"escluse per problemi di verifica: {escluse}")
    if not args.si:
        if not sys.stdin.isatty():
            raise SystemExit("serve una conferma: rilancia con --si")
        risposta = input(f"\nSalvo {len(voci)} pagine su PCW? [s/N] ")
        if risposta.strip().lower() not in ("s", "si", "sì", "y", "yes"):
            print("annullato: nessuna modifica salvata")
            return 0

    info = accedi(pywikibot, site)
    bot = site.has_right("bot")
    print(f"accesso effettuato come {info.get('name')}"
          f"{' (flag bot attivo)' if bot else ''}\n")

    salvate = gia = conflitti = errori = consecutivi = 0
    try:
        with open(args.log, "a", encoding="utf-8") as log:
            for i, (titolo, dati) in enumerate(voci, 1):
                pre = f"[{i}/{len(voci)}]"
                with open(os.path.join(args.outdir, dati["file"]),
                          encoding="utf-8") as f:
                    nuovo = f.read()
                page = pywikibot.Page(site, titolo)
                try:
                    if not page.exists():
                        errori += 1
                        print(f"{pre} ! pagina inesistente: {titolo}")
                        continue
                    # la pagina deve essere ancora quella convertita: se nel
                    # frattempo qualcuno l'ha modificata, si salta
                    if page.latest_revision_id != dati["base_revid"]:
                        conflitti += 1
                        print(f"{pre} ~ modificata nel frattempo, saltata: {titolo}")
                        continue
                    if page.text == nuovo:
                        gia += 1
                        print(f"{pre} = già a posto: {titolo}")
                        continue
                    page.text = nuovo
                    page.save(summary=args.oggetto, minor=False, bot=bot,
                              nocreate=True, quiet=True)
                except exc.EditConflictError:
                    conflitti += 1
                    print(f"{pre} ~ conflitto di modifica, saltata: {titolo}")
                    continue
                except exc.Error as e:
                    errori += 1
                    consecutivi += 1
                    print(f"{pre} ! errore su {titolo}: {e}")
                    if consecutivi >= 5:
                        print("5 errori di fila: interrompo")
                        break
                    continue
                consecutivi = 0
                salvate += 1
                nuova_rev = page.latest_revision_id
                print(f"{pre} + {titolo} → rev {nuova_rev}")
                log.write(json.dumps({"titolo": titolo, "da": dati["base_revid"],
                                      "a": nuova_rev}, ensure_ascii=False) + "\n")
                log.flush()
    except KeyboardInterrupt:
        print("\ninterrotto: rilanciando `run` si riprende da dove si era rimasti")
    print(f"\nsalvate: {salvate}  già a posto: {gia}  saltate per conflitto: "
          f"{conflitti}  errori: {errori}")
    print(f"registro delle revisioni salvate: {args.log}")
    return 0 if errori == 0 else 1


def cmd_run(args):
    """Tutto il necessario in un colpo solo: elenco, download, conversione,
    verifica, report e scrittura su PCW tramite Pywikibot.

    Le pagine già convertite non ricompaiono nell'elenco, perché non contengono
    più nessuna nota vecchia: rilanciare il comando riprende da dove si era
    rimasti. Con --prova si ferma prima di scrivere.
    """
    os.makedirs(args.dir, exist_ok=True)
    os.makedirs(args.outdir, exist_ok=True)

    # 1) elenco aggiornato delle pagine che hanno ancora note vecchie
    titoli = set()
    for ns in args.namespaces.split(","):
        for probe in ('insource:"<ref"', 'insource:"#tag:"'):
            trovati = elenca_pagine(probe, ns.strip(), args.limite)
            print(f"  ns={ns} {probe}: {len(trovati)} pagine", file=sys.stderr)
            titoli.update(trovati)
    titoli = sorted(titoli)
    print(f"pagine con note legacy: {len(titoli)}", file=sys.stderr)

    # 2) download, con la revisione di base per il controllo dei conflitti
    dati = {}
    for i in range(0, len(titoli), 50):
        dati.update(scarica_blocco(titoli[i:i + 50]))
        print(f"  scaricate {min(i + 50, len(titoli))}/{len(titoli)}",
              file=sys.stderr)
        time.sleep(0.5)

    # 3) conversione, verifica e scrittura dei file
    piano, con_problemi, righe_lasciate, anomalie = {}, [], [], []
    note_convertite = 0
    for titolo in titoli:
        info = dati.get(titolo)
        if info is None:
            continue
        testo = info["text"]
        nuovo, convertite, saltate, intervalli = converti(testo, **_opz(args))
        for n in saltate:
            righe_lasciate.append((titolo, n.riga,
                                   n.problemi or [f"group={n.gruppo}"]))
        if not convertite:
            continue
        problemi = verifica(testo, nuovo, intervalli, **_opz(args))
        nome = re.sub(r"[^\w.()\- ]+", "_", titolo.replace("/", "_")) + ".wiki"
        with open(os.path.join(args.dir, nome), "w", encoding="utf-8") as f:
            f.write(testo)
        with open(os.path.join(args.outdir, nome), "w", encoding="utf-8") as f:
            f.write(nuovo)
        piano[titolo] = {"file": nome, "base_revid": info["revid"],
                         "note_convertite": len(convertite),
                         "note_lasciate": len(saltate),
                         "problemi_verifica": problemi}
        note_convertite += len(convertite)
        if problemi:
            con_problemi.append((titolo, problemi))
        for n in saltate:
            if n.problemi:
                anomalie.append((titolo, n.riga, n.tipo, n.problemi,
                                 testo[n.inizio:n.fine][:120]))
    with open(args.piano, "w", encoding="utf-8") as f:
        json.dump(piano, f, ensure_ascii=False, indent=1)
    indice = {t: {"file": v["file"], "revid": v["base_revid"]}
              for t, v in piano.items()}
    with open(os.path.join(args.dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=1, sort_keys=True)

    # 4) report
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(rapporto(piano, note_convertite, len(titoli), righe_lasciate,
                         anomalie, con_problemi, args))

    print(f"\npagine da modificare: {len(piano)}")
    print(f"note da convertire:   {note_convertite}")
    print(f"note lasciate:        {len(righe_lasciate)}")
    print(f"problemi di verifica: {len(con_problemi)} (pagine escluse dal salvataggio)")
    print(f"anomalie:             {len(anomalie)}")
    print(f"report: {args.report} — piano: {args.piano} — wikitext: {args.outdir}/")

    # 5) scrittura su PCW
    if args.prova:
        print("\nmodalità prova: nessuna modifica salvata")
        return 0 if not con_problemi else 1
    return applica_piano(piano, args)


def rapporto(piano, note_convertite, pagine_viste, righe_lasciate, anomalie,
             con_problemi, args):
    """Report leggibile della migrazione."""
    righe = ["# Migrazione delle note al template {{ref}}", ""]
    righe.append(f"* pagine con note vecchie: {pagine_viste}")
    righe.append(f"* pagine da modificare: {len(piano)}")
    righe.append(f"* note da convertire: {note_convertite}")
    righe.append(f"* note lasciate invariate: {len(righe_lasciate)}")
    righe.append(f"* pagine con problemi di verifica: {len(con_problemi)}")
    righe.append(f"* anomalie: {len(anomalie)}")
    righe.append("")
    if con_problemi:
        righe.append("## Problemi di verifica (da controllare, NON caricare)")
        righe.append("")
        for titolo, problemi in con_problemi:
            righe.append(f"* **{titolo}**: {'; '.join(problemi)}")
        righe.append("")
    if anomalie:
        righe.append("## Note non convertibili (da sistemare a mano)")
        righe.append("")
        righe.append("| Pagina | Riga | Tipo | Motivo | Frammento |")
        righe.append("|---|---|---|---|---|")
        for titolo, riga, tipo, prob, frammento in anomalie:
            frammento = frammento.replace("|", "\\|").replace("\n", " ")
            righe.append(f"| {titolo} | {riga} | {tipo} | {'; '.join(prob)} "
                         f"| <code>{frammento}</code> |")
        righe.append("")
    if righe_lasciate:
        gruppi = {}
        for titolo, riga, motivo in righe_lasciate:
            gruppi.setdefault("; ".join(motivo), []).append(titolo)
        righe.append("## Motivi delle note lasciate")
        righe.append("")
        for motivo, titoli in sorted(gruppi.items(), key=lambda x: -len(x[1])):
            righe.append(f"* {len(titoli)}: {motivo}")
            righe.append(f"  * {', '.join(sorted(set(titoli))[:20])}")
        righe.append("")
    righe.append("## Opzioni di questa esecuzione")
    righe.append("")
    righe.append(f"* gruppi: {args.gruppo}")
    righe.append(f"* pipe: {args.pipe}")
    righe.append(f"* ripara nomi: {'sì' if args.ripara_nomi else 'no'}")
    righe.append("")
    return "\n".join(righe)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gruppo", choices=["converti", "tieni"],
                    default="converti",
                    help="note con group=: converti (default) o tieni invariate")
    ap.add_argument("--pipe", choices=["lascia", "nowiki"], default="nowiki",
                    help="«|» di primo livello: nowiki=scrive <nowiki>|</nowiki> "
                         "(default, resa identica), lascia=non tocca la nota")
    ap.add_argument("--fonti", choices=["strutturate", "testo"],
                    default="strutturate",
                    help="strutturate (default): YouTube, X, sito ufficiale, press "
                         "site e copie archiviate con i parametri di {{ref}}; "
                         "testo: nota sempre come testo libero")
    ap.add_argument("--ripara-nomi", action="store_true",
                    help="corregge i marcatori rotti «name=\"X />»")
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("scarica", help="scarica il corpus delle pagine con note legacy")
    p.add_argument("--dir", default="corpus")
    p.add_argument("--namespaces", default="0")
    p.add_argument("--limite", type=int)
    p.set_defaults(func=cmd_scarica)

    p = sub.add_parser("run",
                       help="fa tutto: elenco, download, conversione, verifica, "
                            "report e salvataggio su PCW")
    p.add_argument("--dir", default="corpus")
    p.add_argument("--outdir", default="nuovo")
    p.add_argument("--piano", default="piano.json")
    p.add_argument("--report", default="report_migrazione.md")
    p.add_argument("--log", default="salvataggi.jsonl",
                   help="registro delle revisioni salvate (per annullare)")
    p.add_argument("--namespaces", default="0")
    p.add_argument("--limite", type=int, help="massimo di pagine per ricerca")
    p.add_argument("--oggetto", default="Bot: Note convertite al template ref",
                   help="oggetto delle modifiche")
    p.add_argument("--prova", action="store_true",
                   help="prepara tutto ma non scrive su PCW")
    p.add_argument("--si", action="store_true",
                   help="non chiede conferma prima di salvare")
    p.add_argument("--max-salvataggi", type=int,
                   help="salva al massimo N pagine (per procedere a scaglioni)")
    p.add_argument("--attesa", type=float,
                   help="secondi fra un salvataggio e l'altro "
                        "(default: put_throttle di user-config.py)")
    p.add_argument("--pywikibot-dir",
                   help="cartella con user-config.py (altrimenti: PYWIKIBOT_DIR, "
                        "profilo PowerShell, %%APPDATA%%\\Pywikibot, ~/.pywikibot)")
    p.add_argument("--utente", help="nome utente (default: usernames di user-config.py)")
    p.add_argument("--famiglia", help="default: family di user-config.py")
    p.add_argument("--lingua", help="default: mylang di user-config.py")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("credenziali",
                       help="mostra sito e utente di Pywikibot; con --login prova l'accesso")
    p.add_argument("--pywikibot-dir")
    p.add_argument("--utente")
    p.add_argument("--famiglia", help="default: family di user-config.py")
    p.add_argument("--lingua", help="default: mylang di user-config.py")
    p.add_argument("--login", action="store_true",
                   help="prova anche l'accesso (non salva nulla)")
    p.set_defaults(func=cmd_credenziali)

    p = sub.add_parser("analizza", help="censimento e anomalie")
    p.add_argument("percorsi", nargs="+")
    p.add_argument("--max-anomalie", type=int, default=25)
    p.set_defaults(func=cmd_analizza)

    p = sub.add_parser("converti", help="converte un file")
    p.add_argument("file")
    p.add_argument("--out")
    p.add_argument("--diff", action="store_true")
    p.set_defaults(func=cmd_converti)

    p = sub.add_parser("piano", help="converte un corpus e scrive un piano JSON")
    p.add_argument("--corpus", required=True)
    p.add_argument("--out", default="piano.json")
    p.add_argument("--outdir", help="scrive anche il wikitext convertito, un file per pagina")
    p.set_defaults(func=cmd_piano)

    p = sub.add_parser("titolo", help="scarica una pagina dal wiki e la converte")
    p.add_argument("titolo")
    p.add_argument("--diff", action="store_true")
    p.set_defaults(func=cmd_titolo)

    p = sub.add_parser("estrai-note",
                       help="elenco delle note per il confronto in anteprima")
    p.add_argument("--titolo")
    p.add_argument("--file")
    p.add_argument("--convertito", action="store_true")
    p.set_defaults(func=cmd_estrai_note)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
