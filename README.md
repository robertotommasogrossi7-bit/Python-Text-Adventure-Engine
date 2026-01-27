# Python Text Adventure Engine (CLI)

A minimal, scene-based **text adventure engine** written in Python (terminal/CLI).  
Built as a learning project to practice **project structure**, **state management**, **OOP**, and **command-driven UI**.

## Features
- **Scene loop**: each scene returns the next scene (function) or `None`
- **Global commands** + clean CLI UI (`inventory`, `character`, `inspect`, `take`, `exit`)
- **Character model (OOP)** with HP, attributes, equipment
- **Inventory + equipment**: hands capacity, weapon/armor, sheath (draw / sheath)
- **Inspectable items** with actions and **durability** (example: `use` on the stone)

## Run
```bash
python main.py

Project structure
engine/   # input handling, commands, UI, character logic
models/   # game objects (items)
scenes/   # scenes and story flow
main.py   # entry point


License
MIT
