// AI assistant — Claude with tool use (official Anthropic SDK, browser build),
// voice input via the Web Speech API, optional spoken replies.

import { escapeHTML } from "./config.js";
import { PLOT_IDS } from "./views/viewplots.js";

const SDK_URL = "https://esm.sh/@anthropic-ai/sdk";
const $ = id => document.getElementById(id);

const SYSTEM = `You are the built-in assistant of the Citation Network Explorer, a web app that visualises
scholarly citation networks using live data from OpenAlex (https://openalex.org).

The app has five views you can switch between: "3d" (3D force-directed citation network), "2d"
(GPU-accelerated 2D network), "map" (world map of institutions and their collaborations), "canvas"
(task-adaptive multi-axis 3D scatter — each axis carries a contextual dimension), and "plots"
(analytics dashboard). The network can be grouped by paper, author, institution, journal, topic or field,
and coloured/sized by citation count, year, author count, institution count, or field.

The CANVAS is the preferred answer to analytical "how/where/when has X developed" questions: use
configure_canvas to assign dimensions to axes. Dimensions: year, citations, fwci, topic, subfield,
field (topic/subfield/field are ordered by the OpenAlex ontology: domain > field > subfield > topic),
country, venue, none. Task presets: ideation (year × topic × citations), geography (year × country ×
topic), impact (year × venue × citations), semantic (field × topic × year). Examples:
"where are the authors of this work from and how has that shifted over time?" → load the network,
then configure_canvas x=year y=country; "how did the ideas evolve?" → task=ideation.

To analyse debates or differing scholarly opinions around a body of work: find the relevant works
(query_openalex with filter=cites:W… for citing papers, select=id,title,cited_by_count), then call
get_abstracts on a representative sample and synthesise the differing positions from the abstracts,
citing paper titles.

Use your tools to answer questions and to drive the display:
- To answer questions about a specific paper, author, institution or topic, first resolve it with
  search_entities (or use the loaded dataset via get_current_stats), then query_openalex or
  get_work_details for facts.
- query_openalex supports OpenAlex filter syntax, e.g. filter="author.id:A5023888391,publication_year:2020"
  or group_by="publication_year". Prefer group_by for aggregate questions (counts per year, top venues, …).
- When the user asks to SEE something (a network, a map, a plot), call load_network / set_view /
  configure_graph / show_plot / filter_years so the display actually changes, then confirm briefly.
- OpenAlex IDs look like W… (works), A… (authors), I… (institutions), S… (sources/journals), T… (topics),
  C… (concepts), F… (funders).
- Call get_current_stats before answering questions about "this network" / "these papers".

Keep replies short (1–3 sentences) unless the user asks for detail. State numbers exactly as returned by
tools. If a request is ambiguous, pick the most likely interpretation and say what you did.`;

