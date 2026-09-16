#!/usr/bin/env python3
"""Bewertet eine SWEX-Box fuer den Turm der Pruefung (ToA).

Verbindet den SWEX-Export mit der SWARFARM-Bestiary (Namen + Skills) und
markiert je Monster die Faehigkeiten, auf die es im ToA ankommt:
Schaden ueber Zeit, Heilung, Reinigung, Angriffsleiste, Verteidigungsbruch,
Immunitaet, Wiederbelebung und Kontrolle.

    python toa_advisor.py <swex.json> --bestiary bestiary_data.json
"""

import argparse
import json
import sys

# Effektnamen der Bestiary -> ToA-Rolle
ROLE_EFFECTS = {
    "DoT": ["Continuous DMG"],
    "DoT-Zuend": ["Detonate Continuous Damage"],
    "Heal": ["Heal", "Recovery"],
    "Cleanse": ["Cleanse"],
    "ATB+": ["Increase ATB"],
    "ATB-": ["Decrease ATB"],
    "DefBreak": ["Decrease DEF"],
    "AtkBreak": ["Decrease ATK"],
    "Immun": ["Immunity"],
    "Revive": ["Revive"],
    "SeeleSchutz": ["Protect Soul", "Endure"],
    "Shield": ["Shield"],
    "Invinc": ["Invincible"],
    "Provoke": ["Provoke"],
    "CC": ["Stun", "Freeze", "Sleep", "Silence"],
    "Glancing": ["Glancing Hit"],
    "SpdUp": ["Increase SPD"],
    "SpdDown": ["Decrease SPD"],
    "Brand": ["Brand"],
    "HealBlock": ["Disturb HP Recovery"],
}

ELEMENTS = {1: "Wasser", 2: "Feuer", 3: "Wind", 4: "Licht", 5: "Dunkel"}


def load_bestiary(path):
    data = json.load(open(path, encoding="utf-8"))
    monsters, skills, effects = {}, {}, {}
    details = {}
    for entry in data:
        model, pk, f = entry["model"], entry.get("pk"), entry["fields"]
        if model == "bestiary.monster":
            monsters[f["com2us_id"]] = f
        elif model == "bestiary.skill":
            skills[pk] = f
        elif model == "bestiary.skilleffect":
            effects[pk] = f
        elif model == "bestiary.skilleffectdetail":
            details.setdefault(f["skill"], []).append(f)
    return monsters, skills, effects, details


def unit_roles(mon, skills, effects, details):
    """Welche ToA-relevanten Faehigkeiten hat dieses Monster?"""
    found = {}
    for skill_pk in mon.get("skills") or []:
        skill = skills.get(skill_pk)
        if not skill:
            continue
        for det in details.get(skill_pk, []):
            eff = effects.get(det["effect"])
            if not eff:
                continue
            for role, wanted in ROLE_EFFECTS.items():
                if eff["name"] not in wanted:
                    continue
                # Fremdwirkung zaehlt; reine Selbstbuffs sind im ToA schwaecher
                scope = "AoE" if det.get("aoe") or det.get("all") else "ST"
                if det.get("self_effect"):
                    scope = "self"
                prev = found.get(role)
                rank = {"AoE": 3, "ST": 2, "self": 1}
                if not prev or rank[scope] > rank[prev]:
                    found[role] = scope
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("swex")
    ap.add_argument("--bestiary", required=True)
    ap.add_argument("--min-runes", type=int, default=4)
    ap.add_argument("--min-stars", type=int, default=0)
    args = ap.parse_args()

    monsters, skills, effects, details = load_bestiary(args.bestiary)
    export = json.load(open(args.swex, encoding="utf-8"))

    rows = []
    for unit in export.get("unit_list") or []:
        mid = unit.get("unit_master_id")
        mon = monsters.get(mid)
        runes = unit.get("runes") or []
        if isinstance(runes, dict):
            runes = list(runes.values())
        if len(runes) < args.min_runes:
            continue
        if not mon:
            rows.append((mid, "UNBEKANNT-%s" % mid, "?", 0, unit.get("unit_level"), {}))
            continue
        if mon["natural_stars"] < args.min_stars:
            continue
        rows.append((mid, mon["name"], ELEMENTS.get(mid % 10, "?"),
                     mon["natural_stars"], unit.get("unit_level"),
                     unit_roles(mon, skills, effects, details)))

    order = ["DoT", "DoT-Zuend", "Heal", "Cleanse", "Immun", "ATB+", "ATB-",
             "DefBreak", "AtkBreak", "Revive", "SeeleSchutz", "Shield",
             "Invinc", "Provoke", "CC", "Glancing", "SpdDown", "SpdUp",
             "Brand", "HealBlock"]
    print("%-22s %-7s %-4s %-4s %s" % ("Monster", "Element", "nat*", "Lvl",
                                       "ToA-relevante Faehigkeiten"))
    for _, name, elem, stars, lvl, roles in sorted(
            rows, key=lambda r: (-len(r[5]), -r[3])):
        tags = ["%s(%s)" % (r, roles[r]) for r in order if r in roles]
        print("%-22s %-7s %-4s %-4s %s" % (name, elem, stars, lvl,
                                           " ".join(tags) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
