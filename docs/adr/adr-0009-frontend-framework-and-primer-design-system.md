---
title: "ADR-0009: Frontend Framework and GitHub Primer Design System"
status: "Accepted"
date: "2026-03-07"
authors: "HVE Stem Team"
tags: ["architecture", "web-ui", "frontend", "design-system", "primer", "react"]
supersedes: ""
superseded_by: ""
---

# ADR-0009: Frontend Framework and GitHub Primer Design System

## Status

**Accepted**

## Context

ADR-0008 established that `stem serve` uses FastAPI to serve both the API and
bundled static frontend assets. The current frontend is a placeholder
`index.html` that needs to be replaced with a real application capable of:

- **Dynamic, real-time updates.** When long-running backend commands like
  `stem assess` or `stem remediate` are running, the UI must reflect progress
  and results as they arrive — not after a full page reload.
- **Rich data presentation.** Assessment heatmaps, traffic-light indicators,
  checklist tables, and trend charts require a component-driven UI.
- **GitHub-native look and feel.** Stem is a GitHub-centric tool. Adopting
  GitHub's design system ([Primer](https://primer.style/)) ensures visual
  consistency with the GitHub ecosystem and immediate familiarity for the
  target audience (team leads and DevOps engineers who live in GitHub).
- **Single-package distribution.** Per ADR-0008, the frontend must be
  bundled as static assets inside the Python package — no Node.js runtime
  required at deployment time.
- **Fast development inner loop.** Frontend developers must be able to edit
  code and see changes in the browser within seconds, without rebuilding and
  reinstalling the Python package on every change.

The Primer design system offers multiple integration surfaces:

