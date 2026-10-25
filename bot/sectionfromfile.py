#!/usr/bin/env python3
"""Sovrascrive singole sezioni di pagine esistenti leggendole da un file.

È l'equivalente di ``pagefromfile.py`` limitato alle sezioni: il file ha lo
stesso formato (``{{-start-}}`` ... ``{{-stop-}}``, titolo in grassetto sulla
prima riga), ma ogni blocco contiene solo le sezioni da sostituire, ciascuna
introdotta dal suo titolo (``==Testo==``). Tutto il resto della pagina sul wiki
resta com'è.

Esempio di file::

    {{-start-}}
    '''Wurmple (Sovrano dei Cieli 1)'''
    ==Testo==
    {{Cardtext/Header
    |type=Erba}}
    ...
    {{Cardtext/Footer}}
    {{-stop-}}

Per ogni sezione del blocco lo script cerca nella pagina la sezione con lo
stesso titolo e lo stesso livello e la sostituisce, fino alla sezione
successiva di livello uguale o superiore (come il pulsante "modifica" di
MediaWiki). Le pagine che non esistono non vengono mai create.

Argomenti dello script:

-file:xxx         File da leggere (predefinito: "dict.txt")
-begin:xxx        Marcatore di inizio pagina (predefinito: "{{-start-}}")
-end:xxx          Marcatore di fine pagina (predefinito: "{{-stop-}}")
-titlestart:xxx   Testo che apre il titolo (predefinito: ''')
-titleend:xxx     Testo che chiude il titolo (predefinito: ''')
-notitle          Accettato per compatibilità con pagefromfile: il titolo
                  non viene mai considerato parte delle sezioni

-summary:xxx      Oggetto della modifica. "{sezioni}" viene sostituito con
                  l'elenco delle sezioni modificate
-minor            Segna le modifiche come minori
-showdiff         Mostra il diff e chiede conferma per ogni pagina
                  (senza -showdiff né -always, chiede comunque conferma)
-always           Non chiede conferma

-nosubsections    Sostituisce solo il testo che precede la prima
                  sottosezione: le sottosezioni della pagina (per esempio
                  ===Pokédex=== sotto ==Testo==) restano intatte. In questa
                  modalità ogni titolo nel file è una sezione a sé
-dropsubsections  Consente di eliminare le sottosezioni della pagina che
                  non compaiono nel file. Senza questa opzione, se la
                  sezione sul wiki ha sottosezioni assenti dal file, la
                  pagina viene saltata
-ifmissing:xxx    Cosa fare se una sezione del file non c'è nella pagina:
                  "skippage" (predefinito) salta l'intera pagina,
                  "skipsection" salta solo quella sezione
-nocontent:xxx    Salta una sezione se sul wiki contiene già questo testo
                  (utile per rieseguire lo script senza rifare il lavoro)
-noredirect       Accettato per compatibilità: i redirect vengono sempre
                  saltati

Vanno bene anche gli argomenti globali di Pywikibot, per esempio -simulate.

Uso::

    python3 pwb.py sectionfromfile -file:testo.txt -notitle \\
        -summary:"Aggiornata sezione {sezioni}" -showdiff
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import pywikibot
from pywikibot.bot import CurrentPageBot, SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator

CTX_ATTR = '_section_ctx'

# --------------------------------------------------------------------------
# Analisi del wikitext (nessuna dipendenza da Pywikibot: testabile a parte)
# --------------------------------------------------------------------------

# Parti in cui un "== titolo ==" non è un titolo di sezione
_MASK_RE = re.compile(
    r'<!--.*?(?:-->|\Z)'
    r'|<(nowiki|pre|syntaxhighlight|source|math|chem|score|graph|templatedata)'
    r'(?:\s[^>]*)?>.*?(?:</\1\s*>|\Z)',
    re.DOTALL | re.IGNORECASE)

_HEADING_RE = re.compile(r'^(={1,6})(.+?)(={1,6})[ \t]*$', re.MULTILINE)

_FOOTER_LINE_RE = re.compile(
    r'^\s*(?:'
    r'\[\[\s*(?:Categoria|Category)\s*:[^\]]*\]\]'      # categorie
    r'|\[\[\s*[a-z]{2,3}(?:-[a-z]+)*\s*:[^\]]*\]\]'     # interlingua
    r'|\{\{\s*(?:DEFAULTSORT|ORDINAMENTO)\s*:[^}]*\}\}'
    r'|__[A-Z]+__'
    r')\s*$', re.IGNORECASE)


def mask(text: str) -> str:
    """Copia del testo, lunga uguale, con commenti, nowiki ecc. oscurati.

    Gli a capo restano, così righe e posizioni coincidono con l'originale.
    """
    def blank(m: re.Match) -> str:
        return re.sub(r'[^\n]', ' ', m[0])
    return _MASK_RE.sub(blank, text)


def normalize(title: str) -> str:
    """Forma normalizzata di un titolo di sezione, per i confronti."""
    return re.sub(r'\s+', ' ', title.replace('_', ' ')).strip()


@dataclass
class Heading:
    start: int       # inizio della riga del titolo
    level: int
    title: str       # normalizzato


def find_headings(text: str) -> list[Heading]:
    """Titoli di sezione veri (non dentro commenti, nowiki, pre...)."""
    masked = mask(text)
    result = []
    for m in _HEADING_RE.finditer(masked):
        left, inner, right = m[1], m[2], m[3]
        level = min(len(left), len(right))
        # "===Titolo==" -> livello 2, titolo "=Titolo"
        inner = '=' * (len(left) - level) + inner + '=' * (len(right) - level)
        if not inner.strip():
            continue
        result.append(Heading(m.start(), level, normalize(inner)))
    return result


def footer_start(text: str, start: int) -> int:
    """Posizione da cui, dopo *start*, iniziano solo categorie/interlingua.

    Serve quando la sezione sostituita è l'ultima della pagina: categorie e
    collegamenti interlingua non le appartengono e vanno conservati.
    Righe vuote e commenti (vuoti nel testo oscurato) fanno parte del piè di
    pagina solo se sono seguiti da una categoria o da un interlingua.
    """
    masked = mask(text)
    lines = masked[start:].splitlines(keepends=True)
    pos = len(text)
    cut = len(text)          # inizio dell'ultimo blocco "vero" di piè di pagina
    for line in reversed(lines):
        pos -= len(line)
        if pos < start:
            break
        if _FOOTER_LINE_RE.match(line):
            cut = pos
        elif line.strip():
            break
        # riga vuota o commento: continua a risalire senza spostare il taglio
    # include gli a capo che precedono il piè di pagina, così restano dove sono
    while cut > start and text[cut - 1] == '\n':
        cut -= 1
    return max(cut, start)


@dataclass
class Span:
    heading: Heading
    start: int
    end: int
    subs: list[Heading]


def section_spans(text: str, headings: list[Heading],
                  nosub: bool) -> list[Span]:
    """Estensione di ogni sezione nel testo."""
    spans = []
    for i, h in enumerate(headings):
        end = None
        subs = []
        for nxt in headings[i + 1:]:
            if nosub or nxt.level <= h.level:
                end = nxt.start
                break
            subs.append(nxt)
        if end is None:
            end = footer_start(text, h.start)
        spans.append(Span(h, h.start, end, subs))
    return spans


def split_units(text: str, nosub: bool) -> tuple[str, list[Span]]:
    """Divide il blocco del file nelle sezioni da sostituire.

    Restituisce il testo prima del primo titolo e le sezioni. Senza
    *nosub*, una sezione del file comprende le sue sottosezioni.
    """
    headings = find_headings(text)
    if not headings:
        return text, []
    lead = text[:headings[0].start]
    units = []
    i = 0
    while i < len(headings):
        h = headings[i]
        j = i + 1
        if not nosub:
            while j < len(headings) and headings[j].level > h.level:
                j += 1
        end = headings[j].start if j < len(headings) else len(text)
        units.append(Span(h, h.start, end, headings[i + 1:j]))
        i = j
    return lead, units


class SkipPage(Exception):
    """La pagina va saltata per intero."""


def replace_sections(old: str, block: str, *, nosub: bool = False,
                     dropsub: bool = False, ifmissing: str = 'skippage',
                     nocontent: str = '') -> tuple[str, list[str], list[str]]:
    """Sostituisce in *old* le sezioni presenti in *block*.

    Restituisce (nuovo testo, sezioni sostituite, avvisi). Solleva
    SkipPage se la pagina non va toccata.
    """
    warnings = []
    lead, units = split_units(block, nosub)
    if lead.strip():
        warnings.append('testo prima del primo titolo nel file: ignorato')
    if not units:
        raise SkipPage('nel file non c\'è nessun titolo di sezione')

    page_spans = section_spans(old, find_headings(old), nosub)
    edits = []      # (start, end, nuovo testo, titolo)
    seen = set()
    for unit in units:
        key = (unit.heading.level, unit.heading.title)
        label = '=' * unit.heading.level + unit.heading.title \
            + '=' * unit.heading.level
        if key in seen:
            raise SkipPage(f'la sezione {label} compare due volte nel file')
        seen.add(key)

        matches = [s for s in page_spans
                   if (s.heading.level, s.heading.title) == key]
        if not matches:
            if ifmissing == 'skipsection':
                warnings.append(f'sezione {label} assente nella pagina: '
                                'saltata')
                continue
            raise SkipPage(f'sezione {label} assente nella pagina')
        if len(matches) > 1:
            raise SkipPage(f'nella pagina ci sono {len(matches)} sezioni '
                           f'{label}: non so quale sostituire')
        target = matches[0]
        old_section = old[target.start:target.end]

        if nocontent and (nocontent in old_section
                          or nocontent.lower() in old_section):
            warnings.append(f'sezione {label} contiene già {nocontent!r}: '
                            'saltata')
            continue

        if not nosub and not dropsub:
            new_subs = {(h.level, h.title) for h in unit.subs}
            lost = [h for h in target.subs
                    if (h.level, h.title) not in new_subs]
            if lost:
                names = ', '.join('=' * h.level + h.title + '=' * h.level
                                  for h in lost)
                raise SkipPage(f'la sezione {label} sul wiki contiene '
                               f'sottosezioni assenti dal file ({names}): '
                               'usa -nosubsections o -dropsubsections')

        new_section = block[unit.start:unit.end].rstrip()
        trailing = re.search(r'\s*\Z', old_section)[0]
        # il testo che segue deve restare su una riga a sé
        if (target.end < len(old) and '\n' not in trailing
                and old[target.end] != '\n'):
            trailing = '\n'
        edits.append((target.start, target.end, new_section + trailing,
                      unit.heading.title))

    edits.sort()
    for a, b in zip(edits, edits[1:]):
        if a[1] > b[0]:
            raise SkipPage(f'le sezioni {a[3]} e {b[3]} si sovrappongono')

    new = old
    for start, end, text, _ in reversed(edits):
        new = new[:start] + text + new[end:]
    changed = [title for start, end, text, title in edits
               if old[start:end] != text]
    return new, changed, warnings


# --------------------------------------------------------------------------
# Lettura del file (stesse convenzioni di pagefromfile.py)
# --------------------------------------------------------------------------

def read_blocks(text: str, begin: str, end: str, titlestart: str,
                titleend: str):
    """Restituisce le coppie (titolo, contenuto) del file."""
    page_re = re.compile(re.escape(begin) + '(.*?)' + re.escape(end),
                         re.DOTALL)
    title_re = re.compile(re.escape(titlestart) + '(.*?)'
                          + re.escape(titleend))
    for m in page_re.finditer(text):
        contents = m[1]
        t = title_re.search(contents)
        if not t:
            pywikibot.warning(f'Nessun titolo al carattere {m.start()}: '
                              'blocco saltato.')
            continue
        # il titolo non fa mai parte delle sezioni
        contents = contents[:t.start()] + contents[t.end():]
        yield t[1].strip(), contents.strip('\n')


# --------------------------------------------------------------------------
# Bot
# --------------------------------------------------------------------------

class SectionFromFileBot(SingleSiteBot, CurrentPageBot):

    """Sostituisce le sezioni delle pagine con quelle lette dal file."""

    update_options = {
        'summary': '',
        'minor': False,
        'showdiff': False,
        'nosubsections': False,
        'dropsubsections': False,
        'ifmissing': 'skippage',
        'nocontent': '',
    }

    def skip_page(self, page) -> bool:
        if not page.exists():
            pywikibot.warning(f'{page.title()} non esiste: saltata.')
            return True
        if page.isRedirectPage():
            pywikibot.warning(f'{page.title()} è un redirect: saltata.')
            return True
        return super().skip_page(page)

    def treat_page(self) -> None:
        page = self.current_page
        block = getattr(page, CTX_ATTR)
        try:
            new, changed, warnings = replace_sections(
                page.text, block,
                nosub=self.opt.nosubsections,
                dropsub=self.opt.dropsubsections,
                ifmissing=self.opt.ifmissing,
                nocontent=self.opt.nocontent)
        except SkipPage as e:
            pywikibot.warning(f'{page.title()}: {e}. Pagina saltata.')
            self.counter['skip'] += 1
            return
        for w in warnings:
            pywikibot.warning(f'{page.title()}: {w}.')
        if not changed:
            pywikibot.info(f'{page.title()}: nessuna modifica.')
            return

        sezioni = ', '.join(changed)
        summary = (self.opt.summary.replace('{sezioni}', sezioni)
                   if self.opt.summary
                   else f'Aggiornata sezione {sezioni}')
        self.put_current(new, summary=summary, minor=self.opt.minor,
                         show_diff=self.opt.showdiff or not self.opt.always)


def main(*args: str) -> None:
    filename = 'dict.txt'
    r_opts = {'begin': '{{-start-}}', 'end': '{{-stop-}}',
              'titlestart': "'''", 'titleend': "'''"}
    options = {}

    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        opt = opt.lstrip('-')
        if opt in r_opts:
            r_opts[opt] = value
        elif opt == 'file':
            filename = value
        elif opt in ('notitle', 'noredirect'):
            pass                                   # sempre attivi
        elif opt in ('minor', 'showdiff', 'always', 'nosubsections',
                     'dropsubsections'):
            options[opt] = True
        elif opt in ('summary', 'nocontent'):
            options[opt] = value
        elif opt == 'ifmissing':
            if value not in ('skippage', 'skipsection'):
                pywikibot.error('-ifmissing vale skippage o skipsection.')
                return
            options[opt] = value
        else:
            pywikibot.warning(f'Argomento sconosciuto ignorato: {arg}')

    if options.get('nosubsections') and options.get('dropsubsections'):
        pywikibot.error('-nosubsections e -dropsubsections non vanno '
                        'usati insieme.')
        return
    if not os.path.isfile(filename):
        pywikibot.bot.suggest_help(missing_parameters=['-file'])
        return

    site = pywikibot.Site()
    text = Path(filename).read_text(encoding='utf-8')

    def gen():
        for title, contents in read_blocks(text, **r_opts):
            page = pywikibot.Page(site, title)
            setattr(page, CTX_ATTR, contents)
            yield page

    bot = SectionFromFileBot(generator=PreloadingGenerator(gen()),
                             site=site, **options)
    bot.run()


if __name__ == '__main__':
    main()
