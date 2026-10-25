# UI Redesign Proposal: IntelliInvoice Color Palette Migration

## Executive Summary

Migrate the Wealth Dashboard from Bootstrap 5 (dark, generic) to a Tailwind CSS design inspired by the IntelliInvoice project's refined color palette and component patterns.

---

## IntelliInvoice Design Analysis

### Core Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| **Primary** | `#4f46e5` (indigo-600) | Buttons, links, active states, chart fills |
| **Primary hover** | `#4338ca` (indigo-700) | Interactive hover states |
| **Sidebar bg** | `#0f172a` (slate-900) | Navigation background |
| **Sidebar text** | `#94a3b8` (slate-400) | Inactive nav items |
| **Sidebar active** | `#818cf8` (indigo-400) + `bg-indigo-600/10` | Active nav highlight |
| **Page bg** | `#f8fafc` (slate-50) | Main content background |
| **Card bg** | `#ffffff` (white) | All card/content surfaces |
| **Card border** | `#e2e8f0` (slate-200) | Subtle card borders |
| **Text primary** | `#0f172a` (slate-900) | Headings, important values |
| **Text secondary** | `#475569` (slate-600) | Body text, labels |
| **Text muted** | `#94a3b8` (slate-400) | Placeholders, hints |
| **Header bg** | `#ffffff` (white) | Top header bar |
| **Header border** | `#e2e8f0` (slate-200) | Header bottom border |

### Accent / Status Colors

| Purpose | Hex | Tailwind Token |
|---------|-----|----------------|
| Success / Paid | `#10b981` (emerald-500) | `bg-emerald-50 text-emerald-700` |
| Warning / Review | `#f59e0b` (amber-500) | `bg-amber-50 text-amber-700` |
| Error / Danger | `#ef4444` (red-500) | — |
| Info | `#3b82f6` (blue-500) | `bg-blue-50 text-blue-700` |
| Neutral / Draft | `#64748b` (slate-500) | `bg-slate-100 text-slate-600` |

### Gradient Usage

| Context | Gradient |
|---------|----------|
| Upload CTA banner | `from-indigo-600 to-violet-600` |
| User avatar | `from-indigo-500 to-purple-500` |

### Component Patterns

1. **Sidebar navigation** — Fixed 256px width, dark (`slate-900`), rounded active items with left border accent
2. **Top header** — White background, 64px height, breadcrumb-style page title
3. **Content area** — `slate-50` background, 24px padding
4. **Cards** — White background, `rounded-xl` (12px), subtle border (`slate-200`), `shadow-sm`
5. **Buttons** — `rounded-lg` (8px), indigo-600 primary, with hover state to indigo-700
6. **Inputs** — `rounded-lg`, transparent border, indigo-500 focus ring
7. **Badges** — `rounded-full`, colored background + matching border, `text-xs font-semibold`
8. **Charts** — Recharts with indigo primary fill, rounded bar tops (`[4,4,0,0]`)
9. **Scrollbars** — Custom: track `slate-100`, thumb `slate-300`, hover `slate-400`, 8px width

---

## Current Wealth Dashboard Issues

| Issue | Current State | Problem |
|-------|---------------|---------|
| **Framework** | Bootstrap 5 CDN | Heavy, opinionated, outdated aesthetic |
| **Navigation** | `navbar-dark bg-dark` | Generic dark bar, no sidebar, no visual hierarchy |
| **Cards** | Bootstrap `card` with colored backgrounds | `bg-primary`, `bg-success`, `bg-warning`, `bg-danger` — harsh, inaccessible |
| **Layout** | Container-based, no sidebar | Flat page, no app-like feel |
| **Charts** | Plotly.js defaults | Generic colors, no brand consistency |
| **Buttons** | `btn btn-primary` | Bootstrap default blue, no brand identity |
| **Tables** | `table table-striped` | Generic, no hover states, no action buttons |
| **Color consistency** | Bootstrap semantic colors | No relationship to IntelliInvoice palette |

---

## Proposed Migration Plan

### Phase 1: Foundation (base.html)

**File:** `wealth_dashboard/templates/base.html`

| Change | Detail |
|--------|--------|
| Remove Bootstrap CSS/JS | Eliminate `bootstrap.min.css` and `bootstrap.bundle.min.js` |
| Add Tailwind CSS via PyPI | Use `tailwindcss` Python package (as already established in project) |
| Sidebar navigation | Fixed 256px `bg-slate-900` sidebar with `Layers`-equivalent icon (wealth icon), nav items with `rounded-lg`, active state `bg-indigo-600/10 text-indigo-400 border-r-2 border-indigo-500` |
| Top header | White `h-16`, `border-b border-slate-200`, page title `text-xl font-bold text-slate-800` |
| Content area | `bg-slate-50`, `p-6 lg:p-8`, `flex-1 overflow-auto` |
| Custom scrollbars | Track `#f1f5f9`, thumb `#cbd5e1`, hover `#94a3b8` |

