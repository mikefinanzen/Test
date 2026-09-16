#!/usr/bin/env python3
"""Findet die beste einzelne Runen-Umbelegung fuer ein Monster.

Probiert jede freie Rune gegen die aktuell angelegte Rune desselben Slots,
prueft Mindestwerte und aktive Sets und zeigt die besten Tauschgeschaefte.

    python rune_swap.py <swex.json> --names names.json --unit Veromos \\
        --maximize ACC --min-spd 175 --keep-set Violent
"""

import argparse
import copy
import json
import sys

import sw_export_summary as base

STATS = ("SPD", "HP", "ATK", "DEF", "CR", "CD", "ACC", "RES")


def stats_for(unit, runes):
    probe = copy.copy(unit)
    probe["runes"] = runes
    return base.effective_stats(probe)


def describe(rune):
    return base.rune_line(rune)


def find_units(export, names, wanted):
    hits = []
    for unit in export.get("unit_list") or []:
        mid = unit.get("unit_master_id", 0)
        name = base.monster_name(mid, names)
        if wanted.lower() in name.lower():
            hits.append((name, unit))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("swex")
    ap.add_argument("--names", required=True)
    ap.add_argument("--unit", required=True)
    ap.add_argument("--pick", type=int, default=0,
                    help="Bei mehreren Treffern: welcher (0-basiert)")
    ap.add_argument("--maximize", default="HP", choices=STATS)
    ap.add_argument("--keep-set", action="append", default=[],
                    help="Dieses Set muss aktiv bleiben (mehrfach nutzbar)")
    for stat in STATS:
        ap.add_argument("--min-%s" % stat.lower(), type=int, default=None)
    ap.add_argument("--slot", type=int, default=None,
                    help="Nur diesen Slot betrachten (1-6)")
    ap.add_argument("--assume-empty", action="store_true",
                    help="Den Slot als leer behandeln (Rune schon abgenommen)")
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args()

    names = {int(k): v for k, v in json.load(open(args.names, encoding="utf-8")).items()}
    export = json.load(open(args.swex, encoding="utf-8"))
    spare = export.get("runes") or []

    hits = find_units(export, names, args.unit)
    if not hits:
        print("Kein Monster gefunden fuer '%s'." % args.unit); return 2
    if len(hits) > 1:
        print("Mehrere Treffer:")
        for i, (name, u) in enumerate(hits):
            st = base.effective_stats(u)
            print("  [%d] %s  %d*  Lvl %s  SPD %d HP %d ACC %d  %s" % (
                i, name, u.get("class", 0), u.get("unit_level"), st["SPD"],
                st["HP"], st["ACC"], base.equipped_sets(u)))
        print()
    name, unit = hits[min(args.pick, len(hits) - 1)]

    current_runes = base.unit_runes(unit)
    if args.slot and args.assume_empty:
        current_runes = [r for r in current_runes if r.get("slot_no") != args.slot]
    cur = stats_for(unit, current_runes)
    print("=== %s (aktuell) ===" % name)
    print("  " + "  ".join("%s %s" % (s, cur[s]) for s in STATS))
    print("  Sets: %s" % base.equipped_sets(unit))
    print("  Angelegt:")
    by_slot = {}
    for rune in current_runes:
        by_slot[rune.get("slot_no")] = rune
    if args.slot and args.assume_empty:
        by_slot[args.slot] = None
    for slot in sorted(by_slot):
        print("    %s" % (describe(by_slot[slot]) if by_slot[slot]
                          else "Slot %d: leer" % slot))
    print()

    mins = {s: getattr(args, "min_%s" % s.lower()) for s in STATS}
    mins = {s: v for s, v in mins.items() if v is not None}

    results = []
    for slot, old in by_slot.items():
        if args.slot and slot != args.slot:
            continue
        for cand in spare:
            if cand.get("slot_no") != slot:
                continue
            new_runes = [r for r in current_runes if r is not old] + [cand]
            st = stats_for(unit, new_runes)
            if any(st[s] < v for s, v in mins.items()):
                continue
            sets = base.active_sets(new_runes)
            if any(k not in sets for k in args.keep_set):
                continue
            gain = st[args.maximize] - cur[args.maximize]
            if gain <= 0:
                continue
            results.append((gain, slot, old, cand, st, sets))

    if not results:
        print("Kein Tausch gefunden, der %s erhoeht und alle Vorgaben haelt."
              % args.maximize)
        return 0

    results.sort(key=lambda r: -r[0])
    print("=== Beste Tausche (Ziel: %s hoch) ===" % args.maximize)
    for gain, slot, old, cand, st, sets in results[:args.top]:
        print("+%d %s  in Slot %d" % (gain, args.maximize, slot))
        print("   RAUS: %s" % (describe(old) if old else "(Slot war leer)"))
        print("   REIN: %s" % describe(cand))
        deltas = ["%s %+d" % (s, st[s] - cur[s]) for s in STATS if st[s] != cur[s]]
        print("   Danach: %s | Sets: %s" % (
            "  ".join("%s %s" % (s, st[s]) for s in STATS), "/".join(sets)))
        print("   Aenderung: %s" % ", ".join(deltas))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
