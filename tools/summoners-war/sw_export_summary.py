#!/usr/bin/env python3
"""Erzeugt aus einem SWEX-JSON (Summoners War Exporter) einen kompakten,
einfuegbaren Auszug: Monsterbox + Runenbestand.

Aufruf:
    python sw_export_summary.py <pfad-zur-swex.json> [-o auszug.txt]

Es werden bewusst KEINE persoenlichen Daten (Wizard-ID, Name, Freundesliste,
Kaeufe) ausgegeben - nur Monster, Stats und Runen.
"""

import argparse
import json
import os
import sys
import urllib.request

ELEMENTS = {1: "Wasser", 2: "Feuer", 3: "Wind", 4: "Licht", 5: "Dunkel"}

RUNE_SETS = {
    1: "Energy", 2: "Guard", 3: "Swift", 4: "Blade", 5: "Rage", 6: "Focus",
    7: "Endure", 8: "Fatal", 10: "Despair", 11: "Vampire", 13: "Violent",
    14: "Nemesis", 15: "Will", 16: "Shield", 17: "Revenge", 18: "Destroy",
    19: "Fight", 20: "Determination", 21: "Enhance", 22: "Accuracy",
    23: "Tolerance", 24: "Seal", 25: "Intangible",
}

# Effekt-IDs der Runen-Stats
EFFECTS = {
    1: "HP+", 2: "HP%", 3: "ATK+", 4: "ATK%", 5: "DEF+", 6: "DEF%",
    8: "SPD", 9: "CR%", 10: "CD%", 11: "RES%", 12: "ACC%",
}

QUALITY = {1: "Normal", 2: "Magic", 3: "Rare", 4: "Hero", 5: "Legend",
           11: "Normal+", 12: "Magic+", 13: "Rare+", 14: "Hero+", 15: "Legend+"}

NAME_CACHE = os.path.join(os.path.expanduser("~"), ".sw_monster_names.json")
SWARFARM = "https://swarfarm.com/api/v2/bestiary/?page_size=200"


# ---------------------------------------------------------------- Namen

def load_name_map(names_file=None, offline=False, url=None):
    """com2us_id -> Monstername. Cache -> Datei -> SWARFARM -> leer."""
    if names_file:
        with open(names_file, encoding="utf-8") as fh:
            return {int(k): v for k, v in json.load(fh).items()}

    if os.path.exists(NAME_CACHE):
        try:
            with open(NAME_CACHE, encoding="utf-8") as fh:
                return {int(k): v for k, v in json.load(fh).items()}
        except Exception:
            pass

    if offline:
        return {}

    names = {}
    url = url or SWARFARM
    try:
        while url:
            with urllib.request.urlopen(url, timeout=30) as resp:
                page = json.loads(resp.read().decode("utf-8"))
            if isinstance(page, list):           # nicht paginierte Antwort
                entries, url = page, None
            else:
                entries = page.get("results") or []
                url = page.get("next")
            for mon in entries:
                if not isinstance(mon, dict):
                    continue
                cid = mon.get("com2us_id") or mon.get("com2usId") or mon.get("id")
                name = mon.get("name") or mon.get("Name")
                if cid and name:
                    names[int(cid)] = name
        if names:
            with open(NAME_CACHE, "w", encoding="utf-8") as fh:
                json.dump(names, fh)
            print("Namensliste geladen (%d Monster), gecacht in %s."
                  % (len(names), NAME_CACHE), file=sys.stderr)
    except Exception as exc:
        print("Hinweis: Namen konnten nicht geladen werden (%s). "
              "Der Auszug nutzt dann Familien-IDs - das ist ok, damit kann "
              "weitergearbeitet werden." % exc, file=sys.stderr)
    return names


def monster_name(master_id, names):
    if master_id in names:
        return names[master_id]
    family, awakened, attr = master_id // 100, (master_id // 10) % 10, master_id % 10
    tag = "a" if awakened else ""
    return "Fam%d%s-%s" % (family, tag, ELEMENTS.get(attr, "?"))


# ---------------------------------------------------------------- Runen

def rune_stats(rune):
    """Liefert (flat, pct) Dicts der Gesamtwirkung einer Rune."""
    flat, pct = {}, {}

    def add(eff):
        if not eff:
            return
        eid = eff[0]
        val = eff[1] if len(eff) > 1 else 0
        if len(eff) > 3 and eff[2]:          # aufgeschliffener Zusatzwert
            val += eff[3]
        name = EFFECTS.get(eid)
        if not name:
            return
        target = pct if name.endswith("%") else flat
        target[name] = target.get(name, 0) + val

    add(rune.get("pri_eff"))
    add(rune.get("prefix_eff"))
    for sub in rune.get("sec_eff") or []:
        add(sub)
    return flat, pct


