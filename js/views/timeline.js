// Bottom timeline strip — works per year; box-select filters the network by year range.

import { ACCENT, ACCENT2, PLOTLY_DARK } from "../config.js";

export function createTimeline(el, { onRange }) {
    let years = [];

    function colors(range) {
        if (!range) return years.map(() => ACCENT);
        return years.map(y => (y >= range[0] && y <= range[1]) ? ACCENT2 : ACCENT);
    }

    function bind() {
        el.on("plotly_selected", ev => {
            if (!ev || !ev.range) return;
            const [lo, hi] = ev.range.x;
            const range = [Math.ceil(lo), Math.floor(hi)];
            if (range[0] > range[1]) return;
            Plotly.restyle(el, { "marker.color": [colors(range)] });
            onRange(range);
        });
        el.on("plotly_deselect", () => {
            Plotly.restyle(el, { "marker.color": [colors(null)] });
            onRange(null);
        });
        el.on("plotly_doubleclick", () => {
            Plotly.restyle(el, { "marker.color": [colors(null)] });
            onRange(null);
        });
    }

    let bound = false;

    return {
        update(perYear) {
            years = Object.keys(perYear).map(Number).sort((a, b) => a - b);
            const data = [{
                type: "bar",
                x: years,
                y: years.map(y => perYear[y]),
                marker: { color: colors(null) },
                hovertemplate: "%{x}: %{y} works<extra></extra>",
            }];
            const layout = {
                height: 130,
                width: Math.min(640, Math.max(360, window.innerWidth - 560)),
                margin: { l: 34, r: 10, t: 8, b: 24 },
                dragmode: "select",
                selectdirection: "h",
                ...structuredClone(PLOTLY_DARK),
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
            };
            Plotly.react(el, data, layout, { displayModeBar: false });
            if (!bound) {
                bind();
                bound = true;
            }
        },
    };
}