const TOOLS = [
    {
        name: "search_entities",
        description: "Search OpenAlex for authors, papers, institutions, topics, journals or funders by name. Returns the best matches with their OpenAlex IDs.",
        input_schema: {
            type: "object",
            properties: { query: { type: "string", description: "Name or title to search for" } },
            required: ["query"],
        },
    },
    {
        name: "load_network",
        description: "Load the citation network of an entity into the explorer (replaces the current dataset). For a work, loads the paper plus its references and citing papers.",
        input_schema: {
            type: "object",
            properties: {
                entity_type: { type: "string", enum: ["author", "institution", "source", "topic", "concept", "funder", "work"] },
                id: { type: "string", description: "OpenAlex ID, e.g. A5023888391 or https://openalex.org/A5023888391" },
                name: { type: "string", description: "Display name for the banner" },
                max_works: { type: "integer", description: "Max works to load (default 600, most cited first)" },
            },
            required: ["entity_type", "id", "name"],
        },
    },
    {
        name: "set_view",
        description: "Switch the active visualisation view.",
        input_schema: {
            type: "object",
            properties: { view: { type: "string", enum: ["3d", "2d", "map", "canvas", "plots"] } },
            required: ["view"],
        },
    },
    {
        name: "configure_graph",
        description: "Change how the network is grouped, coloured and sized.",
        input_schema: {
            type: "object",
            properties: {
                group_by: { type: "string", enum: ["paper", "author", "inst", "journal", "topic", "field"] },
                color_by: { type: "string", enum: ["cited_by_count", "publication_year", "n_authors", "n_inst", "field"] },
                size_by: { type: "string", enum: ["", "cited_by_count", "n_authors", "n_inst"] },
            },
        },
    },
    {
        name: "filter_years",
        description: "Filter the displayed network to a publication-year range. Omit both bounds to clear the filter.",
        input_schema: {
            type: "object",
            properties: {
                start_year: { type: ["integer", "null"] },
                end_year: { type: ["integer", "null"] },
            },
        },
    },
    {
        name: "show_plot",
        description: "Open the plots view and highlight one chart.",
        input_schema: {
            type: "object",
            properties: { plot: { type: "string", enum: PLOT_IDS } },
            required: ["plot"],
        },
    },
    {
        name: "configure_canvas",
        description: "Open the multi-axis canvas view and assign dimensions to its axes (task-adaptive alternative to the network graph). Give a task preset and/or explicit axes.",
        input_schema: {
            type: "object",
            properties: {
                task: { type: "string", enum: ["ideation", "geography", "impact", "semantic"] },
                x: { type: "string", enum: ["year", "citations", "fwci", "topic", "subfield", "field", "country", "venue", "none"] },
                y: { type: "string", enum: ["year", "citations", "fwci", "topic", "subfield", "field", "country", "venue", "none"] },
                z: { type: "string", enum: ["year", "citations", "fwci", "topic", "subfield", "field", "country", "venue", "none"] },
            },
        },
    },
    {
        name: "get_abstracts",
        description: "Fetch reconstructed abstracts for up to 12 works by OpenAlex ID — use for discourse/opinion analysis across a set of papers.",
        input_schema: {
            type: "object",
            properties: {
                ids: { type: "array", items: { type: "string" }, description: "OpenAlex work IDs (W…)" },
            },
            required: ["ids"],
        },
    },
    {
        name: "get_current_stats",
        description: "Summary of the currently loaded dataset: entity, work/citation counts, year range, top authors/institutions/venues/topics, most cited works, current view settings.",
        input_schema: { type: "object", properties: {} },
    },
    {
        name: "query_openalex",
        description: "Run a raw OpenAlex API query for facts not in the loaded dataset. Supports search, filter (OpenAlex filter syntax, comma = AND, pipe = OR), group_by for aggregations, sort (e.g. cited_by_count:desc), select, per_page (max 25).",
        input_schema: {
            type: "object",
            properties: {
                endpoint: { type: "string", enum: ["works", "authors", "institutions", "sources", "topics", "concepts", "funders", "publishers"] },
                search: { type: "string" },
                filter: { type: "string" },
                group_by: { type: "string" },
                sort: { type: "string" },
                select: { type: "string" },
                per_page: { type: "integer" },
            },
            required: ["endpoint"],
        },
    },
    {
        name: "get_work_details",
        description: "Full details of one work by OpenAlex ID, including its abstract.",
        input_schema: {
            type: "object",
            properties: { id: { type: "string" } },
            required: ["id"],
        },
    },
];

