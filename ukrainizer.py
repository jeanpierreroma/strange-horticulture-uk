"""Українізатор Strange Horticulture.
Вписує український переклад замість російської мови у файл sharedassets0.assets гри
(у словник TranslationData, звідки гра бере весь текст). Оригінал зберігається поруч.
Запуск: ukrainizer [шлях до теки гри] [--restore]"""
import sys, os, re, json, shutil, struct, hashlib, pathlib, platform

APP = "Strange Horticulture"
SLOT = "ru"
BACKUP = "sharedassets0.assets.original"
HERE = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent))
sys.path.insert(0, str(HERE))
import odin, serialized


def steam_roots():
    home = pathlib.Path.home()
    roots = []
    if platform.system() == "Windows":
        try:
            import winreg
            for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                              (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(hive, key) as k:
                        for name in ("SteamPath", "InstallPath"):
                            try: roots.append(pathlib.Path(winreg.QueryValueEx(k, name)[0]))
                            except OSError: pass
                except OSError: pass
        except ImportError: pass
        roots += [pathlib.Path(r"C:\Program Files (x86)\Steam"), pathlib.Path(r"C:\Program Files\Steam")]
    elif platform.system() == "Darwin":
        roots.append(home / "Library/Application Support/Steam")
    else:
        roots += [home / ".steam/steam", home / ".local/share/Steam"]
    libs = []
    for r in roots:
        libs.append(r)
        vdf = r / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8", errors="replace")):
                libs.append(pathlib.Path(p.replace("\\\\", "\\")))
    return libs


def find_assets(start):
    start = pathlib.Path(start).expanduser()
    if start.is_file() and start.name == "sharedassets0.assets": return start
    for pat in ("Strange Horticulture_Data/sharedassets0.assets",
                "Strange Horticulture.app/Contents/Resources/Data/sharedassets0.assets",
                "Contents/Resources/Data/sharedassets0.assets",
                "sharedassets0.assets"):
        p = start / pat
        if p.exists(): return p
    return None


def locate(arg):
    if arg:
        return find_assets(arg)
    for lib in steam_roots():
        p = find_assets(lib / "steamapps" / "common" / APP)
        if p: return p
    return None


def translation_data(sf):
    for o in sf.objects:
        raw = sf.raw(o)
        if raw[28:32] != struct.pack("<i", 15) or raw[32:48] != b"TranslationData\x00": continue
        nlen = struct.unpack_from("<i", raw, 28)[0]
        p = 32 + nlen; p += -p % 4
        p += 4
        size = struct.unpack_from("<i", raw, p)[0]; start = p + 4
        end = start + size; end += -end % 4
        return o, raw, p, start, end, raw[start:start + size]
    raise SystemExit("Не знайшов у файлі словник перекладів. Можливо, гра оновилася, і цей українізатор до неї не підходить.")


def entries(data):
    """Повертає (токени, [(ключ, мова, en, значення, початок, кінець)])."""
    toks, _ = odin.parse(data)
    out = []; depth = 0; key = lang = en = None
    for e, name, val, a, b, vs in toks:
        if e in (1, 2, 3, 4): depth += 1
        elif e == 5: depth -= 1
        if e == 39 and name == "$k":
            if depth == 2: key = val
            elif depth == 4: lang = val
        if e == 39 and name == "$v" and depth == 4:
            if lang == "en": en = val
            out.append((key, lang, en, val, vs, b))
    return out


def en_key(s):
    return hashlib.sha1(" ".join((s or "").split()).encode("utf-8")).hexdigest()[:12]


def is_original(items):
    return any(lang == SLOT and re.search("[ыэъЫЭ]", v or "") for _, lang, _, v, _, _ in items)


def patch(path):
    tr = json.loads((HERE / "translation.json").read_text(encoding="utf-8"))
    sf = serialized.SerializedFile(path.read_bytes())
    o, raw, p, start, end, data = translation_data(sf)
    items = entries(data)
    backup = path.with_name(BACKUP)
    if is_original(items):
        shutil.copy2(path, backup)
        print(f"Оригінал збережено: {backup}")
    elif not backup.exists():
        print("Схоже, файл уже змінено раніше, а оригіналу поруч немає. Продовжую без резервної копії.")
    out = bytearray(); last = 0; done = changed_en = 0
    for key, lang, en, val, vs, b in items:
        if lang != SLOT or key not in tr: continue
        variants = tr[key]
        t = variants.get(en_key(en))
        if t is None:
            t = list(variants.values())[-1]; changed_en += 1
        out += data[last:vs] + odin.wstr(t); last = b; done += 1
    out += data[last:]
    pad = b"\x00" * (-(start + len(out)) % 4)
    sf.replace(o, raw[:p] + struct.pack("<i", len(out)) + bytes(out) + pad + raw[end:])
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(sf.bytes())
    os.replace(tmp, path)
    print(f"Готово: перекладено {done} рядків.")
    if changed_en:
        print(f"Увага: у {changed_en} рядках англійський текст гри змінився після оновлення, переклад може бути неточним.")
    print("У грі виберіть мову «Русский»: замість неї тепер українська.")


def restore(path):
    backup = path.with_name(BACKUP)
    if not backup.exists():
        raise SystemExit("Резервної копії немає. Поверніть оригінал через Steam: Властивості → Встановлені файли → Перевірити цілісність файлів.")
    shutil.copy2(backup, path)
    print("Оригінальний файл повернуто.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = locate(args[0] if args else None)
    while not path:
        s = input("Не знайшов гру. Перетягніть сюди теку гри (або впишіть шлях) і натисніть Enter: ").strip().strip('"').strip("'")
        if not s: return
        path = find_assets(s.replace("\\ ", " "))
    print(f"Гра: {path}")
    if "--restore" in sys.argv:
        restore(path)
    else:
        patch(path)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0): print(e.code)
    except PermissionError:
        print("Немає доступу до файлу. Закрийте гру й спробуйте ще раз.")
    except Exception as e:
        print(f"Помилка: {e!r}")
    if sys.stdin and sys.stdin.isatty() and getattr(sys, "frozen", False):
        input("\nНатисніть Enter, щоб закрити вікно.")
