# RetroVault 5.0

Lightweight retro launcher gebouwd in Python + PyGame.

## Installatie

```bash
pip install -r requirements.txt
```

## Starten

```bash
python main.py
```

## Besturing

| Actie             | Keyboard         | Controller (Xbox)   |
|-------------------|------------------|---------------------|
| Carrousel links   | ← pijl           | D-pad links / Stick |
| Carrousel rechts  | → pijl           | D-pad rechts / Stick|
| Selecteren        | Enter / Space    | A                   |
| Terug             | Esc / Backspace  | B                   |
| Menu openen       | M of F1          | Start               |
| Afsluiten         | Q                | Select              |
| Fullscreen toggle | F11              | —                   |

## Mappenstructuur

```
retrovault/
├── main.py
├── requirements.txt
├── config/
│   ├── config_manager.py
│   ├── settings.json        ← auto-aangemaakt bij eerste start
│   └── consoles.json        ← auto-aangemaakt bij eerste start
├── ui/
│   └── screen_home.py       ← Sessie 1: hoofdscherm + carrousel
├── input/
│   └── controller.py        ← Keyboard + gamepad
├── launcher/
│   └── runner.py            ← Emulator opstarten
└── assets/
    ├── icons/               ← Plaats hier console icons (.png)
    ├── covers/              ← Plaats hier game covers (.png)
    └── backgrounds/         ← Achtergrondafbeeldingen
```

## Config – consoles.json

Bewerk `config/consoles.json` om:
- Consoles toe te voegen / te verbergen (`"visible": false`)
- Emulator-pad in te stellen (`"emulator_cmd"`)
- Games toe te voegen met cover art

```json
{
  "id": "snes",
  "name": "Super Nintendo",
  "icon": "assets/icons/snes.png",
  "visible": true,
  "emulator_cmd": "retroarch -L cores/snes9x_libretro.dll",
  "roms_path": "roms/snes/",
  "games": [
    {
      "id": "smw",
      "name": "Super Mario World",
      "rom": "roms/snes/smw.smc",
      "cover": "assets/covers/snes/smw.png"
    }
  ]
}
```

## Achtergrond instellen

Zet in `config/settings.json`:
```json
{
  "background_image": "assets/backgrounds/mijn_achtergrond.jpg"
}
```

## Sessies roadmap

- [x] Sessie 1: Architectuur + hoofdscherm + carrousel + keyboard
- [ ] Sessie 2: Console bibliotheekscherm (games grid + cover art)
- [ ] Sessie 3: Menu (consoles tab, scraper placeholder, server placeholder)
- [ ] Sessie 4: Emulator starten via launcher
- [ ] Sessie 5: Controller polish + achtergrond instellen via menu
