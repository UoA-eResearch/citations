// Run axe-core on archived HTML files under jsdom (no script execution, no network), restricted to a frozen subset
// of rules that a static DOM can evaluate. Input: newline-separated file paths on stdin. Output: one JSON line per file.
const fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");
const axeSource = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
const RULES = ["image-alt", "input-image-alt", "label", "select-name", "button-name", "link-name", "html-has-lang",
  "html-lang-valid", "valid-lang", "frame-title", "th-has-data-cells", "td-headers-attr", "aria-required-attr",
  "aria-valid-attr-value", "aria-roles", "duplicate-id-aria", "heading-order", "list", "definition-list"];

async function one(path) {
  const html = fs.readFileSync(path, "utf8");
  const vc = new VirtualConsole();                         // silence page console noise
  const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true, virtualConsole: vc });
  const { window } = dom;
  window.eval(axeSource);
  const nElements = window.document.getElementsByTagName("*").length;
  const res = await window.axe.run(window.document, { runOnly: { type: "rule", values: RULES }, resultTypes: ["violations"] });
  const byRule = {};
  let nodes = 0;
  for (const v of res.violations) { byRule[v.id] = v.nodes.length; nodes += v.nodes.length; }
  window.close();
  return { path, elements: nElements, violation_nodes: nodes, by_rule: byRule };
}

(async () => {
  const paths = fs.readFileSync(0, "utf8").split("\n").filter(Boolean);
  for (const p of paths) {
    try { console.log(JSON.stringify(await one(p))); }
    catch (e) { console.log(JSON.stringify({ path: p, error: String(e).slice(0, 200) })); }
  }
})();
