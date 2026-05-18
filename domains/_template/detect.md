# Detection Signals — [Domain Name]

Claude checks for these signals at session start. If any primary signal is present, the domain activates. Secondary signals strengthen the match but are not required alone.

## Primary Signals
<!-- File presence, directory names, or config files that strongly indicate this domain -->
- `[filename]` exists at project root
- `[directory]/` exists
- `[config file]` present

## Secondary Signals
<!-- Supporting indicators — imports, patterns, naming conventions -->
- Source files contain imports of `[package]`
- Directory contains `[pattern]` files
- `CLAUDE.md` declares `domains: [name]`

## Conflicts
<!-- Note any domains that shouldn't be active simultaneously, or edge cases -->
- None known

## Manual Override
To force-activate this domain regardless of signals, add to the project's `CLAUDE.md`:
```
domains: [name]
```