### Phase 2: Dashboard Template (dashboard.html)

**File:** `wealth_dashboard/templates/dashboard.html`

| Change | Detail |
|--------|--------|
| **Upload CTA** | Gradient banner: `bg-gradient-to-r from-indigo-600 to-violet-600`, `rounded-xl`, `p-8`, white text, white CTA button with `text-indigo-600` |
| **Metrics cards** | Replace Bootstrap colored cards with white `rounded-xl`, `border border-slate-200`, `shadow-sm`. Icon in `bg-slate-50 rounded-full`. Values in `text-2xl font-bold text-slate-900`. Labels in `text-sm font-medium text-slate-500` |
| **Chart containers** | White `rounded-xl`, `border border-slate-200`, `p-6`, chart titles `text-lg font-semibold text-slate-800` |
| **Chart colors** | Plotly traces use indigo palette: `#4f46e5`, `#10b981`, `#f59e0b`, `#ef4444`, `#8b5cf6`, `#ec4899` (matching Intelliinvoice COLORS array) |
| **AI section** | White card, `rounded-xl`, indigo primary button, result alerts use `bg-indigo-50 border-indigo-100` pattern |
| **Tables** | White card, `rounded-xl`, header `bg-slate-50 text-slate-500 uppercase tracking-wider text-xs`, rows `hover:bg-slate-50 transition-colors`, action links `text-indigo-600 hover:text-indigo-800` |

### Phase 3: Upload Template (upload.html)

**File:** `wealth_dashboard/templates/upload.html`

| Change | Detail |
|--------|--------|
| Drop zone | Dashed border `border-2 border-dashed border-slate-300 rounded-xl`, hover state `border-indigo-500 bg-indigo-50` |
| File list | White cards, `rounded-lg`, `border border-slate-200`, file icons in colored circles |
| Progress indicators | Indigo progress bar, `rounded-full` |

### Phase 4: Settings Template (settings.html)

**File:** `wealth_dashboard/templates/settings.html`

| Change | Detail |
|--------|--------|
| Form inputs | `rounded-lg`, `border border-slate-300`, focus ring `focus:ring-2 focus:ring-indigo-500 focus:border-transparent` |
| Tags/chips | `bg-white px-3 py-1.5 rounded border border-slate-200 shadow-sm text-sm text-slate-700` with delete icon |
| Save button | `bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700` |

---

## Color Mapping: Before → After

| Current (Bootstrap) | New (IntelliInvoice) | Visual Impact |
|---------------------|----------------------|---------------|
| `bg-primary` (blue) | White card + indigo icon | Softer, more professional |
| `bg-success` (green) | White card + emerald icon | Consistent with status badges |
| `bg-warning` (yellow) | White card + amber icon | Easier on eyes |
| `bg-danger` (red) | White card + red icon | Less alarming for risk display |
| `navbar-dark bg-dark` | `bg-slate-900` sidebar | Deeper, more refined dark |
| `btn btn-primary` (blue) | `bg-indigo-600` | Warmer, more distinctive brand |
| Plotly default colors | `#4f46e5, #10b981, #f59e0b, #ef4444, #8b5cf6, #ec4899` | Brand-consistent charts |

---

## Files to Modify

| File | Action | Effort |
|------|--------|--------|
| `wealth_dashboard/templates/base.html` | Rewrite: Bootstrap → Tailwind, add sidebar | High |
| `wealth_dashboard/templates/dashboard.html` | Rewrite: Bootstrap cards → Tailwind cards, update Plotly colors | Medium |
| `wealth_dashboard/templates/upload.html` | Rewrite: Bootstrap components → Tailwind | Medium |
| `wealth_dashboard/templates/settings.html` | Rewrite: Bootstrap forms → Tailwind | Medium |
| `wealth_dashboard/static/style.css` | Update: scrollbar styles, any custom overrides | Low |

**Estimated total effort:** 3–4 hours for complete migration with testing.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tailwind CSS via PyPI may differ from CDN Tailwind | Test with existing project setup; use same Tailwind version as IntelliInvoice |
| Plotly.js color overrides may conflict with Tailwind | Set Plotly `layout.colorway` explicitly to match palette |
| Bootstrap JavaScript dependencies (modals, dropdowns) | Replace with Tailwind + vanilla JS or lightweight library |
| Responsive behavior changes | Test mobile breakpoints; Tailwind grid may need adjustment |

---

## Approval Required

Before proceeding, please confirm:
1. **Proceed with this migration plan?** (yes/no)
2. **Any specific components you want to prioritize?** (sidebar, charts, forms, etc.)
3. **Keep Plotly.js for charts, or switch to another library?** (Recharts like IntelliInvoice, or keep Plotly)
4. **Any colors or design elements from the current UI you want to preserve?**
