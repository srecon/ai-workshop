# OpenSpec: Dashboard Modernization

**Status:** Draft — awaiting review
**Scope:** `wealth_dashboard/templates/dashboard.html`, `base.html`, `charts.py`
**Created:** 2026-10-25

---

## 1. Problem Statement

Despite recent glass-morphism improvements, the dashboard retains legacy design inconsistencies:

- **Bright primary colours** (pure green `#10b981`, red `#ef4444`, yellow `#f59e0b`) clash with the dark gradient background
- **Harsh inner borders** on cards create visual noise against translucent glass surfaces
- **Inconsistent spacing** between grid rows/columns causes visual rhythm breaks
- **Charts overflow** containers due to unconstrained Plotly dimensions and white backgrounds
- **Generic typography** lacks clear hierarchy — labels compete with metric values

---

## 2. Goals

| # | Goal | Measurable Outcome |
|---|------|--------------------|
| G1 | Cohesive muted colour palette | Zero pure RGB `(0,255,0)` / `(255,0,0)` / `(255,255,0)` in UI |
| G2 | Refined card design | All cards ≥ `p-8`, `rounded-2xl`, zero `border-slate-xxx` on card wrappers |
| G3 | Clear typographic hierarchy | Metric values ≥ `text-3xl`, labels ≤ `text-xs`, ratio ≥ 3:1 |
| G4 | Uniform layout alignment | Grid gaps consistent (`gap-6`), outer padding uniform (`p-6 lg:p-10`) |
| G5 | Clean chart rendering | Zero chart overflow, invisible grid lines, inline legends |

---

## 3. Design Tokens

### 3.1 Colour Palette (Muted / Sophisticated)

| Role | Old | New | Rationale |
|------|-----|-----|-----------|
| **Success** | `#10b981` (emerald-500) | `#34d399` (emerald-400, softened) | Less neon on dark bg |
| **Warning** | `#f59e0b` (amber-500) | `#fbbf24` (amber-400, desaturated) | Warmer, gentler |
| **Danger** | `#ef4444` (red-500) | `#fb7185` (rose-400, muted) | Softer alert tone |
| **Info** | `#3b82f6` (blue-500) | `#60a5fa` (blue-400) | Lighter on dark bg |
| **Neutral** | `#64748b` (slate-500) | `#94a3b8` (slate-400) | Higher visibility on glass |
| **Text primary** | `#0f172a` (slate-900) | `#1e293b` (slate-800) | Slightly lifted |
| **Text secondary** | `#475569` (slate-600) | `#64748b` (slate-500) | Lower contrast on glass |

**Trade-off:** Desaturating reduces vibrancy but improves harmony on dark gradient backgrounds. Brightness can be restored selectively on interactive elements (hover states).

### 3.2 Spacing System

| Element | Padding | Gap | Radius | Shadow |
|---------|---------|-----|--------|--------|
| **Outer wrapper** | `p-6 lg:p-10` | — | — | — |
| **Cards** | `p-8` (was `p-6`) | — | `rounded-2xl` (16px) | `shadow-lg` |
| **Grid rows** | — | `gap-6` (was `gap-4` for metrics) | — | — |
| **Inner content** | `gap-4` | — | — | — |

**Trade-off:** Larger padding increases vertical scrolling distance on compact screens but significantly improves breathing room and perceived quality. Mobile-first breakpoint at `lg:` preserves compact layouts on phones.

### 3.3 Typography Scale

| Element | Font Size | Weight | Colour | Line Height |
|---------|-----------|--------|--------|-------------|
| **Page heading** | `text-2xl` (24px) | `semibold` | `slate-800` | `leading-snug` |
| **Section title** | `text-lg` (18px) | `semibold` | `slate-700` | `leading-relaxed` |
| **Metric value** | `text-3xl` (30px) | `extrabold` | `slate-900` | `leading-tight` |
| **Label** | `text-xs` (12px) | `medium` | `slate-500` | `tracking-wide` |
| **Body text** | `text-sm` (14px) | `normal` | `slate-600` | `relaxed` |

**Trade-off:** Increasing metric values to `text-3xl` creates a 2.5:1 ratio over labels (vs current 1.5:1). This draws the eye faster to key numbers but may crowd tight spaces on mobile (< 640px).

---

## 4. Detailed Changes

### 4.1 Colour Palette Migration

**Files affected:** `dashboard.html`, `base.html`

| Change | Before | After |
|--------|--------|-------|
| Success indicator | `text-emerald-600` / `bg-emerald-500` | `text-emerald-500` / `bg-emerald-500/80` (opacity reduced) |
| Warning indicator | `text-amber-600` / `bg-amber-500` | `text-amber-500` / `bg-amber-500/80` |
| Danger indicator | `text-red-600` / `bg-red-500` | `text-rose-500` / `bg-rose-500/80` |
| Badge backgrounds | Solid `bg-emerald-500` | Frosted `bg-emerald-500/80` (translucent) |
| Alert boxes | `bg-red-50` / `bg-emerald-50` | `bg-rose-50/60` / `bg-emerald-50/60` (transparent) |

