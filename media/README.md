# Media

Both assets in this folder are **generated, not drawn**. Edit the scripts and re-run
them; never hand-edit the `.svg` output.

```bash
uv run python media/generate_logo.py        # -> media/logo.svg
uv run python media/generate_screenshot.py  # -> media/screenshot.svg
```

| File | Generator | What it is |
| --- | --- | --- |
| `logo.svg` | `generate_logo.py` | A six-blade iris. Blade geometry is sampled in polar coordinates; the palette is a hue wheel seeded by `sha256("image-generation-mcp")`, so the name determines the colours. |
| `screenshot.svg` | `generate_screenshot.py` | A Claude Code session driving the server. Lines come from the `SESSION` table and every position is computed from the line height. |

`svg.py` holds the shared primitives (escaping, HSL conversion, polygon and text
emitters, document wrapper). No third-party dependency is involved — the scripts run
on the standard library alone.

The figures in the screenshot are from a real run: `gpt-image-2`, 1536x1024 PNG, 28.6 s.
