// DOM helpers: toasts, loading overlay, modal, legend, tooltip, search autocomplete.

import { escapeHTML, fmt, shortId } from "./config.js";
import { autocomplete } from "./openalex.js";

const $ = id => document.getElementById(id);

// ---------- toasts ----------

export function toast(message, { error = false, ms = 4000 } = {}) {
    const el = document.createElement("div");
    el.className = "toast" + (error ? " error" : "");
    el.textContent = message;
    $("toasts").appendChild(el);
    setTimeout(() => el.remove(), ms);
}

// ---------- loading ----------

export function showLoading(text = "Loading…") {
    $("loading-text").textContent = text;
    $("loading").classList.remove("hidden");
}

export function loadingProgress(text) {
    $("loading-text").textContent = text;
}

export function hideLoading() {
    $("loading").classList.add("hidden");
}

// ---------- modal ----------

export function showModal(titleHTML, bodyHTML) {
    $("modal-title").innerHTML = titleHTML;
    $("modal-body").innerHTML = bodyHTML;
    $("modal-backdrop").classList.remove("hidden");
    return $("modal-body");
}

export function hideModal() {
    $("modal-backdrop").classList.add("hidden");
}

export function workModalHTML(w) {
    const authors = w.authorships.map(a => {
        const inst = a.institutions?.[0]?.display_name;
        return escapeHTML(inst ? `${a.author?.display_name} (${inst})` : a.author?.display_name || "");
    }).filter(Boolean).join(", ");
    const topics = (w.topics || []).slice(0, 6).map(t => `<span class="chip">${escapeHTML(t.display_name)}</span>`).join("");
    return `
        <div><b>${escapeHTML(authors)}</b></div>
        ${w.venue ? `<div>${escapeHTML(w.venue)} · ${escapeHTML(w.type || "")}</div>` : ""}
        <div class="chips">${topics}</div>
        <div>Citations: <b>${fmt(w.cited_by_count)}</b>${w.fwci != null ? ` · FWCI ${w.fwci.toFixed(2)}` : ""}
            · Open access: ${escapeHTML(w.oa_status)}</div>
        ${w.abstract ? `<p>${escapeHTML(w.abstract)}</p>` : ""}
        <div>${w.doi ? `<a href="${escapeHTML(w.doi)}" target="_blank" rel="noopener">${escapeHTML(w.doi)}</a><br>` : ""}
            <a href="${escapeHTML(w.id)}" target="_blank" rel="noopener">OpenAlex: ${escapeHTML(shortId(w.id))}</a></div>
        <div class="modal-actions">
            <button data-action="ego" data-id="${escapeHTML(w.id)}" data-name="${escapeHTML(w.title)}">Load citation network of this paper</button>
            <button data-action="ask" data-id="${escapeHTML(w.id)}" data-name="${escapeHTML(w.title)}">Ask AI about this paper</button>
        </div>`;
}

export function groupModalHTML(node) {
    const top = (node.works || []).slice()
        .sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0)).slice(0, 12)
        .map(w => `<div class="work-row" data-work-id="${escapeHTML(w.id)}">
            ${escapeHTML(w.title)} (${w.publication_year ?? "?"}) — ${fmt(w.cited_by_count)} citations</div>`)
        .join("");
    const entityType = { author: "author", inst: "institution", journal: "source" }[node.kind];
    const loadBtn = entityType && String(node.id).startsWith("https://openalex.org/")
        ? `<button data-action="load-entity" data-type="${entityType}" data-id="${escapeHTML(node.id)}"
             data-name="${escapeHTML(node.name)}">Load full network of this ${entityType}</button>` : "";
    return `
        <div>${fmt(node.n_works)} works in this dataset · ${fmt(node.cited_by_count)} citations
            · ${node.first_year ?? "?"}–${node.last_year ?? "?"} · Main field: ${escapeHTML(node.field)}</div>
        <h4>Most cited works</h4>${top}
        <div class="modal-actions">${loadBtn}
            <button data-action="ask" data-id="${escapeHTML(node.id)}" data-name="${escapeHTML(node.name)}">Ask AI about this</button>
        </div>`;
}

// ---------- legend ----------

export function renderLegend(scale, attrLabel) {
    const el = $("legend");
    if (!scale) {
        el.innerHTML = "";
        return;
    }
    if (scale.type === "categorical") {
        el.innerHTML = scale.legend.map(item =>
            `<div class="legend-row"><span class="legend-swatch" style="background:${item.color}"></span>
             <span>${escapeHTML(item.label)}</span></div>`).join("");
    } else {
        el.innerHTML = `
            <div>${escapeHTML(attrLabel)}</div>
            <div class="legend-ramp">${scale.ramp.map(c => `<div style="background:${c}"></div>`).join("")}</div>
            <div class="legend-minmax"><span>${fmt(scale.min)}</span><span>${fmt(scale.max)}</span></div>`;
    }
}

