# Strange Horticulture українською

Неофіційний український переклад гри [Strange Horticulture](https://store.steampowered.com/app/1574580/): увесь текст і карта Андерміра.

**Завантажити:** сторінка [Releases](../../releases). Для Windows `ukrainizer-windows.zip`, для Mac `ukrainizer-mac.zip`.

## Як встановити
1. Закрийте гру.
2. Windows: запустіть `ukrainizer.exe`. Mac: двічі клацніть «Встановити.command».
3. У грі виберіть мову «Français». Замість неї тепер українська.

Повернути оригінал: `ukrainizer.exe --restore` (Mac: «Повернути оригінал.command») або перевірка цілісності файлів у Steam.

Після оновлення гри запустіть українізатор ще раз.

## Для розробників
Файлів гри в репозиторії немає. `translation.json` містить лише український текст і короткі хеші англійських рядків, `textures/` — українську карту.
Без збирання: `python3 ukrainizer.py [тека гри] [--restore]` (на Windows `install.bat`).
