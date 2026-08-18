// Map view — deck.gl (GPU) over a MapLibre basemap.
// Institutions as scaled points, co-authorship collaborations as arcs.

import { MAP_STYLE, fmt, escapeHTML } from "../config.js";
import { aggregateInstitutions } from "../graphdata.js";
import { fetchInstitutionGeo } from "../openalex.js";
import { toast } from "../ui.js";

const MAX_MAPPED_INSTITUTIONS = 400;
const MAX_ARCS = 300;

export function createViewMap(container) {
    let deckgl = null;
    let building = false;

    function ensure() {
        if (deckgl) return deckgl;
        deckgl = new deck.DeckGL({
            container,
            mapStyle: MAP_STYLE,
            initialViewState: { longitude: 20, latitude: 20, zoom: 1.4, pitch: 30 },
            controller: true,
            layers: [],
            getTooltip: ({ object }) => {
                if (!object) return null;
                const html = object.arc
                    ? `<b>${escapeHTML(object.aName)}</b> ↔ <b>${escapeHTML(object.bName)}</b><br>${fmt(object.count)} co-authored works`
                    : `<b>${escapeHTML(object.name)}</b><br>${escapeHTML(object.country || "")}<br>${fmt(object.works)} works · ${fmt(object.citations)} citations`;
                return {
                    html,
                    style: {
                        backgroundColor: "rgba(26,26,25,0.95)", color: "#c3c2b7",
                        border: "1px solid rgba(255,255,255,0.1)", borderRadius: "6px",
                        fontSize: "12px", padding: "8px 10px",
                    },
                };
            },
        });
        return deckgl;
    }

    return {
        async update({ works }) {
            if (building) return;
            building = true;
            try {
                const d = ensure();
                const { institutions, collabs } = aggregateInstitutions(works);
                const top = [...institutions.values()].sort((a, b) => b.works - a.works)
                    .slice(0, MAX_MAPPED_INSTITUTIONS);
                if (!top.length) {
                    d.setProps({ layers: [] });
                    toast("No institution affiliations in this dataset to map");
                    return;
                }
                const geo = await fetchInstitutionGeo(top.map(i => i.id));
                const points = top.filter(i => geo.has(i.id)).map(i => ({ ...i, ...geo.get(i.id) }));
                const located = new Set(points.map(p => p.id));
                const nameOf = new Map(points.map(p => [p.id, p.name]));
                const posOf = new Map(points.map(p => [p.id, [p.lng, p.lat]]));
                const arcs = collabs
                    .filter(c => located.has(c.a) && located.has(c.b))
                    .slice(0, MAX_ARCS)
                    .map(c => ({
                        arc: true, count: c.count,
                        aName: nameOf.get(c.a), bName: nameOf.get(c.b),
                        sourcePosition: posOf.get(c.a), targetPosition: posOf.get(c.b),
                    }));
                const maxWorks = Math.max(...points.map(p => p.works));
                d.setProps({
                    layers: [
                        new deck.ArcLayer({
                            id: "collabs",
                            data: arcs,
                            getSourcePosition: a => a.sourcePosition,
                            getTargetPosition: a => a.targetPosition,
                            getWidth: a => Math.max(1, Math.min(8, Math.sqrt(a.count))),
                            getSourceColor: [57, 135, 229, 160],
                            getTargetColor: [217, 89, 38, 160],
                            greatCircle: true,
                            pickable: true,
                        }),
                        new deck.ScatterplotLayer({
                            id: "institutions",
                            data: points,
                            getPosition: p => [p.lng, p.lat],
                            getRadius: p => 30000 + 250000 * Math.sqrt(p.works / maxWorks),
                            radiusMinPixels: 3,
                            radiusMaxPixels: 40,
                            getFillColor: [57, 135, 229, 200],
                            getLineColor: [255, 255, 255, 120],
                            lineWidthMinPixels: 1,
                            stroked: true,
                            pickable: true,
                        }),
                    ],
                });
            } catch (err) {
                console.error(err);
                toast("Map build failed: " + err.message, { error: true });
            } finally {
                building = false;
            }
        },
        resize() { /* deck.gl handles container resize */ },
        restyle() { /* map styling is fixed */ },
    };
}
