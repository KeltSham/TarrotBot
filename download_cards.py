#!/usr/bin/env python3
"""
Скачивает все 78 карт колоды Rider-Waite-Smith в папку images/.
Источник: sacred-texts.com (общественное достояние).

Запуск:
    python3 download_cards.py

Запускайте из корня проекта (там, где лежит index.html).
"""

import urllib.request
import urllib.error
import os
import time

BASE_URL = "https://www.sacred-texts.com/tarot/pkt/img/"
OUT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

os.makedirs(OUT_DIR, exist_ok=True)

# Генерируем список всех 78 файлов
files = []
# Старшие арканы (22)
for i in range(22):
    files.append(f"ar{i:02d}.jpg")
# Жезлы, Кубки, Мечи, Пентакли (по 14)
for prefix in ("wa", "cu", "sw", "pe"):
    for i in range(1, 15):
        files.append(f"{prefix}{i:02d}.jpg")

print(f"Скачиваю {len(files)} карт в {OUT_DIR}")
print("-" * 50)

ok    = 0
fail  = []
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; TarotBot/1.0)"
}

for fname in files:
    out_path = os.path.join(OUT_DIR, fname)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f"  уже есть  {fname}")
        ok += 1
        continue

    url = BASE_URL + fname
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) < 500:
            raise ValueError(f"Слишком маленький файл ({len(data)} байт)")
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"  ✓  {fname}  ({len(data)//1024} кБ)")
        ok += 1
        time.sleep(0.3)   # вежливая пауза
    except Exception as e:
        print(f"  ✗  {fname}  — {e}")
        fail.append(fname)

print("-" * 50)
print(f"Готово: {ok}/{len(files)}")
if fail:
    print(f"Не скачано ({len(fail)}): {', '.join(fail)}")
    print("\nЕсли sacred-texts.com недоступен, попробуйте альтернативный источник:")
    print("  BASE_URL = 'https://upload.wikimedia.org/wikipedia/commons/'")
    print("  (потребуется адаптация имён файлов)")
else:
    print("Все карты скачаны! Можно делать git add images/ && git push")