**Python-side (charts.py):** Update hardcoded hex codes in Plotly figure generation:
```python
COLOR_PALETTE = ['#4f46e5', '#34d399', '#fbbf24', '#fb7185', '#8b5cf6', '#ec4899']
```

### 4.2 Card Design Refinement

**Files affected:** `dashboard.html`

| Property | Before | After |
|----------|--------|-------|
| Padding | `p-6` | `p-8` (increased 33%) |
| Border-radius | `rounded-2xl` (16px) | `rounded-3xl` (24px) on hero cards, `rounded-2xl` (16px) on standard |
| Inner border | `border border-white/20` | **Removed** from card wrappers (kept on internal elements) |
| Shadow | `shadow-lg` | `shadow-xl` (softer, wider spread) |
| Background | `bg-white/70` | `bg-white/60` (more transparency for glass effect) |

**Specific targets:**
- Metric cards: Remove `border-white/20`, increase to `p-8`, upgrade to `rounded-3xl`
- Chart containers: Remove `border-white/20`, increase to `p-8`
- AI section: Remove `border-white/20`, increase to `p-8`
- Table card: Remove `border-white/20`, increase to `p-8`
- CTA banner: Upgrade to `rounded-3xl`, increase to `p-10`

### 4.3 Typography & Hierarchy

**Files affected:** `dashboard.html`, `base.html`

| Element | Before | After | Why |
|---------|--------|-------|-----|
| Metric values | `text-2xl` (20px) | `text-3xl` (24px) extrabold | 2× visual weight increase |
| Labels | `text-sm` (14px) | `text-[11px] uppercase tracking-[0.15em]` | Smaller, spaced-out labels |
| Section headings | `text-lg` (18px) semibold | `text-base` (14px) uppercase tracking-wider | Subdued, scannable |
| Currency symbols | Same as value | `text-slate-400` (dimmed) | Rub symbol recedes, number pops |

**CSS addition to `base.html`:**
```css
.metric-value {
    font-feature-settings: 'tnum'; /* Tabular nums for aligned numbers */
    letter-spacing: -0.02em;
}
.label-text {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
}
```

### 4.4 Layout Alignment

**Files affected:** `dashboard.html`

| Issue | Before | After |
|-------|--------|-------|
| Outer padding | `p-6 lg:p-8` | `p-6 lg:p-10` (wider on desktop) |
| Row gaps (metrics) | `gap-4` | `gap-5` (balanced between density and breath) |
| Row gaps (charts) | `gap-6` | `gap-8` (larger for chart breathing room) |
| Bottom spacing | `space-y-6` | `space-y-8` (stronger vertical rhythm) |
| Sidebar integration | Disconnected (sharp edge) | Subtle divider: `border-l border-white/5` on sidebar |

**Visual improvement:** Wider outer margins on desktop create a "floating island" effect — content centred with generous margins against the gradient background.

### 4.5 Chart Refinement

**Files affected:** `dashboard.html` (JavaScript), `charts.py` (Python)

#### 4.5.1 General Chart Improvements

| Property | Before | After |
|----------|--------|-------|
| Grid lines | Visible (gray) | Invisible (`showgrid: false`) |
| Axes | Visible (gray ticks) | Minimal (`showticklabels: true, showline: false`) |
| Legend | External, cluttered | Internal, condensed, no border |
| Margins | Default (large) | Compact (`t:15, r:15, b:35, l:35`) |
| Tooltip | Default (white box) | Custom styled (matches glass theme) |
| Mode bar | Hidden | Still hidden (correct) |

#### 4.5.2 Wealth Pyramid (Horizontal Bar Chart)

**Issues:** Bars overflow container vertically; labels wrap awkwardly.

**Changes:**
```javascript
{
    orientation: 'h',
    marker: {
        radius: { cornerRadius: 6 }, // Rounded bar tips
        color: chartColors
    },
    bargap: 0.3, // Space between bars
    textposition: 'outside',
    textfont: { size: 10, color: '#94a3b8' },
    showgrid: false, // Remove horizontal grid lines
    margin: { t: 10, r: 30, b: 30, l: 50 }
}
```

#### 4.5.3 Asset Allocation (Pie Chart)

**Issues:** Slice labels overlap; legend duplicates info.

**Changes:**
```javascript
{
    hole: 0.45, // Doughnut style (modern)
    textinfo: 'label+percent',
    textfont: { size: 11, color: '#1e293b' },
    labeldistance: 1.1,
    pull: [0.03], // Pull largest slice slightly outward
    showlegend: false, // Hide external legend (labels on slices)
    hovertemplate: '%{label}: %{value}<br>%{percentOfTotal}',
    customdata: formattedLabels
}
```

#### 4.5.4 Gauges (Net Worth, Risk)

**Issues:** Needle overlaps tick labels; scale unreadable.

