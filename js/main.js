// App bootstrap: wires state, views, search, controls, modal, timeline and the AI assistant.

import { fmt, escapeHTML, shortId } from "./config.js";
import * as openalex from "./openalex.js";
import { buildGraph, makeNumericScale, makeCategoricalScale, summarize } from "./graphdata.js";
import { state, on, setWorks, setView, setYearRange, setDisplay, filteredWorks } from "./state.js";
import * as ui from "./ui.js";
import { createCosmosView } from "./views/cosmosview.js";
import { createViewMap } from "./views/viewmap.js";
import { createViewPlots, PLOT_IDS } from "./views/viewplots.js";
import { createViewCanvas, DIMENSIONS as CANVAS_DIMS, TASKS as CANVAS_TASKS } from "./views/viewcanvas.js";
import { createTimeline } from "./views/timeline.js";
import { initAI } from "./ai.js";

const $ = id => document.getElementById(id);

const COLOR_LABELS = {
    cited_by_count: "Citations",
    publication_year: "Year",
    n_authors: "Authors",
    n_inst: "Institutions",
    field: "Field",
};

// ---------- views ----------

const views = {
    "3d": createCosmosView($("view-3d"), { dimensions: 3, onNodeClick: onNodeClick }),
    "2d": createCosmosView($("view-2d"), { dimensions: 2, onNodeClick: onNodeClick }),
    map: createViewMap($("view-map")),
    canvas: createViewCanvas($("view-canvas"), { onWorkClick: w => showWorkModal(w) }),
    plots: createViewPlots($("plots-grid")),
};
const dirty = { "3d": true, "2d": true, map: true, canvas: true, plots: true };

let graphCache = null; // {nodes, links} for current works+filter+groupBy

function getGraph() {
    if (!graphCache) graphCache = buildGraph(filteredWorks(), state.groupBy);
    return graphCache;
}

function getFieldScale(works) {
    return makeCategoricalScale(works.map(w => w.field));
}

function styleAccessors(nodes, works) {
    let scale, colorOf;
    if (state.colorBy === "field") {
        scale = getFieldScale(works);
        colorOf = n => scale.color(n.field);
    } else {
        scale = makeNumericScale(nodes.map(n => n[state.colorBy]));
        colorOf = n => scale.color(n[state.colorBy]);
    }
    let sizeOf;
    if (!state.sizeBy) {
        sizeOf = () => 3;
    } else {
        const max = Math.max(1, ...nodes.map(n => n[state.sizeBy] || 0));
        sizeOf = n => 2.5 + 9 * Math.sqrt((n[state.sizeBy] || 0) / max);
    }
    return { scale, colorOf, sizeOf };
}

async function updateView(name) {
    const works = filteredWorks();
    if (name === "map") {
        await views.map.update({ works });
    } else if (name === "plots") {
        views.plots.update({ works, fieldScale: getFieldScale(works) });
    } else if (name === "canvas") {
        const { scale, colorOf, sizeOf } = styleAccessors(works, works);
        ui.renderLegend(scale, COLOR_LABELS[state.colorBy]);
        views.canvas.update({ works, colorOf, sizeOf });
    } else {
        const { nodes, links } = getGraph();
        const { scale, colorOf, sizeOf } = styleAccessors(nodes, works);
        ui.renderLegend(scale, COLOR_LABELS[state.colorBy]);
        await views[name].update({ nodes, links, colorOf, sizeOf, weighted: state.groupBy !== "paper" });
    }
    dirty[name] = false;
}

function markAllDirty() {
    graphCache = null;
    for (const k of Object.keys(dirty)) dirty[k] = true;
}

async function refresh({ rebuild = true } = {}) {
    if (rebuild) {
        markAllDirty();
        await updateView(state.view);
        return;
    }
    // Colour/size only. The canvas bakes colours into its markers, graph views restyle
    // in place; everything inactive rebuilds next time it is shown.
    for (const k of Object.keys(dirty)) if (k !== state.view) dirty[k] = true;
    if (state.view === "canvas") {
        await updateView("canvas");
    } else if (state.view === "3d" || state.view === "2d") {
        const { nodes } = getGraph();
        const { scale, colorOf, sizeOf } = styleAccessors(nodes, filteredWorks());
        ui.renderLegend(scale, COLOR_LABELS[state.colorBy]);
        views[state.view].restyle({ colorOf, sizeOf });
    }
}

