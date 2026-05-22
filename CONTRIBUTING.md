# Contributing to Susurro

Thanks for considering a contribution. Susurro is intentionally small — under ~800 lines of Python total — so it stays readable and maintainable by one person in a weekend.

## Dev setup

```bash
git clone https://github.com/danilobrando/susurro
cd susurro
pip install -e ".[dev]"
```

Run from source:

```bash
python -m susurro
```

Generate the menu bar icons (only needed if you change `scripts/generate_icons.py`):

```bash
python scripts/generate_icons.py
```

Run lint and format checks:

```bash
ruff check .
ruff format --check .
```

## Pull request guidelines

- Keep the surface area small. If a change adds more than ~100 lines, open an issue first to align on scope.
- One concern per PR. Refactors and behavior changes don't mix.
- Don't add hidden network calls — privacy is the product. Anything that touches the network needs to be opt-in and clearly labeled.
- Match the existing style: type hints throughout, no docstrings longer than a sentence, no comments that just restate the code.

## What we welcome

- Bug fixes, especially around macOS permissions and menu bar edge cases.
- New keyboard layouts and language defaults.
- Performance benchmarks across M-series chips and Whisper variants.
- Documentation improvements.

## What we're more cautious about

- New features that grow the dependency tree.
- Anything that turns this into a full Speech-Privacy SaaS. There are other projects for that.

## Reporting bugs

Open an issue with:

- macOS version + chip (e.g. `macOS 26.0 / M3 Pro`)
- Output of `pip show mlx-whisper`
- Last 50 lines of `~/.susurro/susurro.log`
- Steps to reproduce
