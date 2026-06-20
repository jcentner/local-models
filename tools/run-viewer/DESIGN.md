# DESIGN.md — Benchmark Run Viewer

Design language: **Vercel / Geist**. Tokens distilled from
[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
(the Vercel `DESIGN.md`) + Anthropic's `frontend-design` anti-slop principles.
This file is the style source of truth; `styles.css` mirrors it.

## 1. Visual theme
Black-and-white precision. Pure black canvas, hairline borders, monospace for all
data/metrics, restrained color used only for status. Dense but calm. No gradients,
no rounded-card-in-card nesting, no Inter, no purple.

## 2. Color palette & roles
| Token | Hex | Role |
|-------|-----|------|
| `--bg` | `#000000` | page canvas |
| `--surface` | `#0a0a0a` | hover / raised |
| `--surface-2` | `#111111` | card headers |
| `--fg` | `#ffffff` | primary text |
| `--dim` | `#888888` | secondary text, labels |
| `--dimmer` | `#5a5a5a` | tertiary / disabled |
| `--border` | `#2e2e2e` | all hairlines |
| `--good` | `#50e3c2` | pass / unchanged state (mint) |
| `--warn` | `#f5a623` | partial / changed state (amber) |
| `--bad` | `#ff4d4f` | fail / error (red) |

Status mapping for `pass@k` / `pass^k` (and per-item `n/k`): `≥0.70` mint ·
`≥0.34` amber · else red. The leaderboard ranks by `pass^k` (reliability); `pass@k`
rides along as a muted `@` secondary.

## 3. Typography
- Display/body: **Geist** (300–600). Tight tracking (`-.01em` on headings).
- Mono: **Geist Mono** — ids, metrics, tool calls, code, labels, crumbs.
- Scale: h2 18px / h3 16px / body 13px / mono-meta 11px / label 10px uppercase.

## 4. Component stylings
- **Run row**: 1px inset selection ring (`#333`), no fill flood. Pass pill right-aligned.
- **Pill**: 999px radius, tinted bg + matching fg from the status token.
- **Card**: 1px border, `--surface-2` header, `--code` body blocks.
- **Tool call**: mono row, 2px left rule (white; red on error).
- **Criterion bar**: 6px track `--track`, white fill.
- **Code**: `<pre>` on `--code`, light Python highlight (keyword red, string mint, number blue).

## 5. Layout
- App shell: top bar + two-pane body (320px rail / fluid detail).
- 12–24px padding rhythm; detail content max-width ~920px (cards) / 780px (wiki prose).

## 6. Depth & elevation
Flat. Separation by 1px borders and surface steps (`#000 → #0a0a0a → #111`), not shadow.

## 7. Do / Don't
- Do: monospace every number; one accent per state; hairline structure.
- Don't: gradients, gl*ow, drop shadows, color outside the three status tokens,
  decorative icon tiles, nested cards.

## 8. Responsive
Single-column collapse below ~720px (rail over detail). Touch targets ≥32px.