// ---------- state events ----------

on("data", () => {
    const stats = summarize(state.works);
    ui.renderBanner(state.entity, stats);
    timeline.update(stats.perYear);
    markAllDirty();
    updateView(state.view);
});

on("filter", () => {
    markAllDirty();
    updateView(state.view);
});

on("view", () => {
    for (const [name, el] of Object.entries(viewEls)) el.classList.toggle("hidden", name !== state.view);
    for (const btn of document.querySelectorAll("#view-switcher button")) {
        btn.classList.toggle("active", btn.dataset.view === state.view);
    }
    const graphView = state.view === "3d" || state.view === "2d";
    const canvasView = state.view === "canvas";
    $("controls").classList.toggle("hidden", !(graphView || canvasView));
    $("group-label").classList.toggle("hidden", canvasView); // grouping doesn't apply to the canvas
    $("canvas-controls").classList.toggle("hidden", !canvasView);
    $("timeline-wrap").classList.toggle("hidden", !(graphView || canvasView));
    if (dirty[state.view]) updateView(state.view);
    views[state.view].resize?.();
});

// ---------- node interaction ----------

function onNodeClick(node) {
    ui.hideTooltip();
    if (node.kind === "paper") showWorkModal(node.work);
    else showGroupModal(node);
}

async function showWorkModal(work) {
    ui.showModal(`${escapeHTML(work.title)} (${work.publication_year ?? "?"})`, ui.workModalHTML(work));
    if (!work.abstract) {
        try {
            const full = await openalex.fetchWorkDetails(work.id);
            work.abstract = full.abstract;
            if (!$("modal-backdrop").classList.contains("hidden") && work.abstract) {
                $("modal-body").innerHTML = ui.workModalHTML(work);
            }
        } catch { /* abstract is a nice-to-have */ }
    }
}

function showGroupModal(node) {
    ui.showModal(escapeHTML(node.name), ui.groupModalHTML(node));
}

$("modal-close").addEventListener("click", ui.hideModal);
$("modal-backdrop").addEventListener("click", e => {
    if (e.target === $("modal-backdrop")) ui.hideModal();
});

$("modal-body").addEventListener("click", async e => {
    const workRow = e.target.closest(".work-row");
    if (workRow) {
        const w = state.works.find(x => x.id === workRow.dataset.workId);
        if (w) showWorkModal(w);
        return;
    }
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const { action, id, name, type } = btn.dataset;
    if (action === "ego") {
        ui.hideModal();
        await loadEntity("work", id, name);
    } else if (action === "load-entity") {
        ui.hideModal();
        await loadEntity(type, id, name);
    } else if (action === "ask") {
        ui.hideModal();
        assistant.ask(`Tell me about "${name}" (${id})`);
    }
});

// ---------- data loading ----------

async function loadEntity(type, id, name, maxWorks) {
    ui.showLoading(`Loading works for ${name}…`);
    try {
        const works = await openalex.loadEntityWorks(type, id, {
            cap: maxWorks || undefined,
            onProgress: (n, total) => ui.loadingProgress(`Loading works for ${name}… ${fmt(n)}${total ? " / " + fmt(total) : ""}`),
        });
        if (!works.length) {
            ui.toast(`No works found for ${name}`, { error: true });
            return null;
        }
        openalex.normalizeWorks(works);
        setWorks(works, { type, id, name });
        ui.toast(`Loaded ${fmt(works.length)} works for ${name}`);
        return summarize(works);
    } catch (err) {
        console.error(err);
        ui.toast(`Failed to load ${name}: ${err.message}`, { error: true });
        throw err;
    } finally {
        ui.hideLoading();
    }
}

async function loadLocalData(path, name) {
    ui.showLoading(`Loading ${name}…`);
    try {
        const res = await fetch(path);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const works = await res.json();
        openalex.normalizeWorks(works);
        setWorks(works, { type: "local", id: path, name });
    } catch (err) {
        console.error(err);
        ui.toast(`Failed to load ${path}: ${err.message}`, { error: true });
    } finally {
        ui.hideLoading();
    }
}

