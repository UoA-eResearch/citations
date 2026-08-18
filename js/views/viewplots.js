// Plots view — Plotly analytics dashboard over the loaded dataset.

import { ACCENT, ACCENT2, PLOTLY_DARK, OTHER_COLOR, escapeHTML } from "../config.js";
import { summarize } from "../graphdata.js";

export const PLOT_IDS = [
    "papers_per_year", "citations_per_year", "top_authors", "top_journals",
    "top_topics", "top_fields", "oa_status", "work_types",
];

const CONFIG = { displayModeBar: false, responsive: true };

function layout(title, extra = {}) {
    return {
        title: { text: title, font: { size: 14, color: "#ffffff" } },
        height: 320,
        margin: { l: 160, r: 20, t: 44, b: 40 },
        bargap: 0.25,
        ...structuredClone(PLOTLY_DARK),
        ...extra,
    };
}

function hbar(el, title, entries, { color = ACCENT, colorOf = null, value = e => e.works, hover = "%{x} works" } = {}) {
    const data = entries.slice().reverse(); // Plotly draws first item at the bottom
    Plotly.react(el, [{
        type: "bar",
        orientation: "h",
        y: data.map(e => e.name.length > 32 ? e.name.slice(0, 30) + "…" : e.name),
        x: data.map(value),
        marker: { color: colorOf ? data.map(colorOf) : color },
        hovertemplate: "%{y}<br>" + hover + "<extra></extra>",
    }], layout(title, { margin: { l: 190, r: 20, t: 44, b: 40 } }), CONFIG);
}

function vbar(el, title, byYear, { color = ACCENT, hover = "%{y}" } = {}) {
    const years = Object.keys(byYear).map(Number).sort((a, b) => a - b);
    Plotly.react(el, [{
        type: "bar",
        x: years,
        y: years.map(y => byYear[y]),
        marker: { color },
        hovertemplate: "%{x}<br>" + hover + "<extra></extra>",
    }], layout(title, { margin: { l: 60, r: 20, t: 44, b: 40 } }), CONFIG);
}

export function createViewPlots(container) {
    let built = false;

    function scaffold() {
        if (built) return;
        container.innerHTML = PLOT_IDS.map(id =>
            `<div class="plot-card" id="card-${escapeHTML(id)}"><div id="plot-${escapeHTML(id)}"></div></div>`).join("");
        built = true;
    }

    return {
        update({ works, fieldScale }) {
            scaffold();
            const s = summarize(works);
            const plot = id => document.getElementById("plot-" + id);

            vbar(plot("papers_per_year"), "Works per year", s.perYear, { hover: "%{y} works" });
            vbar(plot("citations_per_year"), "Citations by publication year", s.citPerYear,
                { color: ACCENT2, hover: "%{y} citations" });
            hbar(plot("top_authors"), "Top authors (by works in dataset)", s.topAuthors);
            hbar(plot("top_journals"), "Top journals / venues", s.topVenues);
            hbar(plot("top_topics"), "Top topics", s.topTopics);
            hbar(plot("top_fields"), "Fields", s.topFields, {
                colorOf: fieldScale ? e => fieldScale.color(e.name) : () => OTHER_COLOR,
            });
            hbar(plot("oa_status"), "Open access status",
                Object.entries(s.oaCounts).map(([name, works]) => ({ name, works })).sort((a, b) => b.works - a.works));
            hbar(plot("work_types"), "Work types",
                Object.entries(s.typeCounts).map(([name, works]) => ({ name, works })).sort((a, b) => b.works - a.works));
        },
        highlight(plotId) {
            for (const card of container.querySelectorAll(".plot-card")) card.classList.remove("highlighted");
            const card = document.getElementById("card-" + plotId);
            if (card) {
                card.classList.add("highlighted");
                card.scrollIntoView({ behavior: "smooth", block: "center" });
                setTimeout(() => card.classList.remove("highlighted"), 4000);
            }
        },
        resize() {
            for (const card of container.querySelectorAll(".plot-card > div")) Plotly.Plots.resize(card);
        },
        restyle() { /* plots restyle on update */ },
    };
}