def rune_line(rune):
    flat, pct = rune_stats(rune)
    main = rune.get("pri_eff") or [0, 0]
    main_name = EFFECTS.get(main[0], "?")
    parts = ["%s%s" % (k, v) for k, v in sorted(pct.items())]
    parts += ["%s%s" % (k, v) for k, v in sorted(flat.items())]
    return "%d* %s %s Slot%d Haupt:%s+%s [%s]" % (
        rune.get("class", 0) % 10 or rune.get("class", 0),
        QUALITY.get(rune.get("extra", 0), "?"),
        RUNE_SETS.get(rune.get("set_id"), "Set%s" % rune.get("set_id")),
        rune.get("slot_no", 0), main_name, main[1], ", ".join(parts))


def rune_speed(rune):
    flat, _ = rune_stats(rune)
    return flat.get("SPD", 0)


def rune_acc(rune):
    _, pct = rune_stats(rune)
    return pct.get("ACC%", 0)


# ---------------------------------------------------------------- Monster

def unit_runes(unit):
    runes = unit.get("runes") or []
    if isinstance(runes, dict):
        runes = list(runes.values())
    return [r for r in runes if isinstance(r, dict)]


def effective_stats(unit):
    """Basiswerte + Runen -> tatsaechliche Kampfwerte."""
    base = {
        "HP": (unit.get("con", 0) or 0) * 15,
        "ATK": unit.get("atk", 0) or 0,
        "DEF": unit.get("def", 0) or 0,
        "SPD": unit.get("spd", 0) or 0,
        "CR": unit.get("critical_rate", 0) or 0,
        "CD": unit.get("critical_damage", 0) or 0,
        "RES": unit.get("resist", 0) or 0,
        "ACC": unit.get("accuracy", 0) or 0,
    }
    flat, pct = {}, {}
    for rune in unit_runes(unit):
        f, p = rune_stats(rune)
        for k, v in f.items():
            flat[k] = flat.get(k, 0) + v
        for k, v in p.items():
            pct[k] = pct.get(k, 0) + v

    out = dict(base)
    for key, fkey, pkey in (("HP", "HP+", "HP%"), ("ATK", "ATK+", "ATK%"),
                            ("DEF", "DEF+", "DEF%")):
        out[key] = int(base[key] * (1 + pct.get(pkey, 0) / 100.0) + flat.get(fkey, 0))
    out["SPD"] = base["SPD"] + flat.get("SPD", 0)
    out["CR"] = base["CR"] + pct.get("CR%", 0)
    out["CD"] = base["CD"] + pct.get("CD%", 0)
    out["RES"] = base["RES"] + pct.get("RES%", 0)
    out["ACC"] = base["ACC"] + pct.get("ACC%", 0)
    return out