// ---------- search ----------

const SEARCHABLE = new Set(["work", "author", "institution", "source", "topic", "concept", "funder"]);

ui.initSearch(item => {
    if (!SEARCHABLE.has(item.entity_type)) {
        ui.toast(`Sorry — ${item.entity_type} networks aren't supported yet`, { error: true });
        return;
    }
    loadEntity(item.entity_type, item.id, item.display_name).catch(() => { });
});

// ---------- controls ----------

$("group").addEventListener("change", e => {
    setDisplay({ groupBy: e.target.value });
    refresh({ rebuild: true });
});
$("color").addEventListener("change", e => {
    setDisplay({ colorBy: e.target.value });
    refresh({ rebuild: false });
});
$("size").addEventListener("change", e => {
    setDisplay({ sizeBy: e.target.value });
    refresh({ rebuild: false });
});
$("controls-collapse").addEventListener("click", () => {
    const body = $("controls-body");
    body.classList.toggle("hidden");
    $("controls-collapse").textContent = body.classList.contains("hidden") ? "+" : "–";
});

const viewEls = {
    "3d": $("view-3d"),
    "2d": $("view-2d"),
    map: $("view-map"),
    canvas: $("view-canvas"),
    plots: $("view-plots"),
};

// ---------- canvas axis controls ----------

function syncCanvasSelects(taskId) {
    const axes = views.canvas.getAxes();
    for (const a of ["x", "y", "z"]) $(`canvas-${a}`).value = axes[a];
    if (taskId) {
        $("canvas-task").value = taskId;
    } else {
        const match = Object.entries(CANVAS_TASKS)
            .find(([, t]) => t.x === axes.x && t.y === axes.y && t.z === axes.z);
        $("canvas-task").value = match ? match[0] : "custom";
    }
}

(function initCanvasControls() {
    $("canvas-task").innerHTML =
        Object.entries(CANVAS_TASKS).map(([id, t]) => `<option value="${id}">${t.label}</option>`).join("")
        + `<option value="custom">Custom</option>`;
    for (const a of ["x", "y", "z"]) {
        $(`canvas-${a}`).innerHTML =
            Object.entries(CANVAS_DIMS).map(([id, d]) => `<option value="${id}">${d.label}</option>`).join("");
    }
    syncCanvasSelects();
    $("canvas-task").addEventListener("change", e => {
        const t = CANVAS_TASKS[e.target.value];
        if (!t) return;
        views.canvas.setAxes(t);
        syncCanvasSelects(e.target.value);
        dirty.canvas = true;
        updateView("canvas");
    });
    for (const a of ["x", "y", "z"]) {
        $(`canvas-${a}`).addEventListener("change", e => {
            views.canvas.setAxes({ [a]: e.target.value });
            syncCanvasSelects();
            dirty.canvas = true;
            updateView("canvas");
        });
    }
})();

for (const btn of document.querySelectorAll("#view-switcher button")) {
    btn.addEventListener("click", () => setView(btn.dataset.view));
}

// ---------- timeline ----------

const timeline = createTimeline($("timeline"), {
    onRange: range => setYearRange(range),
});

window.addEventListener("resize", () => views[state.view].resize?.());

// ---------- AI assistant facade ----------

