"""Проверка каталога. Запуск: python3 validate_catalog.py
Ничего устанавливать не нужно, только Python 3."""
import json, sys, os
from datetime import date

here = os.path.dirname(os.path.abspath(__file__))
def load(n): return json.load(open(os.path.join(here, n + ".json"), encoding="utf-8"))

hotels_file = sys.argv[1].replace(".json", "") if len(sys.argv) > 1 else "hotels"
dest, hotels, transport, transfers = (load(n) for n in ("destinations", hotels_file, "transport", "transfers"))
errors = []
dest_ids = {d["id"] for d in dest}

# 1. уникальность id
for name, items in (("destinations", dest), ("hotels", hotels), ("transport", transport), ("transfers", transfers)):
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        errors.append(f"{name}: есть повторяющиеся id")

# 2. ссылки на направления существуют
for name, items in (("hotels", hotels), ("transport", transport), ("transfers", transfers)):
    for i in items:
        if i["destination_id"] not in dest_ids:
            errors.append(f"{name}/{i['id']}: неизвестное направление {i['destination_id']}")

# 3. цены и даты
for name, items, price_key in (("hotels", hotels, "price_per_night"), ("transport", transport, "price_per_adult"), ("transfers", transfers, "price")):
    for i in items:
        if i[price_key] <= 0:
            errors.append(f"{name}/{i['id']}: цена должна быть > 0")
        if date.fromisoformat(i["available_from"]) > date.fromisoformat(i["available_to"]):
            errors.append(f"{name}/{i['id']}: available_from позже available_to")

# 4. блокированные даты внутри периода доступности
for h in hotels:
    for b in h["blackout_dates"]:
        if not (h["available_from"] <= b["from"] <= b["to"] <= h["available_to"]):
            errors.append(f"hotels/{h['id']}: blackout вне периода доступности")

# 5. у каждого направления есть всё нужное
for d in dest:
    if not [h for h in hotels if h["destination_id"] == d["id"]]: errors.append(f"{d['id']}: нет отелей")
    if not [t for t in transport if t["destination_id"] == d["id"] and t["direction"] == "outbound"]: errors.append(f"{d['id']}: нет рейса/поезда туда")
    if not [t for t in transport if t["destination_id"] == d["id"] and t["direction"] == "return"]: errors.append(f"{d['id']}: нет рейса/поезда обратно")
    if not [t for t in transfers if t["destination_id"] == d["id"]]: errors.append(f"{d['id']}: нет трансферов")

# 6. разнообразие (чтобы агенту было из чего выбирать компромиссы)
for d in dest:
    hs = [h for h in hotels if h["destination_id"] == d["id"]]
    if not any(h["pets_allowed"] for h in hs): print(f"  заметка: в {d['name']} нет отелей с животными")

print(f"Направлений: {len(dest)}, отелей: {len(hotels)}, транспорта: {len(transport)}, трансферов: {len(transfers)}")
if errors:
    print("ОШИБКИ:"); [print(" -", e) for e in errors]; sys.exit(1)
print("Каталог в порядке")
