> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: 6 风格 commit message（conventional / emoji / poetic / 鲁迅 / 俳句 / changelog）

---

# commit-poet

> Turn your `git diff` into commit messages worth reading.

An [OpenClaw](https://openclawskill.ai) skill for OpenClaw that reads your git diffs and generates accurate, well-crafted commit messages in six distinct styles. From strict Conventional Commits to emoji one-liners to literary haiku, commit-poet analyzes your actual changes -- file-by-file, line-by-line -- and produces messages that are both truthful and stylish.

## Style Gallery

### conventional
Follows the [Conventional Commits](https://www.conventionalcommits.org/) spec. Imperative mood, scoped types, under 72 chars.

```
feat(auth): add user registration with email verification

- Add POST /api/auth/register endpoint
- Implement email verification service with token generation
```
```
fix(orders): prevent duplicate orders from concurrent requests
```
```
refactor(validation): extract shared validation logic into middleware
```

### emoji
Emoji-prefixed lines, one per logical change. Multiple changes get multiple emoji lines.

```
✨ Add user registration with email verification
📧 Implement verification email service
✅ Add registration flow integration tests
```
```
✨ Add dark mode with theme toggle component
🐛 Fix CSS overflow bug in main stylesheet
📦 Update react (18.2->18.3) and tailwind (3.3->3.4)
🔥 Remove deprecated utility functions
```

### poetic
English verse. Creativity serves clarity, never distorts it.

```
A door now opens for the yet-unknown,
where users sign their names and make this place their own.
An email flies to prove they're real, and tests confirm the deal.
```
```
Three controllers carried the same heavy load, validation repeated down every road.
Now a single middleware bears that weight, and the controllers breathe, clean and straight.
```

### 鲁迅
鲁迅杂文风格，讽刺中带深刻。中文输出。

```
从前，用户想要进门，却发现门上连个门铃都没有。今天我装了门铃，还附赠了验证码——毕竟，不是什么人都配进来的。
```
```
三个 controller 各自搬着同样的砖，干着同样的活，却互不相识。我把砖堆到了一处，告诉它们：从今往后，验证这事，有人统一管了。
```
```
白天太亮了，我给它加了个暗色模式——权当是对光明的讽刺。顺手修了个 CSS 溢出的毛病，扔掉了一堆早该进坟墓的废弃函数。八个文件，一场小型革命。
```

### haiku
5-7-5 syllable haiku. Every line must reflect the actual changes.

```
New users arrive
Email proves identity
Tests guard the gateway
```
```
Shared code extracted
Three controllers now breathe free
One truth validates
```
```
Dark mode now exists
Old code swept, bugs fixed, deps fresh
Eight files tell the tale
```

### changelog
Keep a Changelog format with Added/Fixed/Changed/Removed prefixes.

```
Added: user registration endpoint (POST /api/auth/register)
Added: email verification service with token generation
Added: integration tests for registration flow
```
```
Added: dark mode theme (src/themes/dark.css) and ThemeToggle component
Fixed: CSS overflow issue in main stylesheet
Changed: updated react 18.2->18.3, tailwind 3.3->3.4
Removed: deprecated utility functions (src/utils/deprecated.ts, -89 lines)
```

## Features

- **6 commit styles** -- conventional, emoji, poetic, 鲁迅, haiku, changelog
- **Accuracy first** -- creative styles never invent changes not in the diff
- **Smart analysis** -- detects change type and scope from file paths
- **Multi-file awareness** -- 3+ files changed triggers itemized body
- **Breaking change detection** -- flags changed APIs, removed interfaces
- **Multi-style output** -- request several styles at once
- **Interactive refinement** -- adjust style, length, or detail after generation
- **Bilingual triggers** -- responds to Chinese and English prompts

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/commit-poet
```

## Quick Start

```bash
git add -p                              # stage your changes
# In OpenClaw, say: "write me a commit message"
```

Or preview the diff first with the helper script:

```bash
./scripts/get_diff.sh --cached          # staged changes with stats
./scripts/get_diff.sh --cached src/     # staged changes in src/ only
./scripts/get_diff.sh                   # unstaged changes
```

## How It Works

1. **Read** -- runs `git diff --stat` for scope, then the full diff for details
2. **Analyze** -- determines change type, affected modules, additions/removals, and infers intent
3. **Style** -- applies chosen style (default: conventional) with strict formatting rules
4. **Generate** -- produces the message, then offers interactive refinement

## Style Rules

- **conventional** -- Conventional Commits spec. Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`, `build`. Scope from directory name. Imperative mood, lowercase, no period, under 72 chars. `BREAKING CHANGE:` footer when needed.
- **emoji** -- One emoji-prefixed line per logical change. `✨` feature, `🐛` bugfix, `♻️` refactor, `📝` docs, `🎨` style, `✅` tests, `🔧` config, `⚡` perf, `🔥` removal, `📦` deps, `🚀` deploy, `🔒` security.
- **poetic** -- Short English verse. Rhyme optional, technical accuracy mandatory.
- **鲁迅** -- Chinese output in Lu Xun's sardonic essay style. Sharp metaphors, dry wit.
- **haiku** -- Strict 5-7-5 syllable structure. Must reflect actual changes.
- **changelog** -- `Added:` / `Fixed:` / `Changed:` / `Removed:` prefixes per Keep a Changelog.

## When to Use Which Style

| Style | Best For |
|-------|----------|
| `conventional` | CI-parsed commits, auto-generated changelogs, professional codebases |
| `emoji` | Open source projects, visual scanning of git log |
| `poetic` | Personal projects, hackathons, making reviewers smile |
| `鲁迅` | Chinese-speaking teams, codebases that have earned some sarcasm |
| `haiku` | Minimalist repos, small atomic commits |
| `changelog` | Projects maintaining CHANGELOG.md, release-oriented workflows |

## Trigger Phrases

| Language | Phrases |
|----------|---------|
| English | "commit message", "git commit", "write a commit" |
| Chinese | "提交信息", "帮我写提交说明" |

## Project Structure

```
commit-poet/
├── SKILL.md                  # Skill definition (styles, rules, analysis pipeline)
├── scripts/
│   └── get_diff.sh           # Formatted diff helper with stats
├── references/
│   └── examples.md           # 30 examples: 5 scenarios x 6 styles
├── assets/                   # Skill assets
└── README.md
```

## get_diff.sh Options

| Option | Description | Example |
|--------|-------------|---------|
| *(none)* | Show unstaged changes | `./scripts/get_diff.sh` |
| `--cached` | Show staged changes | `./scripts/get_diff.sh --cached` |
| `path` | Filter to specific path | `./scripts/get_diff.sh src/` |
| `--cached path` | Staged changes in path | `./scripts/get_diff.sh --cached src/` |
| `-h`, `--help` | Print usage info | `./scripts/get_diff.sh --help` |

## Requirements

- **Git** -- must be inside a git repository
- **Bash** -- for the `get_diff.sh` helper script
- **OpenClaw** with OpenClaw skill support

## Contributing

To add a new style, update `SKILL.md` with rules and examples, and add matching examples to `references/examples.md`.

## License

MIT