const assistant = initAI({
    async execute(name, input) {
        switch (name) {
            case "search_entities": {
                const results = await openalex.autocomplete(input.query);
                return results.slice(0, 8).map(r => ({
                    id: r.id, display_name: r.display_name, entity_type: r.entity_type,
                    hint: r.hint, works_count: r.works_count,
                }));
            }
            case "load_network": {
                const stats = await loadEntity(input.entity_type, input.id, input.name, input.max_works);
                if (!stats) return "No works found.";
                return {
                    loaded: input.name, works: stats.count, total_citations: stats.totalCitations,
                    years: [stats.yearMin, stats.yearMax],
                    top_authors: stats.topAuthors.slice(0, 5).map(a => a.name),
                    top_topics: stats.topTopics.slice(0, 5).map(t => t.name),
                };
            }
            case "set_view":
                setView(input.view);
                return `View is now ${input.view}.`;
            case "configure_graph": {
                const patch = {};
                if (input.group_by) {
                    patch.groupBy = input.group_by;
                    $("group").value = input.group_by;
                }
                if (input.color_by) {
                    patch.colorBy = input.color_by;
                    $("color").value = input.color_by;
                }
                if (input.size_by !== undefined) {
                    patch.sizeBy = input.size_by;
                    $("size").value = input.size_by;
                }
                setDisplay(patch);
                await refresh({ rebuild: !!input.group_by });
                return `Graph configured: ${JSON.stringify(patch)}.`;
            }
            case "filter_years": {
                const range = (input.start_year || input.end_year)
                    ? [input.start_year || 1500, input.end_year || 3000] : null;
                setYearRange(range);
                return range ? `Filtered to ${range[0]}–${range[1]} (${fmt(filteredWorks().length)} works shown).`
                    : "Year filter cleared.";
            }
            case "configure_canvas": {
                if (input.task && CANVAS_TASKS[input.task]) views.canvas.setAxes(CANVAS_TASKS[input.task]);
                views.canvas.setAxes(input);
                syncCanvasSelects();
                dirty.canvas = true;
                if (state.view === "canvas") await updateView("canvas");
                else setView("canvas");
                const axes = views.canvas.getAxes();
                return `Canvas shown with X=${axes.x}, Y=${axes.y}, Z=${axes.z} `
                    + `(${fmt(filteredWorks().length)} works plotted).`;
            }
            case "get_abstracts":
                return openalex.fetchAbstracts(input.ids || []);
            case "show_plot":
                if (!PLOT_IDS.includes(input.plot)) throw new Error(`Unknown plot; valid: ${PLOT_IDS.join(", ")}`);
                setView("plots");
                if (dirty.plots) await updateView("plots");
                views.plots.highlight(input.plot);
                return `Showing the ${input.plot} chart.`;
            case "get_current_stats": {
                const stats = summarize(filteredWorks());
                return {
                    entity: state.entity, view: state.view,
                    group_by: state.groupBy, color_by: state.colorBy, size_by: state.sizeBy,
                    year_filter: state.yearRange,
                    works: stats.count, total_citations: stats.totalCitations,
                    years: [stats.yearMin, stats.yearMax],
                    top_authors: stats.topAuthors.slice(0, 10),
                    top_institutions: stats.topInstitutions.slice(0, 10),
                    top_venues: stats.topVenues.slice(0, 10),
                    top_topics: stats.topTopics.slice(0, 10),
                    most_cited: stats.mostCited,
                    oa_status: stats.oaCounts, work_types: stats.typeCounts,
                };
            }
            case "query_openalex":
                return openalex.rawQuery(input);
            case "get_work_details": {
                const w = await openalex.fetchWorkDetails(input.id);
                return {
                    id: w.id, doi: w.doi, title: w.title || w.display_name, year: w.publication_year,
                    type: w.type, venue: w.primary_location?.source?.display_name,
                    authors: (w.authorships || []).map(a => a.author?.display_name).filter(Boolean),
                    institutions: [...new Set((w.authorships || []).flatMap(a => (a.institutions || []).map(i => i.display_name)))],
                    topics: (w.topics || []).map(t => t.display_name),
                    cited_by_count: w.cited_by_count, fwci: w.fwci,
                    open_access: w.open_access?.oa_status, abstract: w.abstract,
                };
            }
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    },
});

// ---------- boot ----------

(function boot() {
    const params = new URLSearchParams(window.location.search);
    const data = params.get("data");
    const type = params.get("type");
    const id = params.get("id");
    if (type && id) {
        loadEntity(type, id, params.get("name") || shortId(id)).catch(() => { });
    } else if (data === "Decolonizing_Methodologies") {
        loadLocalData("Decolonizing_Methodologies/data.json", "Influence of Decolonizing Methodologies");
    } else if (data) {
        loadLocalData(`data/${data}.json`, data);
    } else {
        loadLocalData("data/Dan.json", "Daniel J. Exeter");
    }
})();
