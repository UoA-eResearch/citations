// Shared constants and the colour palette (validated dark-surface steps).

export const MAILTO = "nick.young@auckland.ac.nz";
export const OPENALEX_BASE = "https://api.openalex.org";

// How many works to pull from the live API per entity (cursor-paginated, most cited first).
export const MAX_WORKS = 600;
// Cap on rendered edges for grouped views (kept by weight).
export const MAX_EDGES = 5000;

// Categorical palette — 8 slots, fixed order, validated for the dark surface.
export const CATEGORICAL = [
    "#3987e5", // blue
    "#d95926", // orange
    "#199e70", // aqua
    "#c98500", // yellow
    "#d55181", // magenta
    "#008300", // green
    "#9085e9", // violet
    "#e66767", // red
];
export const OTHER_COLOR = "#898781"; // muted — used for categories beyond the 8 slots

// Sequential blue ramp, ordered low → high for a dark canvas
// (dark steps recede toward the surface; light steps carry salience).
export const SEQUENTIAL = [
    "#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5", "#5598e7",
    "#6da7ec", "#86b6ef", "#9ec5f4", "#b7d3f6", "#cde2fb",
];

export const ACCENT = "#3987e5";
export const ACCENT2 = "#d95926";

// Plotly dark-theme layout tokens (chart chrome from the reference palette).
export const PLOTLY_DARK = {
    paper_bgcolor: "#1a1a19",
    plot_bgcolor: "#1a1a19",
    font: { color: "#c3c2b7", family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: 12 },
    xaxis: { gridcolor: "#2c2c2a", zerolinecolor: "#383835", linecolor: "#383835" },
    yaxis: { gridcolor: "#2c2c2a", zerolinecolor: "#383835", linecolor: "#383835" },
    colorway: CATEGORICAL,
};

export const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export function uniq(arr) {
    return [...new Set(arr)];
}

export function fmt(n) {
    return (n ?? 0).toLocaleString("en");
}

export function escapeHTML(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
}

// OpenAlex IDs arrive as full URLs ("https://openalex.org/W123") — shorten for API filters.
export function shortId(id) {
    return String(id ?? "").replace("https://openalex.org/", "");
}
