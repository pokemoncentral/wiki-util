Script della vecchia pipeline "Bulbapedia → traduzione", sostituiti da
`gccp-build.py` (novembre 2026), che costruisce le pagine direttamente dai
dati di gioco (`ptcgp-carddump`).

- `gccp-download.py` — scaricava le pagine inglesi `<Pokémon> (TCG Pocket)` da Bulbapedia.
- `gccp-translate-page.py` — traduceva una pagina inglese in `<Pokémon> (GCC Pocket)`.
- `gccp-translate-dir.py` — eseguiva la traduzione su una cartella intera.
- `gccp-translate-page-test.py` — prova delle sostituzioni.
- `gccp-replacements.csv` — sostituzioni regex usate dalla traduzione.
- `tcgp_scraper.py` — raccoglieva da Bulbapedia i dati giapponesi delle carte.

Sono tenuti solo come riferimento: non servono più per generare le pagine.
