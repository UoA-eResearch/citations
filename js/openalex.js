// OpenAlex API client — live data loading, normalization, and raw queries.

import { OPENALEX_BASE, MAILTO, MAX_WORKS, uniq, shortId } from "./config.js";

const WORK_FIELDS = [
    "id", "doi", "title", "display_name", "publication_year", "publication_date",
    "type", "cited_by_count", "fwci", "referenced_works", "authorships",
    "primary_location", "primary_topic", "topics", "open_access", "language",
].join(",");

async function getJSON(path, params = {}) {
    const url = new URL(OPENALEX_BASE + path);
    for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    }
    url.searchParams.set("mailto", MAILTO);
    const res = await fetch(url);
    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`OpenAlex ${res.status}: ${body.slice(0, 300) || res.statusText}`);
    }
    return res.json();
}

export async function autocomplete(q) {
    const data = await getJSON("/autocomplete", { q, author_hint: "institution" });
    return data.results || [];
}

// Cursor-paginate /works for a filter, most-cited first, up to `cap` works.
export async function fetchWorks(filter, { cap = MAX_WORKS, sort = "cited_by_count:desc", onProgress } = {}) {
    const works = [];
    let cursor = "*";
    while (works.length < cap && cursor) {
        const page = await getJSON("/works", {
            filter,
            sort,
            select: WORK_FIELDS,
            "per-page": Math.min(200, cap - works.length),
            cursor,
        });
        works.push(...page.results);
        cursor = page.meta.next_cursor;
        if (onProgress) onProgress(works.length, Math.min(cap, page.meta.count));
        if (!page.results.length) break;
    }
    return works;
}

export async function fetchWorksByIds(ids, { onProgress } = {}) {
    const works = [];
    for (let i = 0; i < ids.length; i += 50) {
        const chunk = ids.slice(i, i + 50).map(shortId);
        const page = await getJSON("/works", {
            filter: "ids.openalex:" + chunk.join("|"),
            select: WORK_FIELDS,
            "per-page": 50,
        });
        works.push(...page.results);
        if (onProgress) onProgress(works.length, ids.length);
    }
    return works;
}

// Batch-resolve institution locations for the map view. Returns Map(id -> {name, lat, lng, country}).
const instGeoCache = new Map();
export async function fetchInstitutionGeo(ids) {
    const missing = ids.filter(id => !instGeoCache.has(id));
    for (let i = 0; i < missing.length; i += 50) {
        const chunk = missing.slice(i, i + 50).map(shortId);
        const page = await getJSON("/institutions", {
            filter: "ids.openalex:" + chunk.join("|"),
            select: "id,display_name,geo",
            "per-page": 50,
        });
        for (const inst of page.results) {
            if (inst.geo && inst.geo.latitude != null) {
                instGeoCache.set(inst.id, {
                    name: inst.display_name,
                    lat: inst.geo.latitude,
                    lng: inst.geo.longitude,
                    country: inst.geo.country,
                });
            }
        }
    }
    const out = new Map();
    for (const id of ids) if (instGeoCache.has(id)) out.set(id, instGeoCache.get(id));
    return out;
}

const ENTITY_FILTERS = {
    author: id => `author.id:${id}`,
    institution: id => `institutions.id:${id}`,
    source: id => `primary_location.source.id:${id}`,
    topic: id => `primary_topic.id:${id}`,
    concept: id => `concepts.id:${id}`,
    funder: id => `grants.funder:${id}`,
};

// Load the citation network for an entity. For works: the paper + its references + citing papers.
export async function loadEntityWorks(entityType, id, { cap = MAX_WORKS, onProgress } = {}) {
    const sid = shortId(id);
    if (entityType === "work") {
        const centre = await getJSON("/works/" + sid, { select: WORK_FIELDS });
        if (onProgress) onProgress(1, cap);
        const refs = await fetchWorksByIds(centre.referenced_works || [], { onProgress });
        const citing = await fetchWorks(`cites:${sid}`, { cap: Math.max(50, cap - refs.length - 1), onProgress });
        const seen = new Set();
        return [centre, ...refs, ...citing].filter(w => !seen.has(w.id) && seen.add(w.id));
    }
    const makeFilter = ENTITY_FILTERS[entityType];
    if (!makeFilter) throw new Error(`Unsupported entity type: ${entityType}`);
    return fetchWorks(makeFilter(sid), { cap, onProgress });
}

