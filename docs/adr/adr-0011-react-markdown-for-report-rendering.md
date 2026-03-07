---
title: "ADR-0011: Use react-markdown for Report Rendering"
status: "Accepted"
date: "2026-03-07"
authors: "HVE Stem Team"
tags: ["architecture", "web-ui", "frontend", "markdown", "security"]
supersedes: ""
superseded_by: ""
---

# ADR-0011: Use react-markdown for Report Rendering

## Status

**Accepted**

## Context

The `MarkdownReport` component renders assessment reports produced by
`stem assess`. These reports are Markdown documents containing headings,
tables, lists, code blocks, bold/italic text, links, and blockquotes.

The current implementation uses a hand-rolled regex-based Markdown-to-HTML
converter (`markdownToHtml`) that injects the result via React's
`dangerouslySetInnerHTML`. Alongside it, ~140 lines of hand-written CSS in
`index.css` approximate GitHub's Markdown styling under the `.markdown-body`
class.

This approach has several problems:

| Problem                  | Detail                                                                              |
|--------------------------|-------------------------------------------------------------------------------------|
| **Security**             | `dangerouslySetInnerHTML` bypasses React's XSS protections. Although the converter  |
|                          | escapes `&`, `<`, and `>` up-front, the subsequent regex passes re-introduce raw    |
|                          | HTML tags, creating a fragile trust boundary.                                       |
| **Correctness**          | The regex handles only a subset of CommonMark and none of GFM (no task lists, no    |
|                          | strikethrough, no autolinks, no footnotes). Edge cases in nesting, indentation,     |
|                          | and multi-line constructs silently produce broken output.                            |
| **Maintainability**      | ~110 lines of interleaved regex replacements plus ~140 lines of hand-written CSS    |
|                          | that must be kept in sync with GitHub's evolving design tokens. Any new Markdown    |
|                          | feature requires writing and debugging more regex.                                  |
| **Styling fidelity**     | The custom CSS approximates GitHub's rendering but diverges in spacing, font sizes, |
|                          | table striping, and dark-mode behaviour.                                            |

## Options Considered

### Option A — `react-markdown` + `remark-gfm` + `github-markdown-css` (Recommended)

Replace the hand-rolled converter with the community-standard
[`react-markdown`](https://github.com/remarkjs/react-markdown) library.

| Aspect              | Detail                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------|
| **Security**        | Builds a React virtual DOM — no `dangerouslySetInnerHTML`, no XSS vector by default.    |
| **Compliance**      | 100 % CommonMark; 100 % GFM when paired with the `remark-gfm` plugin.                  |
| **Styling**         | `github-markdown-css` provides the exact CSS GitHub.com uses for rendered Markdown,     |
|                     | with built-in light, dark, and high-contrast theme variants.                            |
| **Adoption**        | ~14.6 M weekly npm downloads; actively maintained under the unified/remark ecosystem.   |
| **Extensibility**   | Rich plugin ecosystem (remark / rehype) for syntax highlighting, math, etc.             |
| **Bundle cost**     | `react-markdown` ≈ 52 kB unpacked; `remark-gfm` ≈ 28 kB; `github-markdown-css` ≈ 170 kB. |

### Option B — `marked` + `DOMPurify`

Use the [`marked`](https://github.com/markedjs/marked) library to convert
Markdown to an HTML string, sanitise with `DOMPurify`, and inject via
`dangerouslySetInnerHTML`.

| Aspect              | Detail                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------|
| **Security**        | `DOMPurify` mitigates XSS but still relies on `dangerouslySetInnerHTML`.                |
| **Compliance**      | Good CommonMark and GFM support.                                                        |
| **Styling**         | Same `github-markdown-css` can be used.                                                 |
| **React integration** | Produces a raw HTML string, not a virtual DOM — loses React's diffing and component   |
|                     | composition model.                                                                      |

Rejected: the continued use of `dangerouslySetInnerHTML` is unnecessary when
`react-markdown` renders directly to React elements.

### Option C — Keep the hand-rolled converter

Continue maintaining the regex-based converter.

Rejected: ongoing maintenance burden, known correctness gaps, and the
`dangerouslySetInnerHTML` XSS surface outweigh the zero-dependency advantage.

## Decision

Adopt **Option A**: replace the hand-rolled Markdown converter with
`react-markdown`, `remark-gfm`, and `github-markdown-css`.

### Changes

1. **Install packages**: `react-markdown`, `remark-gfm`, `github-markdown-css`.
2. **Rewrite `MarkdownReport.tsx`**: delete the `markdownToHtml` function and
   render via the `<Markdown>` component with the `remarkGfm` plugin.
3. **Import `github-markdown-css`** in the component for the `.markdown-body`
   class styling.
4. **Remove** the ~140 lines of hand-written `.markdown-body` CSS from
   `index.css`.

## Consequences

### Positive

- **Eliminates XSS surface** — no more `dangerouslySetInnerHTML`.
- **Full GFM support** — tables, task lists, strikethrough, autolinks, and
  footnotes work out of the box.
- **Pixel-perfect GitHub styling** — `github-markdown-css` is generated from
  GitHub.com itself, with automatic light/dark theme support.
- **~250 lines of custom code removed** (regex converter + CSS).
- **Extensible** — future needs (syntax highlighting, math) are a plugin
  install away.

### Negative

- Adds three new runtime dependencies (~250 kB unpacked total).
- `github-markdown-css` includes styles for elements the reports may not use
  today (images, details/summary, etc.) — a minor overhead.

### Neutral

- The `MarkdownReport` component API (`content: string`) remains unchanged;
  no consumer changes are required.