| Surface                                                                             | Description                                                      |
|-------------------------------------------------------------------------------------|------------------------------------------------------------------|
| **[Primer React](https://primer.style/react)** (`@primer/react`)                   | Full React component library — buttons, navigation, data tables, dialogs, etc. |
| **[Primer CSS](https://primer.style/css)** (`@primer/css`)                          | Utility-first CSS framework — usable without React.              |
| **[Primer Primitives](https://primer.style/foundations/primitives)** (`@primer/primitives`) | Design tokens (colours, spacing, typography) as CSS variables.   |
| **[Primer ViewComponents](https://primer.style/view-components)**                   | Rails-specific; not applicable.                                  |

The richest, most actively maintained surface is **Primer React**. Primer CSS
is available but provides only styling — no interactive components, no
accessibility wiring, no state management. For the dynamic dashboard Stem
requires, a component library is essential.

## Options Considered

### Option A — React (Vite) + Primer React (Recommended)

Use **React** with **Vite** as the build tool, consuming the full
**`@primer/react`** component library.

| Aspect                   | Detail                                                                                       |
|--------------------------|----------------------------------------------------------------------------------------------|
| **Framework**            | React 19 (current stable)                                                                    |
| **Build tool**           | Vite 6 — fast HMR, optimised production builds, static export out of the box                 |
| **Design system**        | `@primer/react` — official GitHub component library with 60+ components                      |
| **Real-time updates**    | Server-Sent Events (SSE) consumed via React hooks; components re-render on new data           |
| **Static export**        | `vite build` produces a `dist/` folder of plain HTML/JS/CSS — no server required              |
| **Bundle into Python**   | Copy `dist/` into `src/stem/data/static/` before `uv build`                                  |
| **Dev inner loop**       | Vite dev server (port 5173) with HMR + API proxy to FastAPI (port 8777); sub-second feedback  |

**Why React:** Primer React is the primary Primer integration surface. It
provides accessible, styled components out of the box (DataTable, TreeView,
ActionMenu, PageLayout, Flash, ProgressBar, etc.) that map directly to Stem's
UI needs. Choosing React means zero custom styling for standard UI patterns.

**Why Vite:** Vite is the modern standard for React builds. It starts in
milliseconds, provides instant Hot Module Replacement (HMR), and produces
highly optimised static bundles. Unlike Next.js (mentioned in the original
NARRATIVE.md), Vite does not require a Node.js server at runtime — the output
is pure static files, perfectly aligned with the single-package distribution
requirement from ADR-0008.

### Option B — Next.js (Static Export) + Primer React

Use **Next.js** with `output: 'export'` for a static HTML export.

| Aspect                   | Detail                                                                                       |
|--------------------------|----------------------------------------------------------------------------------------------|
| **Framework**            | Next.js 15 with App Router                                                                   |
| **Build tool**           | Next.js built-in (Webpack/Turbopack)                                                         |
| **Design system**        | `@primer/react` — same as Option A                                                           |
| **Real-time updates**    | SSE via React hooks — same as Option A                                                       |
| **Static export**        | `next build && next export` produces a static `out/` folder                                  |
| **Bundle into Python**   | Copy `out/` into `src/stem/data/static/`                                                     |
| **Dev inner loop**       | `next dev` with Fast Refresh + custom proxy or `rewrites` to FastAPI                         |

**Drawbacks compared to Option A:**

- Next.js is designed for server-rendered and edge-deployed applications.
  Using `output: 'export'` disables its most valuable features (SSR, ISR,
  API routes, middleware). What remains is effectively a React SPA with more
  configuration overhead.
- Next.js static export has gotchas: no `next/image` optimisation, no
  dynamic routes without `generateStaticParams`, no middleware. These
  limitations create ongoing friction for a dashboard that is inherently
  dynamic and client-rendered.
- Slower cold starts for the dev server compared to Vite.
- Larger dependency tree (Webpack, SWC, Next.js runtime code) for no
  benefit in a purely static-export scenario.

### Option C — Vanilla JS + Primer CSS (No Framework)

Use plain HTML/JavaScript with **Primer CSS** for styling.

| Aspect                   | Detail                                                                                       |
|--------------------------|----------------------------------------------------------------------------------------------|
| **Framework**            | None — vanilla JS or lightweight library (e.g., htmx, Alpine.js)                             |
| **Build tool**           | Optional (esbuild or none)                                                                   |
| **Design system**        | `@primer/css` — utility classes only, no interactive components                               |
| **Real-time updates**    | Manual DOM manipulation via `EventSource` API                                                |
| **Static export**        | Already static — no build step required                                                      |
| **Bundle into Python**   | Files are directly in `src/stem/data/static/`                                                |
| **Dev inner loop**       | Edit HTML/JS and reload browser; or use a simple live-reload server                          |

**Drawbacks:**

- No component library for complex UI patterns (data tables with sorting,
  accessible dialogs, tree views). Every interactive element must be built
  from scratch.
- Primer CSS provides only styling utilities — no accessibility guarantees,
  no keyboard navigation, no ARIA attributes.
- Manual DOM manipulation for real-time updates becomes brittle and hard to
  maintain as the dashboard grows (heatmaps, trend charts, multi-repo views).
- No type safety, no component composition model, significantly more code to
  achieve the same result.

### Option D — Vue / Svelte + Primer CSS

Use a non-React SPA framework with Primer CSS for styling.

| Aspect                   | Detail                                                                                       |
|--------------------------|----------------------------------------------------------------------------------------------|
| **Framework**            | Vue 3 or Svelte 5                                                                            |
| **Build tool**           | Vite (both have first-class Vite support)                                                    |
| **Design system**        | `@primer/css` only — no official component library for Vue or Svelte                         |
| **Real-time updates**    | Framework-native reactivity + `EventSource`                                                  |
| **Static export**        | `vite build` produces static assets — same as Option A                                       |
| **Bundle into Python**   | Copy `dist/` into `src/stem/data/static/`                                                    |
| **Dev inner loop**       | Vite dev server with HMR + API proxy — same as Option A                                      |

**Drawbacks:**

- Primer React is the only official component library. Vue and Svelte would
  only get Primer CSS (utility classes) and Primer Primitives (design tokens).
  Every component must be hand-built to match the GitHub look and feel.
- Active Primer community contributions, bug fixes, and new components are
  React-only. Choosing Vue/Svelte means maintaining a parallel component
  effort.

## Decision

Adopt **Option A: React (Vite) + Primer React**.

The frontend will be a React single-page application built with Vite, using
`@primer/react` as the component library and `@primer/primitives` for design
tokens.

### Project layout

```text
app/                          # Frontend source (NOT bundled in Python package)
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx              # Entry point
    ├── App.tsx               # Root component with Primer ThemeProvider
    ├── api/                  # API client + SSE hooks
    ├── pages/                # Route-level components (Dashboard, RepoDetail, …)
    └── components/           # Shared UI components
```

The `app/` directory lives at the repository root alongside `src/stem/`. It is
a standalone Node.js project with its own `package.json` and is **not**
included in the Python wheel — only the build output is.

### Static asset bundling

The production build workflow:

```bash
cd app && npm ci && npm run build    # Produces app/dist/
cp -r app/dist/* src/stem/data/static/   # Bundle into Python package
uv build                                  # Build the wheel
```

This can be scripted in a `Makefile` or GitHub Actions workflow. The
`src/stem/data/static/` directory is gitignored except for a minimal
placeholder `index.html` used when developing without the frontend build.

### Real-time updates via Server-Sent Events

For dynamic progress during `stem assess` and `stem remediate`, the FastAPI
backend exposes SSE endpoints:

```text
GET /api/assess/stream    → text/event-stream
GET /api/remediate/stream → text/event-stream
```

The React frontend subscribes via `EventSource` (or a React hook wrapper) and
re-renders components as events arrive. This is simpler than WebSockets for
the one-directional progress-reporting pattern Stem needs, and SSE works
natively in browsers without additional libraries.

### Development inner loop

For day-to-day frontend development, there is no need to rebuild or reinstall
the Python package:

```bash
# Terminal 1 — Start the API server
uv run stem serve --no-browser

# Terminal 2 — Start the Vite dev server with API proxy
cd app && npm run dev
```

The Vite configuration proxies `/api/*` requests to `http://localhost:8777`,
allowing the React app to talk to the live FastAPI backend:

```typescript
// app/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8777",
    },
  },
});
```

Developers open `http://localhost:5173` in the browser. Vite provides instant
HMR — changing a React component updates the browser in under a second. The
API proxy ensures all backend calls work identically to production.

### Key dependencies

| Package                | Role                                      |
|------------------------|-------------------------------------------|
| `react`, `react-dom`  | UI framework                              |
| `@primer/react`       | GitHub design system component library    |
| `@primer/primitives`  | Design tokens (colours, spacing, type)    |
| `react-router`        | Client-side routing (Dashboard, Detail…)  |
| `vite`                | Build tool and dev server                 |
| `typescript`          | Type safety                               |

## Consequences

### Positive

- **POS-001**: Full access to 60+ Primer React components (DataTable,
  TreeView, ActionMenu, PageLayout, Flash, ProgressBar, NavList, etc.)
  gives the dashboard a native GitHub look and feel with minimal custom CSS.
- **POS-002**: Vite's dev server provides sub-second HMR feedback. Combined
  with the API proxy, frontend developers can iterate on the UI without
  touching the Python package.
- **POS-003**: `vite build` produces optimised static assets (tree-shaken,
  code-split, minified) that drop directly into `src/stem/data/static/`
  with no runtime server required — fully compatible with ADR-0008.
- **POS-004**: SSE for real-time updates is a lightweight, standards-based
  pattern that avoids the complexity of WebSocket connection management
  while providing the dynamic feedback users expect during long-running
  operations.
- **POS-005**: TypeScript provides type safety across the frontend codebase,
  catching integration errors (e.g., mismatched API response shapes) at
  compile time.
- **POS-006**: React is the most widely adopted frontend framework, ensuring
  a large talent pool and extensive ecosystem of compatible libraries
  (charting, testing, etc.).

### Negative

- **NEG-001**: Node.js is required as a **development-time** dependency for
  building the frontend. It is NOT required at runtime — end users never need
  Node.js. This adds a toolchain requirement for contributors working on the
  web UI.
- **NEG-002**: The `app/` directory introduces a second package ecosystem
  (npm) alongside Python (uv). Contributors must be comfortable with both,
  though frontend and backend work is largely independent.
- **NEG-003**: The Primer React library is maintained by GitHub and follows
  GitHub's design evolution. Breaking changes in `@primer/react` major
  versions will require migration effort. Pinning to a specific major version
  mitigates this.
- **NEG-004**: The build-and-copy step (`npm run build` → copy to
  `src/stem/data/static/`) adds a step to the release process. This is
  mitigated by scripting it in CI.
- **NEG-005**: The `app/` directory name is generic. If ambiguity arises
  with other project components, it can be renamed without affecting the
  Python package or the bundling process.

### Neutral

- This decision **supersedes the NARRATIVE.md mention of Next.js**. The
  NARRATIVE stated that the frontend "will eventually be built as a static
  HTML export" using Next.js. After analysis, Vite + React produces the same
  static output with less complexity, fewer gotchas, and a faster dev
  experience. The NARRATIVE.md should be updated to reflect this change.
- The `app/` directory is excluded from the Python wheel via Hatchling
  configuration. Only `src/stem/data/static/` (the build output) is packaged.

## Alternatives Considered

Detailed above in the Options section:

- **Option B (Next.js + Primer React)**: Rejected. Next.js static export
  disables its best features and adds unnecessary complexity.
- **Option C (Vanilla JS + Primer CSS)**: Rejected. No component library
  means rebuilding accessible UI patterns from scratch; not viable for a
  dynamic dashboard.
- **Option D (Vue/Svelte + Primer CSS)**: Rejected. No official Primer
  component library for these frameworks; would require maintaining a
  parallel component effort.