// ---------- entity banner ----------

export function renderBanner(entity, stats) {
    const el = $("entity-banner");
    if (!entity) {
        el.classList.add("hidden");
        return;
    }
    el.classList.remove("hidden");
    el.innerHTML = `<div class="entity-name">${escapeHTML(entity.name)}</div>
        <div class="entity-meta">${fmt(stats.count)} works · ${fmt(stats.totalCitations)} citations
        · ${stats.yearMin ?? "?"}–${stats.yearMax ?? "?"}</div>`;
    document.title = `${entity.name} — Citation Network Explorer`;
}

// ---------- tooltip ----------

const tooltipEl = () => $("tooltip");

export function showTooltip(html, x, y) {
    const el = tooltipEl();
    el.innerHTML = html;
    el.classList.remove("hidden");
    const pad = 14;
    const w = el.offsetWidth, h = el.offsetHeight;
    el.style.left = Math.min(x + pad, window.innerWidth - w - 8) + "px";
    el.style.top = Math.min(y + pad, window.innerHeight - h - 8) + "px";
}

export function hideTooltip() {
    tooltipEl().classList.add("hidden");
}

export function nodeTooltipHTML(node) {
    if (node.kind === "paper") {
        const w = node.work;
        return `<b>${escapeHTML(w.title)}</b> (${w.publication_year ?? "?"})<br>
            ${escapeHTML(w.authorships.slice(0, 6).map(a => a.author?.display_name).filter(Boolean).join(", "))}
            ${w.n_authors > 6 ? " …" : ""}<br>
            ${w.venue ? escapeHTML(w.venue) + "<br>" : ""}
            ${escapeHTML(w.topic)}<br>Citations: ${fmt(w.cited_by_count)}`;
    }
    return `<b>${escapeHTML(node.name)}</b><br>${fmt(node.n_works)} works · ${fmt(node.cited_by_count)} citations
        · ${node.first_year ?? "?"}–${node.last_year ?? "?"}<br>${escapeHTML(node.field)}`;
}

// ---------- search autocomplete ----------

const TYPE_ICONS = { work: "paper", author: "author", institution: "institution", source: "journal", topic: "topic", concept: "concept", funder: "funder", publisher: "publisher" };

export function initSearch(onSelect) {
    const input = $("search");
    const results = $("search-results");
    let options = [];
    let active = -1;
    let timer = null;
    let ctrl = null;

    function close() {
        results.classList.add("hidden");
        results.innerHTML = "";
        active = -1;
    }

    function render() {
        if (!options.length) {
            close();
            return;
        }
        results.innerHTML = options.map((r, i) => `
            <div class="search-result${i === active ? " active" : ""}" data-i="${i}">
                <span class="type">${escapeHTML(TYPE_ICONS[r.entity_type] || r.entity_type)}</span>
                <span><span class="name">${escapeHTML(r.display_name)}</span>
                ${r.hint ? `<span class="hint-text"> — ${escapeHTML(r.hint)}</span>` : ""}</span>
            </div>`).join("");
        results.classList.remove("hidden");
        for (const el of results.querySelectorAll(".search-result")) {
            el.addEventListener("mousedown", e => {
                e.preventDefault();
                pick(Number(el.dataset.i));
            });
        }
    }

    function pick(i) {
        const item = options[i];
        if (!item) return;
        input.value = item.display_name;
        close();
        input.blur();
        onSelect(item);
    }

    input.addEventListener("input", () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (q.length < 2) {
            close();
            return;
        }
        timer = setTimeout(async () => {
            ctrl?.abort();
            ctrl = new AbortController();
            const mine = ctrl;
            try {
                const res = await autocomplete(q);
                if (mine.signal.aborted) return;
                options = res;
                active = -1;
                render();
            } catch (err) {
                if (!mine.signal.aborted) console.error(err);
            }
        }, 250);
    });

    input.addEventListener("keydown", e => {
        if (e.key === "ArrowDown") {
            active = Math.min(active + 1, options.length - 1);
            render();
            e.preventDefault();
        } else if (e.key === "ArrowUp") {
            active = Math.max(active - 1, 0);
            render();
            e.preventDefault();
        } else if (e.key === "Enter") {
            pick(active >= 0 ? active : 0);
            e.preventDefault();
        } else if (e.key === "Escape") {
            close();
        }
    });

    input.addEventListener("blur", () => setTimeout(close, 150));
}
