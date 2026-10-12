#!/usr/bin/env python3
"""Универсальный J2-клоузер ПМ (Спринт 2+): перед КАЖДЫМ finish закрывает
все не-активные сессии реестра (finished/returned/abandoned/stale) —
finished-сессия продолжает держать зону и ломает pm_bounds_check.
Активная (running) не трогается. Запуск: python3 j2close.py [active_delegation_id]
Если active не задан — активной считается последняя created сессия."""
import sys, json
sys.path.insert(0, "scripts")
import session_check as sc

REG = sys.argv[2] if len(sys.argv) > 2 else "/home/hermes-bot/.hermes/cache/scratch/flowctl-sprint2/registry.json"
active = sys.argv[1] if len(sys.argv) > 1 else None
data, err = sc.registry_load(sc.Path(REG))
assert not err, err
sessions = data.get("sessions", [])
if active is None and sessions:
    active = sessions[-1]["delegation_id"]
n = 0
for i, s in enumerate(sessions):
    if s["delegation_id"] == active:
        continue
    if s["status"] in ("finished", "returned", "abandoned", "stale"):
        s["owner_pm"] = f"main/auto-{i}"
        sc.transition(s, "closed", "pm_decision", "PM: J2 auto-cleanup before finish.")
        n += 1
sc.registry_write(sc.Path(REG), data)
print(f"closed {n}; active={active}")
