// Central app state with a tiny pub/sub. Views subscribe to change events.

const listeners = new Map(); // event -> Set(fn)

export const state = {
    works: [],            // normalized works currently loaded (unfiltered)
    entity: null,         // {type, id, name} of what is loaded
    groupBy: "paper",
    colorBy: "cited_by_count",
    sizeBy: "cited_by_count",
    yearRange: null,      // [min, max] inclusive, or null
    view: "3d",           // '3d' | '2d' | 'map' | 'plots'
};

export function on(event, fn) {
    if (!listeners.has(event)) listeners.set(event, new Set());
    listeners.get(event).add(fn);
    return () => listeners.get(event).delete(fn);
}

export function emit(event, payload) {
    for (const fn of listeners.get(event) || []) {
        try {
            fn(payload);
        } catch (err) {
            console.error(`listener for "${event}" failed`, err);
        }
    }
}

// Works after the year filter is applied — what every view renders.
export function filteredWorks() {
    if (!state.yearRange) return state.works;
    const [lo, hi] = state.yearRange;
    return state.works.filter(w => w.publication_year >= lo && w.publication_year <= hi);
}

export function setWorks(works, entity) {
    state.works = works;
    state.entity = entity;
    state.yearRange = null;
    emit("data");
}

export function setView(view) {
    if (state.view === view) return;
    state.view = view;
    emit("view");
}

export function setYearRange(range) {
    state.yearRange = range;
    emit("filter");
}

export function setDisplay({ groupBy, colorBy, sizeBy }) {
    if (groupBy !== undefined) state.groupBy = groupBy;
    if (colorBy !== undefined) state.colorBy = colorBy;
    if (sizeBy !== undefined) state.sizeBy = sizeBy;
    emit("display");
}