def equipped_sets(unit):
    """Aktive Runensets als lesbarer String, z.B. 'Violent/Will'."""
    counts = {}
    for rune in unit_runes(unit):
        name = RUNE_SETS.get(rune.get("set_id"), "?")
        counts[name] = counts.get(name, 0) + 1
    four = {"Violent", "Swift", "Rage", "Fatal", "Despair", "Vampire",
            "Destroy", "Rage", "Seal", "Intangible"}
    active = []
    for name, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
        need = 4 if name in four else 2
        for _ in range(cnt // need):
            active.append(name)
    return "/".join(active) if active else "-"


def natural_stars(unit):
    """SWEX liefert das nicht direkt; aus Basis-HP grob nicht ableitbar ->
    'class' ist die aktuelle Sternzahl."""
    return unit.get("class", 0)


# ---------------------------------------------------------------- Report

def build_report(data, names, top_runes=15):
    out = []
    w = out.append

    units = data.get("unit_list") or []
    w("=== SUMMONERS WAR - BOX-AUSZUG ===")
    w("Wizard-Level: %s" % data.get("wizard_info", {}).get("wizard_level",
                                                           data.get("wizard_level", "?")))
    w("Monster gesamt: %d" % len(units))
    w("")

    rows = []
    for unit in units:
        mid = unit.get("unit_master_id", 0)
        stats = effective_stats(unit)
        rows.append({
            "name": monster_name(mid, names),
            "element": ELEMENTS.get(mid % 10, "?"),
            "awakened": bool((mid // 10) % 10),
            "stars": natural_stars(unit),
            "level": unit.get("unit_level", 0),
            "sets": equipped_sets(unit),
            "runes": len(unit_runes(unit)),
            "s": stats,
        })

    # Gerunte Monster zuerst - das sind die einsatzfaehigen Einheiten.
    ranked = sorted(rows, key=lambda r: (-r["runes"], -r["stars"], -r["s"]["SPD"]))
    geared = [r for r in ranked if r["runes"] >= 4]

    w("--- EINSATZFAEHIGE MONSTER (>=4 Runen), sortiert nach Speed ---")
    w("%-22s %-7s %-3s %-4s %5s %6s %5s %4s %4s %4s %4s  %s" % (
        "Monster", "Element", "*", "Lvl", "SPD", "HP", "ATK", "DEF", "CR", "CD", "ACC", "Sets"))
    for r in sorted(geared, key=lambda r: -r["s"]["SPD"]):
        s = r["s"]
        w("%-22s %-7s %-3d %-4d %5d %6d %5d %4d %4d %4d %4d  %s" % (
            r["name"] + ("*" if r["awakened"] else ""), r["element"], r["stars"],
            r["level"], s["SPD"], s["HP"], s["ATK"], s["DEF"], s["CR"], s["CD"],
            s["ACC"], r["sets"]))
    w("")

    w("--- UNGERUNTE / RESERVE-MONSTER (5*+) ---")
    reserve = [r for r in ranked if r["runes"] < 4 and r["stars"] >= 5]
    w(", ".join("%s (%s %d*)" % (r["name"], r["element"], r["stars"])
                for r in reserve) or "(keine)")
    w("")

    w("--- RESTLICHE BOX (kompakt) ---")
    rest = {}
    for r in ranked:
        if r["runes"] < 4 and r["stars"] < 5:
            key = "%s (%s)" % (r["name"], r["element"])
            rest[key] = rest.get(key, 0) + 1
    w(", ".join("%s x%d" % (k, v) if v > 1 else k
                for k, v in sorted(rest.items())) or "(keine)")
    w("")

    # ---- Runenbestand
    spare = data.get("runes") or []
    all_runes = list(spare)
    for unit in units:
        all_runes.extend(unit_runes(unit))

    w("=== RUNEN ===")
    w("Gesamt: %d (davon nicht angelegt: %d)" % (len(all_runes), len(spare)))

    by_set = {}
    for rune in all_runes:
        name = RUNE_SETS.get(rune.get("set_id"), "Set%s" % rune.get("set_id"))
        by_set[name] = by_set.get(name, 0) + 1
    w("Nach Set: " + ", ".join("%s %d" % (k, v)
                               for k, v in sorted(by_set.items(), key=lambda kv: -kv[1])))

    six = [r for r in all_runes if (r.get("class", 0) % 10) == 6 or r.get("class") == 6]
    legend = [r for r in six if r.get("extra", 0) in (5, 15)]
    hero = [r for r in six if r.get("extra", 0) in (4, 14)]
    w("6* Runen: %d (Legend %d, Hero %d)" % (len(six), len(legend), len(hero)))
    w("")

    w("--- BESTE FREIE RUNEN NACH SPEED ---")
    for rune in sorted(spare, key=rune_speed, reverse=True)[:top_runes]:
        if rune_speed(rune) <= 0:
            break
        w("  " + rune_line(rune))
    w("")

    w("--- BESTE FREIE RUNEN NACH GENAUIGKEIT ---")
    for rune in sorted(spare, key=rune_acc, reverse=True)[:top_runes]:
        if rune_acc(rune) <= 0:
            break
        w("  " + rune_line(rune))

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_file", help="SWEX-Export (*.json)")
    ap.add_argument("-o", "--out", help="Ausgabedatei (Standard: Konsole)")
    ap.add_argument("--names", help="Eigene Namensliste (JSON: id -> Name)")
    ap.add_argument("--names-url", help="Alternative Quelle fuer die Namensliste")
    ap.add_argument("--offline", action="store_true",
                    help="Keine Namen aus dem Netz laden")
    ap.add_argument("--top-runes", type=int, default=15,
                    help="Wie viele Top-Runen je Kategorie (Standard 15)")
    args = ap.parse_args()

    with open(args.json_file, encoding="utf-8") as fh:
        data = json.load(fh)

    names = load_name_map(args.names, args.offline, args.names_url)
    report = build_report(data, names, args.top_runes)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
        print("Auszug geschrieben: %s" % args.out)
    else:
        print(report)


if __name__ == "__main__":
    main()