**Changes:**
```javascript
{
    needle: {
        color: '#4f46e5',
        owncolor: true,
        length: 0.75,
        width: 4
    },
    axis: {
        visible: false, // Hide circular axis line
        range: [0, 10],
        tickfont: { size: 9, color: '#94a3b8' }
    },
    bgcolor: 'rgba(0,0,0,0)',
    domain: { x: [0.1, 0.9], y: [0.2, 0.8] }
}
```

#### 4.5.5 Cashflow (Line/Area Chart)

**Issues:** White background obscures gradient; thick lines dominate.

**Changes:**
```javascript
{
    fill: 'tozeroy', // Area fill under line
    fillcolor: 'rgba(79, 70, 229, 0.15)', // Faint indigo fill
    line: { width: 2.5, color: '#4f46e5' },
    markers: { size: 5, color: '#4f46e5', fillcolor: 'white' },
    hovertemplate: '%{y|rub}<extra></extra>', // Custom tooltip (no extra box)
    showgrid: false,
    xaxis: {
        tickfont: { size: 10, color: '#94a3b8' },
        gridcolor: 'rgba(255,255,255,0.05)' // Near-invisible grid
    }
}
```

---

## 5. Files Modified

| File | Lines Est. | Type |
|------|-----------|------|
| `wealth_dashboard/templates/dashboard.html` | ~340 → ~380 | HTML/Tailwind/JS |
| `wealth_dashboard/templates/base.html` | ~114 → ~130 | HTML/CSS |
| `wealth_dashboard/charts.py` | ~200 → ~250 | Python (colour constants, chart configs) |

**Total estimated change:** ~100 lines across 3 files.

---

## 6. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Reduced contrast on dark bg | Medium | Medium | Run WCAG AA checker; bump saturation if needed |
| Larger cards push content below fold | Low | Low | `lg:` breakpoint scales padding back on mobile |
| Chart.py changes break existing tests | Medium | High | Update test fixtures with new colour constants |
| Rounded bar tips unsupported in old Plotly | Low | Low | Pin Plotly ≥ 2.8 (already using 3.0.1) |

---

## 7. Acceptance Criteria

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| AC1 | Zero bright primary colours in DOM | Regex scan: no `rgb\(0,\s*255,\s*0\)` etc. |
| AC2 | All cards padded ≥ `p-8`, radius ≥ `rounded-2xl` | Manual audit of `dashboard.html` |
| AC3 | Metric-to-label size ratio ≥ 2:1 | Inspect computed styles in DevTools |
| AC4 | Grid gaps uniform (metrics `gap-5`, charts `gap-8`) | Visual inspection |
| AC5 | Zero chart overflow in any container | Resize browser; verify no clipping |
| AC6 | All charts use indigo/emerald/amber/rose palette | Trace `marker.colour` values in JS |
| AC7 | All existing tests pass | `pytest tests/` |
| AC8 | Page loads in < 2s on simulated 3G | Lighthouse audit |

---

## 8. Implementation Order (Phases)

| Phase | Scope | Effort | Depends On |
|-------|-------|--------|------------|
| **Phase 1** | Colour palette constants (Python + JS) | 30 min | None |
| **Phase 2** | Card refinement (padding, radius, shadow) | 45 min | Phase 1 |
| **Phase 3** | Typography scale + currency dimming | 30 min | Phase 2 |
| **Phase 4** | Layout alignment (spacing, sidebar divider) | 30 min | Phase 3 |
| **Phase 5** | Chart refinements (individual per-chart) | 2 hrs | Phase 4 |
| **Phase 6** | Testing + acceptance verification | 1 hr | Phase 5 |

**Total estimated effort:** ~4.5 hours.

---

## 9. Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| Author | AI Workshop Bot | Submitted | 2026-10-25 |
| Reviewer | _(awaiting)_ | Pending | — |
| Approver | _(awaiting)_ | Pending | — |

---

## Appendix A: Before/After Comparison Matrix

| Aspect | Current State | Target State | Delta |
|--------|--------------|--------------|-------|
| **Palette** | Pure RGB greens/reds/yellows | Muted emerald/rose/amber/blue | Harmonic coherence ↑ |
| **Card padding** | `p-6` (24px) | `p-8` (32px) | +33% breathing room |
| **Border radius** | `rounded-2xl` (16px) | `rounded-2xl/3xl` (16–24px) | Softer edges |
| **Inner borders** | `border-white/20` on every card | Removed from wrappers | Visual noise ↓ |
| **Shadow** | `shadow-lg` | `shadow-xl` | Depth ↑ |
| **Transparency** | `bg-white/70` | `bg-white/60` | Glass effect ↑ |
| **Metric size** | `text-2xl` (20px) | `text-3xl` (24px) | Visibility ↑ |
| **Label size** | `text-sm` (14px) | `text-[11px]` (11px) | Contrast ratio 2.2:1 |
| **Grid lines** | Visible gray | Invisible/near-invisible | Clarity ↑ |
| **Legend** | External, bordered | Inline/hide (labels on chart) | Space ↓ |
| **Bar tips** | Square | Rounded (radius 6px) | Polished ↑ |
| **Pie style** | Standard pie | Doughnut (hole 0.45) | Modern ↑ |
