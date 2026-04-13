#!/usr/bin/env python3
"""
convert_to_webp.py — конвертация PNG → WebP (JPEG пропускаются, они уже оптимальны).

Правило выбора формата:
  PNG  → WebP  (даёт -13…-60% для UI-ассетов с прозрачностью/крупными плашками)
  JPEG → остаётся JPEG  (карты таро уже сжаты до 25-40 KB; WebP выходит тяжелее)

Требует: pip install Pillow
Запуск:  python3 convert_to_webp.py

Что делает автоматически:
  1. Конвертирует PNG → WebP (если экономия >= 2%)
  2. Обновляет пути в script.js, sw.js, style.css
  3. НЕ удаляет оригинальные PNG (удали вручную после визуальной проверки)
"""
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Установи Pillow: pip install Pillow")
    sys.exit(1)

ROOT          = Path(__file__).parent
IMG_DIR       = ROOT / 'images'
QUALITY       = 85   # баланс качество/размер для lossy WebP
METHOD        = 6    # медленнее, но лучшее сжатие (0–6)
MIN_SAVING_PCT = 2   # игнорировать конвертацию, если экономия < 2%

# Файлы, в которых нужно обновить пути после конвертации
CODE_FILES = [
    ROOT / 'script.js',
    ROOT / 'sw.js',
    ROOT / 'style.css',
]

if not IMG_DIR.exists():
    print(f"Папка {IMG_DIR} не найдена. Запусти скрипт из корня проекта.")
    sys.exit(1)

converted_files: list[str] = []   # имена файлов (без пути), которые реально сконвертированы
converted = skipped = errors = rejected = 0
saved_total_kb = 0

# ── 1. Конвертация ────────────────────────────────────────────────────────────
print('Конвертация изображений...\n')

for src in sorted(IMG_DIR.iterdir()):
    ext = src.suffix.lower()

    # JPEG не трогаем — при повторном сжатии они становятся только тяжелее
    if ext in ('.jpg', '.jpeg'):
        print(f'  —    {src.name:44s} JPEG — пропускаем (уже оптимален)')
        skipped += 1
        continue

    if ext != '.png':
        continue

    dst = src.with_suffix('.webp')
    if dst.exists():
        print(f'  SKIP {src.name:44s} → уже существует')
        skipped += 1
        continue

    try:
        with Image.open(src) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
                img.save(dst, 'WEBP', quality=QUALITY, method=METHOD, lossless=False)
            else:
                img = img.convert('RGB')
                img.save(dst, 'WEBP', quality=QUALITY, method=METHOD)

        src_kb = src.stat().st_size / 1024
        dst_kb = dst.stat().st_size / 1024
        ratio  = (1 - dst_kb / src_kb) * 100
        saved  = src_kb - dst_kb

        if ratio < MIN_SAVING_PCT:
            dst.unlink()
            print(f'  ✗    {src.name:44s} {src_kb:5.0f} KB → {dst_kb:5.0f} KB  ({ratio:+.0f}%) — не выгодно, оставляем PNG')
            rejected += 1
        else:
            saved_total_kb += saved
            print(f'  ✓    {src.name:44s} {src_kb:5.0f} KB → {dst_kb:5.0f} KB  (-{ratio:.0f}%)')
            converted_files.append(src.name)   # только имя файла, напр. "bg_mystic_xxx.png"
            converted += 1

    except Exception as e:
        print(f'  ERR  {src.name}: {e}')
        errors += 1

print()
print('═' * 66)
print(f'  Конвертация:  {converted} файлов  |  {rejected} не выгодно  |  {skipped} пропущено  |  {errors} ошибок')
if converted:
    print(f'  Сэкономлено:  {saved_total_kb:.0f} KB')

# ── 2. Обновление путей в коде ────────────────────────────────────────────────
if not converted_files:
    print()
    print('  Нечего обновлять в коде — конвертаций не было.')
    sys.exit(0)

print()
print('Обновление путей в коде...\n')

for code_path in CODE_FILES:
    if not code_path.exists():
        print(f'  SKIP {code_path.name} — файл не найден')
        continue

    original = code_path.read_text(encoding='utf-8')
    updated  = original
    changes  = []

    for png_name in converted_files:
        stem     = Path(png_name).stem              # "bg_mystic_1774882343565"
        old_ref  = f'{stem}.png'
        new_ref  = f'{stem}.webp'
        if old_ref in updated:
            updated = updated.replace(old_ref, new_ref)
            changes.append(f'{old_ref} → {new_ref}')

    if changes:
        code_path.write_text(updated, encoding='utf-8')
        for ch in changes:
            print(f'  ✓  {code_path.name}: {ch}')
    else:
        print(f'  —  {code_path.name}: упоминаний не найдено')

# ── 3. Итог ───────────────────────────────────────────────────────────────────
print()
print('═' * 66)
print('  Готово. Оригинальные PNG НЕ удалены.')
print('  Проверь .webp визуально, затем удали оригиналы:')
print('    find images/ -name "*.png" -delete')