let regionNames = null;
function countryName(code) {
    try {
        regionNames ??= new Intl.DisplayNames(["en"], { type: "region" });
        return regionNames.of(code) || code;
    } catch {
        return code;
    }
}

// Derive the summary fields the graph/plots/canvas/AI all use. Works in place, returns the list.
export function normalizeWorks(works) {
    for (const w of works) {
        w.title = w.title || w.display_name || "(untitled)";
        w.authorships = w.authorships || [];
        w.referenced_works = w.referenced_works || [];
        w.n_authors = w.authorships.length;
        w.institution_names = uniq(
            w.authorships.flatMap(a => (a.institutions || []).map(i => i.display_name)).filter(Boolean));
        w.n_inst = w.institution_names.length;
        // Ontology path from the OpenAlex topic hierarchy: domain > field > subfield > topic.
        w.domain = w.primary_topic?.domain?.display_name || "Unknown";
        w.field = w.primary_topic?.field?.display_name
            || w.primary_topic?.display_name
            || w.concepts?.[0]?.display_name
            || "Unknown";
        w.subfield = w.primary_topic?.subfield?.display_name || w.field;
        w.topic = w.primary_topic?.display_name || w.concepts?.[0]?.display_name || "Unknown";
        w.venue = w.primary_location?.source?.display_name || null;
        w.oa_status = w.open_access?.oa_status || "unknown";
        // Modal affiliation country — the paper's "home" for geographic axes.
        const cc = {};
        for (const a of w.authorships) {
            for (const i of a.institutions || []) if (i.country_code) cc[i.country_code] = (cc[i.country_code] || 0) + 1;
        }
        w.country_code = Object.entries(cc).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
        w.country = w.country_code ? countryName(w.country_code) : "Unknown";
    }
    return works;
}

export function reconstructAbstract(invertedIndex, maxWords = 350) {
    if (!invertedIndex) return null;
    const words = [];
    for (const [word, positions] of Object.entries(invertedIndex)) {
        for (const pos of positions) words[pos] = word;
    }
    const text = words.filter(Boolean).slice(0, maxWords).join(" ");
    return words.length > maxWords ? text + "…" : text;
}

export async function fetchWorkDetails(id) {
    const w = await getJSON("/works/" + shortId(id), {
        select: WORK_FIELDS + ",abstract_inverted_index,biblio,keywords",
    });
    w.abstract = reconstructAbstract(w.abstract_inverted_index);
    delete w.abstract_inverted_index;
    return w;
}

// Batch-fetch reconstructed abstracts — feeds the AI's discourse/opinion analysis.
export async function fetchAbstracts(ids, { max = 12 } = {}) {
    const wanted = ids.slice(0, max).map(shortId);
    const out = [];
    for (let i = 0; i < wanted.length; i += 25) {
        const page = await getJSON("/works", {
            filter: "ids.openalex:" + wanted.slice(i, i + 25).join("|"),
            select: "id,title,display_name,publication_year,cited_by_count,abstract_inverted_index",
            "per-page": 25,
        });
        for (const w of page.results) {
            out.push({
                id: w.id,
                title: w.title || w.display_name,
                year: w.publication_year,
                cited_by_count: w.cited_by_count,
                abstract: (reconstructAbstract(w.abstract_inverted_index, 250) || "(no abstract available)"),
            });
        }
    }
    return out;
}

const RAW_ENDPOINTS = ["works", "authors", "institutions", "sources", "topics", "concepts", "funders", "publishers"];

// Constrained raw query used by the AI assistant to answer arbitrary data questions.
export async function rawQuery({ endpoint, search, filter, group_by, sort, per_page = 10, select }) {
    if (!RAW_ENDPOINTS.includes(endpoint)) throw new Error(`endpoint must be one of ${RAW_ENDPOINTS.join(", ")}`);
    const data = await getJSON("/" + endpoint, {
        search, filter, group_by, sort, select,
        "per-page": Math.min(Number(per_page) || 10, 25),
    });
    if (group_by) {
        return { count: data.meta?.count, groups: (data.group_by || []).slice(0, 30) };
    }
    // Trim the payload the model sees: drop the heaviest fields unless explicitly selected.
    const results = (data.results || []).map(r => {
        const { abstract_inverted_index, abstract_inverted_index_v3, counts_by_year, ...rest } = r;
        if (!select && rest.referenced_works) rest.referenced_works = rest.referenced_works.length + " ids (omitted)";
        return rest;
    });
    return { count: data.meta?.count, results };
}