export function initAI(app) {
    let AnthropicSDK = null;
    let client = null;
    let clientSig = null;
    let messages = [];
    let busy = false;

    // ---------- settings ----------
    // One-time migration from the original single-provider keys.
    if (localStorage.getItem("anthropic_api_key") && !localStorage.getItem("cne_ai-key")) {
        localStorage.setItem("cne_ai-key", localStorage.getItem("anthropic_api_key"));
    }
    if (localStorage.getItem("ai_model") && !localStorage.getItem("cne_ai-model")) {
        localStorage.setItem("cne_ai-model", localStorage.getItem("ai_model"));
    }
    const PERSISTED = [
        "ai-provider", "ai-key", "ai-model",
        "bedrock-region", "bedrock-access-key", "bedrock-secret-key", "bedrock-session-token", "bedrock-model",
        "foundry-resource", "foundry-key", "foundry-model",
        "openai-base", "openai-key", "openai-model",
    ];
    for (const id of PERSISTED) {
        const el = $(id);
        const stored = localStorage.getItem("cne_" + id);
        if (stored !== null && stored !== "") el.value = stored;
        el.addEventListener("change", () => {
            localStorage.setItem("cne_" + id, el.value.trim());
            client = null; // any credential/model change invalidates the cached client
        });
    }
    const providerSelect = $("ai-provider");
    function updateProviderFields() {
        for (const el of document.querySelectorAll("#ai-settings .provider-fields")) {
            el.classList.toggle("hidden", el.dataset.provider !== providerSelect.value);
        }
    }
    providerSelect.addEventListener("change", updateProviderFields);
    updateProviderFields();

    const ttsCheck = $("ai-tts");
    ttsCheck.checked = localStorage.getItem("ai_tts") === "1";
    ttsCheck.addEventListener("change", () => localStorage.setItem("ai_tts", ttsCheck.checked ? "1" : "0"));

    // Active provider configuration, or null if required fields are missing.
    function getConfig() {
        const provider = providerSelect.value;
        const v = id => $(id).value.trim();
        if (provider === "anthropic") {
            if (!v("ai-key")) return null;
            return { provider, key: v("ai-key"), model: v("ai-model") || "claude-opus-5" };
        }
        if (provider === "bedrock") {
            if (!v("bedrock-region") || !v("bedrock-access-key") || !v("bedrock-secret-key")) return null;
            return {
                provider, region: v("bedrock-region"),
                accessKey: v("bedrock-access-key"), secretKey: v("bedrock-secret-key"),
                sessionToken: v("bedrock-session-token"),
                model: v("bedrock-model") || "anthropic.claude-opus-5",
            };
        }
        if (provider === "foundry") {
            if (!v("foundry-resource") || !v("foundry-key")) return null;
            return {
                provider, resource: v("foundry-resource").replace(/^https?:\/\//, "").replace(/\/+$/, ""),
                key: v("foundry-key"), model: v("foundry-model") || "claude-opus-5",
            };
        }
        if (provider === "openai") {
            if (!v("openai-base") || !v("openai-model")) return null;
            return { provider, base: v("openai-base").replace(/\/+$/, ""), key: v("openai-key"), model: v("openai-model") };
        }
        return null;
    }

    // ---------- panel ----------
    const panel = $("ai-panel");
    $("ai-toggle").addEventListener("click", () => {
        panel.classList.toggle("hidden");
        $("ai-toggle").classList.toggle("active", !panel.classList.contains("hidden"));
        if (!panel.classList.contains("hidden")) $("ai-input").focus();
    });
    $("ai-close").addEventListener("click", () => {
        panel.classList.add("hidden");
        $("ai-toggle").classList.remove("active");
    });
    $("ai-settings-btn").addEventListener("click", () => $("ai-settings").classList.toggle("hidden"));

    // ---------- messages ----------
    const messagesEl = $("ai-messages");

    function renderMarkdown(text) {
        let html = escapeHTML(text);
        html = html.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
        html = html.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
        return html;
    }

    function addMsg(cls, text, { html = false } = {}) {
        const el = document.createElement("div");
        el.className = "ai-msg " + cls;
        if (html) el.innerHTML = text;
        else el.innerHTML = renderMarkdown(text);
        messagesEl.appendChild(el);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return el;
    }

    function speak(text) {
        if (!ttsCheck.checked || !window.speechSynthesis) return;
        const plain = text.replace(/\*\*|`/g, "").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");
        speechSynthesis.cancel();
        speechSynthesis.speak(new SpeechSynthesisUtterance(plain));
    }

    // ---------- provider clients ----------
    async function ensureClient(cfg) {
        const sig = JSON.stringify(cfg);
        if (client && clientSig === sig) return client;
        if (cfg.provider === "anthropic") {
            const mod = await import(SDK_URL);
            AnthropicSDK = mod.default;
            client = new AnthropicSDK({ apiKey: cfg.key, dangerouslyAllowBrowser: true });
        } else if (cfg.provider === "bedrock") {
            const mod = await import("https://esm.sh/@anthropic-ai/bedrock-sdk");
            const Ctor = mod.AnthropicBedrockMantle || mod.AnthropicBedrock;
            client = new Ctor({
                awsRegion: cfg.region,
                providerChainResolver: async () => ({
                    accessKeyId: cfg.accessKey,
                    secretAccessKey: cfg.secretKey,
                    ...(cfg.sessionToken ? { sessionToken: cfg.sessionToken } : {}),
                }),
                dangerouslyAllowBrowser: true,
            });
        } else if (cfg.provider === "foundry") {
            const mod = await import("https://esm.sh/@anthropic-ai/foundry-sdk");
            const Ctor = mod.AnthropicFoundry || mod.default;
            client = new Ctor({ apiKey: cfg.key, resource: cfg.resource, dangerouslyAllowBrowser: true });
        } else {
            client = { openaiCompatible: true }; // plain fetch adapter, no SDK
        }
        clientSig = sig;
        return client;
    }

    // One request through whichever provider is active, always returning
    // Anthropic-shaped { content, stop_reason }.
    async function sendRequest(cfg, c) {
        if (cfg.provider === "openai") return openaiCreate(cfg);
        const params = { model: cfg.model, max_tokens: 4096, system: SYSTEM, tools: TOOLS, messages };
        if (cfg.provider === "anthropic") {
            params.system = [{ type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } }];
            if (/^claude-(opus-5|fable-5)/.test(cfg.model)) {
                // Server-side refusal fallback — Claude API only (not Bedrock/Foundry).
                return c.beta.messages.create({
                    ...params,
                    betas: ["server-side-fallback-2026-07-01"],
                    fallbacks: "default",
                });
            }
        }
        return c.messages.create(params);
    }

    // ---------- OpenAI-compatible adapter ----------
    function toOpenAIMessages() {
        const out = [{ role: "system", content: SYSTEM }];
        for (const m of messages) {
            if (typeof m.content === "string") {
                out.push({ role: m.role, content: m.content });
                continue;
            }
            if (m.role === "user") {
                for (const b of m.content) {
                    if (b.type === "tool_result") {
                        out.push({
                            role: "tool", tool_call_id: b.tool_use_id,
                            content: typeof b.content === "string" ? b.content : JSON.stringify(b.content),
                        });
                    }
                }
            } else {
                const text = m.content.filter(b => b.type === "text").map(b => b.text).join("\n");
                const toolCalls = m.content.filter(b => b.type === "tool_use").map(b => ({
                    id: b.id, type: "function",
                    function: { name: b.name, arguments: JSON.stringify(b.input || {}) },
                }));
                const msg = { role: "assistant", content: text || null };
                if (toolCalls.length) msg.tool_calls = toolCalls;
                out.push(msg);
            }
        }
        return out;
    }

    async function openaiCreate(cfg) {
        const res = await fetch(cfg.base + "/chat/completions", {
            method: "POST",
            headers: {
                "content-type": "application/json",
                ...(cfg.key ? { authorization: "Bearer " + cfg.key } : {}),
            },
            body: JSON.stringify({
                model: cfg.model,
                max_tokens: 4096,
                messages: toOpenAIMessages(),
                tools: TOOLS.map(t => ({
                    type: "function",
                    function: { name: t.name, description: t.description, parameters: t.input_schema },
                })),
                tool_choice: "auto",
            }),
        });
        if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 300)}`);
        const data = await res.json();
        const m = data.choices?.[0]?.message || {};
        const content = [];
        if (m.content) {
            content.push({ type: "text", text: typeof m.content === "string" ? m.content : JSON.stringify(m.content) });
        }
        for (const tc of m.tool_calls || []) {
            let input = {};
            try {
                input = JSON.parse(tc.function?.arguments || "{}");
            } catch { /* leave empty input */ }
            content.push({
                type: "tool_use",
                id: tc.id || "call_" + Math.random().toString(36).slice(2),
                name: tc.function?.name, input,
            });
        }
        return { content, stop_reason: m.tool_calls?.length ? "tool_use" : "end_turn" };
    }

    function trimHistory() {
        if (messages.length <= 40) return;
        let i = messages.length - 30;
        while (i < messages.length && !(messages[i].role === "user" && typeof messages[i].content === "string")) i++;
        if (i < messages.length) messages = messages.slice(i);
    }

    async function runTurn(userText) {
        const cfg = getConfig();
        if (!cfg) {
            await fallbackParser(userText);
            return;
        }
        let c;
        try {
            c = await ensureClient(cfg);
        } catch (err) {
            console.error(err);
            addMsg("error", `Could not load the ${cfg.provider} client: ${err.message}`);
            return;
        }
        messages.push({ role: "user", content: userText });
        trimHistory();
        const thinkingEl = addMsg("thinking", "Thinking…");
        let finalText = "";
        try {
            for (let iteration = 0; iteration < 12; iteration++) {
                const response = await sendRequest(cfg, c);
                messages.push({ role: "assistant", content: response.content });
                for (const block of response.content) {
                    if (block.type === "text" && block.text.trim()) {
                        finalText = block.text;
                        addMsg("assistant", block.text);
                    }
                }
                if (response.stop_reason === "pause_turn") continue;
                if (response.stop_reason === "refusal") {
                    addMsg("error", "The model declined to answer that request.");
                    break;
                }
                const toolUses = response.content.filter(b => b.type === "tool_use");
                if (response.stop_reason !== "tool_use" || !toolUses.length) break;
                const results = [];
                for (const tu of toolUses) {
                    addMsg("tool", `⚙ ${tu.name}(${summariseInput(tu.input)})`);
                    let result, isError = false;
                    try {
                        result = await app.execute(tu.name, tu.input || {});
                    } catch (err) {
                        result = String(err?.message || err);
                        isError = true;
                        console.error(`tool ${tu.name} failed`, err);
                    }
                    results.push({
                        type: "tool_result",
                        tool_use_id: tu.id,
                        content: typeof result === "string" ? result : JSON.stringify(result),
                        ...(isError ? { is_error: true } : {}),
                    });
                }
                messages.push({ role: "user", content: results });
            }
            if (finalText) speak(finalText);
        } catch (err) {
            handleAPIError(err, cfg);
        } finally {
            thinkingEl.remove();
        }
    }

    function summariseInput(input) {
        const s = JSON.stringify(input ?? {});
        return s.length > 90 ? s.slice(0, 88) + "…" : s;
    }

    function handleAPIError(err, cfg) {
        console.error(err);
        const status = err?.status;
        if (status === 401 || status === 403 || (AnthropicSDK && err instanceof AnthropicSDK.AuthenticationError)) {
            addMsg("error", "Authentication failed — check the credentials in ⚙ settings.");
            $("ai-settings").classList.remove("hidden");
        } else if (status === 429 || (AnthropicSDK && err instanceof AnthropicSDK.RateLimitError)) {
            addMsg("error", "Rate limited — wait a moment and try again.");
        } else if (err instanceof TypeError && cfg?.provider === "openai") {
            addMsg("error", `Could not reach ${cfg.base} — is the server running, and does it allow CORS from this origin (e.g. OLLAMA_ORIGINS for Ollama)?`);
        } else if (err instanceof TypeError) {
            addMsg("error", `Network/CORS error talking to the ${cfg?.provider ?? ""} endpoint: ${err.message}. The endpoint may not allow browser requests from this origin.`);
        } else {
            addMsg("error", `Request failed${status ? ` (${status})` : ""}: ` + (err?.message || err));
        }
        // Drop any dangling tool_use turn so the next request is valid.
        while (messages.length && messages[messages.length - 1].role === "assistant") messages.pop();
    }

    // Minimal command parser used when no API key is configured.
    async function fallbackParser(text) {
        const t = text.toLowerCase().trim();
        const viewMatch = t.match(/\b(3d|2d|map|canvas|plots?)\b/);
        if (/^(show|switch|go|open|view)\b/.test(t) && viewMatch) {
            await app.execute("set_view", { view: viewMatch[1].replace("plots", "plots").replace(/^plot$/, "plots") });
            addMsg("assistant", `Switched to the ${viewMatch[1]} view.`);
            return;
        }
        const loadMatch = text.match(/^(?:load|show)\s+(.+?)(?:'s)?(?:\s+network)?$/i);
        if (loadMatch) {
            const results = await app.execute("search_entities", { query: loadMatch[1] });
            if (results.length) {
                const r = results[0];
                addMsg("assistant", `Loading ${r.display_name} (${r.entity_type})…`);
                await app.execute("load_network", { entity_type: r.entity_type, id: r.id, name: r.display_name });
                return;
            }
        }
        addMsg("error", "Configure an AI provider in ⚙ settings (Anthropic API, Amazon Bedrock, Azure AI Foundry, or a local OpenAI-compatible server) to unlock the full assistant. Without one I only understand simple commands like “show map” or “load <author name>”.");
        $("ai-settings").classList.remove("hidden");
    }

    // ---------- input ----------
    const form = $("ai-form");
    const input = $("ai-input");

    async function submit() {
        const text = input.value.trim();
        if (!text || busy) return;
        input.value = "";
        input.style.height = "auto";
        addMsg("user", text);
        busy = true;
        $("ai-send").disabled = true;
        try {
            await runTurn(text);
        } finally {
            busy = false;
            $("ai-send").disabled = false;
        }
    }

    form.addEventListener("submit", e => {
        e.preventDefault();
        submit();
    });
    input.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
        }
    });
    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });

    // ---------- voice ----------
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = $("ai-mic");
    if (!SR) {
        micBtn.title = "Voice input is not supported in this browser";
        micBtn.disabled = true;
        micBtn.style.opacity = 0.4;
    } else {
        let rec = null;
        let listening = false;
        micBtn.addEventListener("click", () => {
            if (listening) {
                rec?.stop();
                return;
            }
            rec = new SR();
            rec.lang = "en";
            rec.interimResults = true;
            rec.continuous = false;
            let finalText = "";
            rec.onresult = ev => {
                let interim = "";
                for (const res of ev.results) {
                    if (res.isFinal) finalText += res[0].transcript;
                    else interim += res[0].transcript;
                }
                input.value = (finalText + interim).trim();
            };
            rec.onerror = ev => {
                if (ev.error !== "aborted") addMsg("error", "Voice input error: " + ev.error);
            };
            rec.onend = () => {
                listening = false;
                micBtn.classList.remove("listening");
                if (input.value.trim()) submit();
            };
            listening = true;
            micBtn.classList.add("listening");
            rec.start();
        });
    }

    return {
        ask(text) {
            panel.classList.remove("hidden");
            $("ai-toggle").classList.add("active");
            input.value = text;
            submit();
        },
    };
}
