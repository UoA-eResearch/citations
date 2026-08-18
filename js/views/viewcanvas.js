// Dynamic canvas view — task-adaptive multi-axis 3D scatter of the loaded works.
// Instead of a node-link graph, each axis carries a contextual dimension (time,
// ontology-ordered topics, geography, venue, impact) and reconfigures per task,
// either from the axis pickers or from the AI assistant.

import { PLOTLY_DARK, escapeHTML, fmt } from "../config.js";

function trunc(s, n) {
    s = String(s ?? "");
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

// Each dimension maps a work to an axis value. Categorical dimensions with a
// `path` are ordered by their ontology path (OpenAlex domain > field > subfield
// > topic), so semantically related categories sit next to each other.
export const DIMENSIONS = {
    year: { label: "Time (year)", numeric: w => w.publication_year, jitter: 0.25 },
    citations: { label: "Citations", numeric: w => Math.log10((w.cited_by_count || 0) + 1), logTicks: true },
    fwci: { label: "Field-weighted impact", numeric: w => w.fwci ?? 0 },
    topic: { label: "Topic (ontology order)", cat: w => w.topic, path: w => [w.domain, w.field, w.subfield, w.topic] },
    subfield: { label: "Subfield (ontology order)", cat: w => w.subfield, path: w => [w.domain, w.field, w.subfield] },
    field: { label: "Field (ontology order)", cat: w => w.field, path: w => [w.domain, w.field] },
    country: { label: "Country", cat: w => w.country || "Unknown" },
    venue: { label: "Journal / venue", cat: w => w.venue || "Unknown" },
    none: { label: "— (flat)", numeric: () => 0, flat: true },
};

// Task presets — the "known tasks" the canvas adapts to.
export const TASKS = {
    ideation: { label: "Ideation over time", x: "year", y: "topic", z: "citations" },
    geography: { label: "Geographic story", x: "year", y: "country", z: "topic" },
    impact: { label: "Impact landscape", x: "year", y: "venue", z: "citations" },
    semantic: { label: "Semantic map", x: "field", y: "topic", z: "year" },
};

const MAX_CATEGORIES = 30;

function buildAxis(works, dimKey) {
    const dim = DIMENSIONS[dimKey] || DIMENSIONS.none;
    const layout = {
        title: { text: dim.label, font: { size: 12 } },
        gridcolor: "#2c2c2a",
        zerolinecolor: "#383835",
        color: "#c3c2b7",
        showbackground: false,
    };
    if (dim.flat) {
        return { values: works.map(() => 0), layout: { ...layout, visible: false } };
    }
    if (dim.numeric) {
        if (dim.logTicks) {
            layout.tickvals = [0, 1, 2, 3, 4, 5];
            layout.ticktext = ["0", "10", "100", "1k", "10k", "100k"];
        }
        const j = dim.jitter || 0;
        return {
            values: works.map(w => (dim.numeric(w) ?? 0) + (j ? (Math.random() - 0.5) * 2 * j : 0)),
            layout,
        };
    }
    // Categorical: top-N by count, ontology-ordered when a hierarchy path exists.
    const counts = new Map();
    const paths = new Map();
    for (const w of works) {
        const v = dim.cat(w);
        counts.set(v, (counts.get(v) || 0) + 1);
        if (dim.path && !paths.has(v)) paths.set(v, dim.path(w).join(" / "));
    }
    const cats = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, MAX_CATEGORIES).map(([v]) => v);
    if (dim.path) cats.sort((a, b) => (paths.get(a) || "").localeCompare(paths.get(b) || ""));
    const hasOther = counts.size > cats.length;
    const idx = new Map(cats.map((c, i) => [c, i]));
    const otherIdx = cats.length;
    layout.tickvals = [...cats.keys(), ...(hasOther ? [otherIdx] : [])];
    layout.ticktext = [...cats.map(c => trunc(c, 24)), ...(hasOther ? ["Other"] : [])];
    layout.tickfont = { size: 9 };
    return {
        values: works.map(w => (idx.get(dim.cat(w)) ?? otherIdx) + (Math.random() - 0.5) * 0.7),
        layout,
    };
}

export function createViewCanvas(container, { onWorkClick }) {
    const axes = { ...TASKS.ideation };
    let currentWorks = [];
    let bound = false;
    let last = null; // {works, colorOf, sizeOf} for restyle-triggered re-renders

    function render() {
        if (!last) return;
        const { works, colorOf, sizeOf } = last;
        currentWorks = works;
        const ax = buildAxis(works, axes.x);
        const ay = buildAxis(works, axes.y);
        const az = buildAxis(works, axes.z);
        const trace = {
            type: "scatter3d",
            mode: "markers",
            x: ax.values,
            y: ay.values,
            z: az.values,
            customdata: works.map((_, i) => i),
            text: works.map(w =>
                `<b>${escapeHTML(trunc(w.title, 70))}</b> (${w.publication_year ?? "?"})<br>` +
                `${escapeHTML(trunc(w.venue || "", 50))}<br>${escapeHTML(w.topic)} · ${escapeHTML(w.country || "")}` +
                `<br>Citations: ${fmt(w.cited_by_count)}`),
            hovertemplate: "%{text}<extra></extra>",
            marker: {
                color: works.map(colorOf),
                size: works.map(w => 1.5 + sizeOf(w) * 0.9),
                opacity: 0.85,
                line: { width: 0 },
            },
        };
        const layout = {
            width: container.clientWidth,
            height: container.clientHeight,
            margin: { l: 0, r: 0, t: 0, b: 0 },
            paper_bgcolor: "#0d0d0d",
            font: PLOTLY_DARK.font,
            uirevision: `${axes.x}|${axes.y}|${axes.z}`, // keep the camera unless the axes change
            scene: {
                xaxis: ax.layout,
                yaxis: ay.layout,
                zaxis: az.layout,
                bgcolor: "#0d0d0d",
                aspectmode: "cube",
                camera: { eye: { x: 1.7, y: 1.4, z: 0.8 } },
            },
        };
        Plotly.react(container, [trace], layout, { displayModeBar: false });
        if (!bound) {
            container.on("plotly_click", ev => {
                const i = ev.points?.[0]?.customdata;
                if (i !== undefined && currentWorks[i]) onWorkClick(currentWorks[i]);
            });
            bound = true;
        }
    }

    return {
        update({ works, colorOf, sizeOf }) {
            last = { works, colorOf, sizeOf };
            render();
        },
        restyle({ colorOf, sizeOf }) {
            if (!last) return;
            last = { ...last, colorOf, sizeOf };
            render();
        },
        setAxes(next) {
            for (const a of ["x", "y", "z"]) {
                if (next[a] && DIMENSIONS[next[a]]) axes[a] = next[a];
            }
        },
        getAxes() {
            return { ...axes };
        },
        resize() {
            if (last) render();
        },
    };
}
