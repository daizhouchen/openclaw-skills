> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: 自然语言→5 风格 SVG 图标（outline / filled / duotone / hand-drawn / pixel）

---

# SVG Icon Forge

> Describe an icon in words. Get a pixel-perfect SVG in any style.

SVG Icon Forge is an [OpenClaw](https://openclawskill.ai) skill that generates production-ready SVG icons from natural language descriptions. Tell it what you need -- a search icon, a trash can, a play button -- and it produces clean, optimized, theme-aware SVG in any of 5 visual styles. It handles single icons, batch sets with visual consistency, and can output ready-to-use React or Vue components.

## Style Gallery

SVG Icon Forge supports 5 distinct icon styles. If no style is specified, `outline` is used by default.

| Style | Stroke / Fill | Visual Character |
|-------|--------------|------------------|
| **outline** | `stroke="currentColor"` width 2, `fill="none"` | Clean 24x24 line icons inspired by Lucide/Feather. Round caps and joins. Minimal geometry, no unnecessary complexity. |
| **filled** | `fill="currentColor"`, no stroke | Solid, bold shapes that use negative space (cutouts) for detail. Designed to stay recognizable at small sizes. |
| **duotone** | Two `<g>` layers: primary at full opacity, secondary at `opacity="0.3"` | Two-tone depth effect. Background layer provides context, foreground layer carries the main shape. Layers grouped for easy theming. |
| **hand-drawn** | `stroke="currentColor"` width 1.5--2, `fill="none"` | Irregular, wobbly paths using cubic bezier curves with subtle control-point offsets. No perfect circles or straight lines -- deliberate human imperfection. |
| **pixel** | `fill="currentColor"` | Pixel-art aesthetic built from `<rect>` elements on integer coordinates. Strict grid alignment, no anti-aliasing. On-pixels use `currentColor`, off-pixels are transparent. |

### Example: Search icon in outline vs. pixel

**Outline** -- stroked circle and line:
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
  <title>Search</title>
  <circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>
</svg>
```

**Pixel** -- grid-aligned rectangles:
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
     fill="currentColor"><title>Search</title>
  <rect x="8" y="4" width="6" height="2"/>
  <rect x="6" y="6" width="2" height="2"/><rect x="14" y="6" width="2" height="2"/>
  <rect x="4" y="8" width="2" height="6"/><rect x="16" y="8" width="2" height="6"/>
  <rect x="8" y="16" width="6" height="2"/>
  <rect x="16" y="16" width="2" height="2"/><rect x="18" y="18" width="2" height="2"/>
</svg>
```

## Built-in Icon Library

15 parameterized templates across 4 categories, each available in all 5 styles (75 total variants):

| Category | Icon | Description |
|----------|------|-------------|
| **Navigation** | `arrow_right` | Right-pointing arrow |
| | `menu` | Hamburger menu (three horizontal lines) |
| | `close` | X / close button |
| | `search` | Magnifying glass |
| **Actions** | `edit` | Pencil / edit |
| | `delete` | Trash can |
| | `save` | Floppy disk |
| | `share` | Network nodes with connecting lines |
| **Status** | `check` | Checkmark |
| | `warning` | Triangle with exclamation |
| | `error` | Circle with X |
| | `info` | Circle with "i" |
| **Media** | `play` | Play triangle |
| | `pause` | Two vertical bars |
| | `volume` | Speaker with sound waves |

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/svg-icon-forge
```

## Quick Start

After installation, describe what you need in natural language:

- "Generate a search icon in duotone style"
- "Create an icon set for a media player: play, pause, volume -- outline style"
- "I need a hand-drawn trash icon for my app"
- "Give me a filled checkmark icon wrapped as a React component"

For icon sets, the skill produces an SVG sprite sheet combining all icons into `<symbol>` elements:

```svg
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="icon-play" viewBox="0 0 24 24"><!-- paths --></symbol>
  <symbol id="icon-pause" viewBox="0 0 24 24"><!-- paths --></symbol>
</svg>
```

Usage: `<svg><use href="#icon-play"/></svg>`

## SVG Optimizer

The bundled `scripts/optimize_svg.py` validates and optimizes every generated icon.

**Strips:** editor metadata (`inkscape:*`, `sodipodi:*`, `sketch:*`, `serif:*`), redundant attributes (`data-name`, `class`, `style`, `xml:space`), editor elements (`<metadata>`, `<namedview>`, empty `<defs>`), and extraneous namespace declarations.

**Optimizes:** collapses whitespace in path `d` data, normalizes `viewBox`/`width`/`height` to the 24x24 standard.

**Validates:** `viewBox` is `0 0 24 24`, `currentColor` is present, file size under 1 KB, `<title>` element exists.

```bash
python3 scripts/optimize_svg.py icon.svg -o icon_opt.svg   # optimize
python3 scripts/optimize_svg.py icon.svg --validate         # validate only
python3 scripts/optimize_svg.py --string '<svg>...</svg>'   # optimize a string
```

## Quality Standards

Every icon produced by SVG Icon Forge meets these criteria:

- **ViewBox**: `viewBox="0 0 24 24"` with `width="24" height="24"`
- **Themeable colors**: `currentColor` exclusively -- icons adapt to any CSS color
- **Pixel alignment**: Integer coordinates preferred; half-pixels only when centering requires it
- **Compact paths**: Relative path commands (`m`, `l`, `c`, `a`) where practical
- **File size**: Under 1 KB per icon (typical range: 262--340 bytes optimized)
- **No bloat**: No editor metadata, no unnecessary IDs, no inline styles
- **Accessible**: `<title>` element in every SVG
- **Standards-compliant**: Valid XML with proper `xmlns` for standalone files

## Component Wrappers

### React

```jsx
export const SearchIcon = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round"
       strokeLinejoin="round" {...props}>
    <title>Search</title>
    <circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>
  </svg>
);
```

### Vue

```vue
<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="2" stroke-linecap="round"
       stroke-linejoin="round" v-bind="$attrs">
    <title>Search</title>
    <circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>
  </svg>
</template>
<script setup>
defineProps({ size: { type: Number, default: 24 } });
</script>
```

## Trigger Phrases

The skill activates when user input matches these patterns:

| Language | Phrases |
|----------|---------|
| Chinese | "图标", "SVG图标", "UI图标", "生成图标集" |
| English | "icon", "SVG icon", "generate icons", "icon set" |

## Project Structure

```
svg-icon-forge/
├── SKILL.md                     # Skill definition, style specs, quality rules
├── README.md
├── scripts/
│   ├── optimize_svg.py          # SVG optimizer and validator
│   └── test_skill.py            # Test suite (75 icon/style combinations)
├── assets/
│   └── icon_templates.py        # 15 parameterized templates x 5 styles
├── references/
│   └── examples.md              # Gallery of 10 icons in all 5 styles
└── test_output/                 # Pre-generated sample SVGs
```

## Test Results

The test suite (`scripts/test_skill.py`) runs two passes:

1. **Sample test** -- 5 representative icons (one per style) are generated, optimized, XML-validated, size-checked, and run through full quality validation.
2. **Bulk test** -- All 15 icons x 5 styles = 75 combinations are generated and XML-validated.

Results: **75/75 pass**. All SVGs are valid XML, all under 1 KB, all quality checks green.

## Requirements

- Python 3.8+ (standard library only -- no external packages)

## Contributing

Contributions are welcome. To add a new icon template, create a function in `assets/icon_templates.py` that returns SVG strings for all 5 styles, then register it in the `ALL_ICONS` dictionary. Run `python3 scripts/test_skill.py` to verify.

## License

MIT
