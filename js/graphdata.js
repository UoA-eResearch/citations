// Graph construction (grouping, edges), colour/size scales, and dataset summaries.

import { CATEGORICAL, OTHER_COLOR, SEQUENTIAL, MAX_EDGES, uniq } from "./config.js";

// ---------- grouping ----------

// For each grouping mode, return the [{id, name}] groups a work belongs to.
const GROUP_KEYS = {
    author: w => w.authorships.map(a => ({ id: a.author?.id, name: a.author?.display_name })),
    inst: w => {
        const seen = new Map();
        for (const a of w.authorships) {
            for (const i of a.institutions || []) if (i.id && !seen.has(i.id)) seen.set(i.id, i.display_name);
        }
        return [...seen].map(([id, name]) => ({ id, name }));
    },
    journal: w => w.primary_location?.source
        ? [{ id: w.primary_location.source.id, name: w.primary_location.source.display_name }] : [],
    topic: w => [{ id: "topic:" + w.topic, name: w.topic }],
    field: w => [{ id: "field:" + w.field, name: w.field }],
};

export function buildGraph(works, groupBy = "paper") {
    if (groupBy === "paper") return buildPaperGraph(works);
    return buildGroupedGraph(works, groupBy);
}

function buildPaperGraph(works) {
    const ids = new Set(works.map(w => w.id));
    const nodes = works.map(w => ({
        id: w.id,
        name: w.title,
        kind: "paper",
        work: w,
        cited_by_count: w.cited_by_count || 0,
        publication_year: w.publication_year,
        n_authors: w.n_authors,
        n_inst: w.n_inst,
        field: w.field,
    }));
    const links = [];
    for (const w of works) {
        for (const ref of w.referenced_works) {
            if (ids.has(ref) && ref !== w.id) links.push({ source: w.id, target: ref, weight: 1 });
        }
    }
    return { nodes, links };
}

function buildGroupedGraph(works, groupBy) {
    const getGroups = GROUP_KEYS[groupBy];
    const groups = new Map();       // id -> node
    const workGroups = new Map();   // work id -> [group ids]
    for (const w of works) {
        const gs = getGroups(w).filter(g => g.id);
        workGroups.set(w.id, gs.map(g => g.id));
        for (const g of gs) {
            let node = groups.get(g.id);
            if (!node) {
                node = {
                    id: g.id, name: g.name || "(unknown)", kind: groupBy,
                    n_works: 0, cited_by_count: 0,
                    first_year: w.publication_year, last_year: w.publication_year,
                    fields: {}, works: [],
                };
                groups.set(g.id, node);
            }
            node.n_works++;
            node.cited_by_count += w.cited_by_count || 0;
            node.works.push(w);
            if (w.publication_year) {
                if (!node.first_year || w.publication_year < node.first_year) node.first_year = w.publication_year;
                if (!node.last_year || w.publication_year > node.last_year) node.last_year = w.publication_year;
            }
            node.fields[w.field] = (node.fields[w.field] || 0) + 1;
        }
    }
    for (const node of groups.values()) {
        node.field = Object.entries(node.fields).sort((a, b) => b[1] - a[1])[0]?.[0] || "Unknown";
        node.publication_year = node.first_year;
        node.n_authors = node.n_works; // aliases so shared colour/size options keep working
        node.n_inst = node.n_works;
    }
    // Edge A→B when a work in group A cites a work in group B (within the dataset).
    const edgeWeights = new Map();
    const inSet = new Map(works.map(w => [w.id, w]));
    for (const w of works) {
        const sources = workGroups.get(w.id) || [];
        for (const ref of w.referenced_works) {
            if (!inSet.has(ref)) continue;
            const targets = workGroups.get(ref) || [];
            for (const s of sources) {
                for (const t of targets) {
                    if (s === t) continue;
                    const key = s + "\t" + t;
                    edgeWeights.set(key, (edgeWeights.get(key) || 0) + 1);
                }
            }
        }
    }
    let links = [...edgeWeights].map(([key, weight]) => {
        const [source, target] = key.split("\t");
        return { source, target, weight };
    });
    if (links.length > MAX_EDGES) {
        links.sort((a, b) => b.weight - a.weight);
        links = links.slice(0, MAX_EDGES);
    }
    return { nodes: [...groups.values()], links };
}

// ---------- scales ----------

function quantileBreaks(values, n) {
    const sorted = uniq(values).filter(v => v != null && isFinite(v)).sort((a, b) => a - b);
    if (!sorted.length) return [0];
    const breaks = [];
    for (let i = 0; i <= n; i++) breaks.push(sorted[Math.min(sorted.length - 1, Math.floor((i / n) * (sorted.length - 1)))]);
    return breaks;
}

