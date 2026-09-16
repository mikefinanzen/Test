# SWEX-Auszug fuer die Team-Analyse

Erzeugt aus dem JSON-Export des **Summoners War Exporter (SWEX)** einen kompakten
Textauszug deiner Box: einsatzfaehige Monster mit ihren tatsaechlichen Kampfwerten
(Basiswerte + Runen), Reservemonster und den Runenbestand.

## Benutzung

### Der einfache Weg (Windows)

1. SWEX starten, Summoners War ueber Steam starten und einmal einloggen.
   SWEX legt dann eine Datei wie `<Wizard-Name>-<Datum>.json` an.
2. **`Auszug_erstellen.bat` doppelklicken.**
   Das Skript sucht den Export selbst in Dokumente / Downloads / Desktop /
   Benutzerordner, schreibt `auszug.txt` daneben und legt den Text direkt
   in die Zwischenablage.
3. Im Chat mit `Strg+V` einfuegen.

Voraussetzung ist eine Python-Installation (https://www.python.org/downloads/,
beim Setup "Add python.exe to PATH" ankreuzen). Die .bat sagt es dir, falls
Python fehlt.

### Manuell

```
python sw_export_summary.py "C:\Pfad\zu\deinem-export.json" -o auszug.txt
python sw_export_summary.py --auto --clip          # sucht selbst + Zwischenablage
```

## Optionen

| Option | Wirkung |
|---|---|
| `--auto` | sucht den SWEX-Export selbst in den ueblichen Ordnern |
| `--clip` | legt den Auszug zusaetzlich in die Zwischenablage |
| `-o DATEI` | schreibt in eine Datei statt auf die Konsole |
| `--max-monsters N` | wie viele gerunte Monster gelistet werden (Standard 40) |
| `--top-runes N` | wie viele Top-Runen je Kategorie (Standard 15) |
| `--offline` | laedt keine Monsternamen aus dem Netz (Ausgabe dann mit Familien-IDs) |
| `--names DATEI` | eigene Namensliste als JSON (`{"14313": "Bernard", ...}`) |
| `--names-url URL` | alternative Quelle fuer die Namensliste |

Die Monsternamen werden beim ersten Lauf einmalig von swarfarm.com geladen und in
`~/.sw_monster_names.json` gecacht. Klappt das nicht, laeuft das Skript trotzdem
durch und gibt Familien-IDs aus.

## Datenschutz

Ausgegeben werden nur Monster, Stats und Runen. Wizard-ID, Name, Freundesliste,
Chat- und Kaufdaten aus dem Export landen **nicht** im Auszug.
