# SWEX-Auszug fuer die Team-Analyse

Erzeugt aus dem JSON-Export des **Summoners War Exporter (SWEX)** einen kompakten
Textauszug deiner Box: einsatzfaehige Monster mit ihren tatsaechlichen Kampfwerten
(Basiswerte + Runen), Reservemonster und den Runenbestand.

## Benutzung

1. SWEX starten, Summoners War ueber Steam starten und einmal einloggen.
   SWEX legt dann eine Datei wie `<Wizard-Name>-<Datum>.json` an
   (Pfad steht im SWEX-Fenster unter "Files will be saved to ...").
2. Im Terminal:

   ```
   python sw_export_summary.py "C:\Pfad\zu\deinem-export.json" -o auszug.txt
   ```

3. Den Inhalt von `auszug.txt` in den Chat einfuegen.

## Optionen

| Option | Wirkung |
|---|---|
| `-o DATEI` | schreibt in eine Datei statt auf die Konsole |
| `--offline` | laedt keine Monsternamen aus dem Netz (Ausgabe dann mit Familien-IDs) |
| `--names DATEI` | eigene Namensliste als JSON (`{"14313": "Bernard", ...}`) |
| `--names-url URL` | alternative Quelle fuer die Namensliste |
| `--top-runes N` | wie viele Top-Runen je Kategorie gelistet werden (Standard 15) |

Die Monsternamen werden beim ersten Lauf einmalig von swarfarm.com geladen und in
`~/.sw_monster_names.json` gecacht. Klappt das nicht, laeuft das Skript trotzdem
durch und gibt Familien-IDs aus.

## Datenschutz

Ausgegeben werden nur Monster, Stats und Runen. Wizard-ID, Name, Freundesliste,
Chat- und Kaufdaten aus dem Export landen **nicht** im Auszug.