// Sequential (single-hue) scale for numeric attributes, quantile-binned into the ramp.
export function makeNumericScale(values) {
    const breaks = quantileBreaks(values, SEQUENTIAL.length);
    const color = v => {
        if (v == null || !isFinite(v)) return OTHER_COLOR;
        for (let i = SEQUENTIAL.length - 1; i >= 0; i--) {
            if (v >= breaks[i]) return SEQUENTIAL[Math.min(i, SEQUENTIAL.length - 1)];
        }
        return SEQUENTIAL[0];
    };
    return {
        type: "numeric", color,
        min: breaks[0], max: breaks[breaks.length - 1],
        ramp: SEQUENTIAL,
    };
}

// Categorical scale: top-8 categories get the fixed palette slots, the rest fold to "Other".
export function makeCategoricalScale(values) {
    const counts = new Map();
    for (const v of values) counts.set(v, (counts.get(v) || 0) + 1);
    const ordered = [...counts].sort((a, b) => b[1] - a[1]).map(([v]) => v);
    const mapping = new Map();
    ordered.slice(0, CATEGORICAL.length).forEach((v, i) => mapping.set(v, CATEGORICAL[i]));
    const color = v => mapping.get(v) || OTHER_COLOR;
    const legend = ordered.slice(0, CATEGORICAL.length).map(v => ({ label: v, color: mapping.get(v) }));
    if (ordered.length > CATEGORICAL.length) legend.push({ label: "Other", color: OTHER_COLOR });
    return { type: "categorical", color, legend, mapping };
}

// ---------- summaries ----------

function topBy(items, keyFn, n = 15) {
    const counts = new Map();
    for (const item of items) {
        for (const key of keyFn(item)) {
            if (!key) continue;
            const e = counts.get(key) || { name: key, works: 0, citations: 0 };
            e.works++;
            e.citations += item.cited_by_count || 0;
            counts.set(key, e);
        }
    }
    return [...counts.values()].sort((a, b) => b.works - a.works).slice(0, n);
}

export function summarize(works) {
    const years = works.map(w => w.publication_year).filter(Boolean);
    const perYear = {};
    const citPerYear = {};
    for (const w of works) {
        const y = w.publication_year;
        if (!y) continue;
        perYear[y] = (perYear[y] || 0) + 1;
        citPerYear[y] = (citPerYear[y] || 0) + (w.cited_by_count || 0);
    }
    const oa = {};
    const types = {};
    for (const w of works) {
        oa[w.oa_status] = (oa[w.oa_status] || 0) + 1;
        types[w.type || "unknown"] = (types[w.type || "unknown"] || 0) + 1;
    }
    return {
        count: works.length,
        totalCitations: works.reduce((s, w) => s + (w.cited_by_count || 0), 0),
        yearMin: years.length ? Math.min(...years) : null,
        yearMax: years.length ? Math.max(...years) : null,
        perYear, citPerYear,
        topAuthors: topBy(works, w => w.authorships.map(a => a.author?.display_name)),
        topInstitutions: topBy(works, w => w.institution_names),
        topVenues: topBy(works, w => [w.venue]),
        topTopics: topBy(works, w => [w.topic]),
        topFields: topBy(works, w => [w.field]),
        mostCited: [...works].sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0)).slice(0, 10)
            .map(w => ({ id: w.id, title: w.title, year: w.publication_year, citations: w.cited_by_count })),
        oaCounts: oa,
        typeCounts: types,
    };
}

// Institution aggregation for the map view: id -> {name, works, citations, collabs}.
export function aggregateInstitutions(works) {
    const insts = new Map();
    const pairs = new Map();
    for (const w of works) {
        const ids = new Map();
        for (const a of w.authorships) {
            for (const i of a.institutions || []) if (i.id) ids.set(i.id, i.display_name);
        }
        for (const [id, name] of ids) {
            const e = insts.get(id) || { id, name, works: 0, citations: 0 };
            e.works++;
            e.citations += w.cited_by_count || 0;
            insts.set(id, e);
        }
        const list = [...ids.keys()].sort();
        for (let i = 0; i < list.length; i++) {
            for (let j = i + 1; j < list.length; j++) {
                const key = list[i] + "\t" + list[j];
                pairs.set(key, (pairs.get(key) || 0) + 1);
            }
        }
    }
    const collabs = [...pairs].map(([key, count]) => {
        const [a, b] = key.split("\t");
        return { a, b, count };
    }).sort((x, y) => y.count - x.count);
    return { institutions: insts, collabs };
}
