// Exercise the actual loader with independent mock Notes and Webmention responses.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const source = fs.readFileSync(path.join(__dirname, "../assets/js/main.js"), "utf8");
const code = source.slice(source.indexOf("function getWebmentionTarget()"),
  source.indexOf("/* =====================================================\n   SECTION 13:"));
const calls = [];
function node() {
  return {textContent: "–", innerHTML: "", addEventListener(name, fn) { this[name] = fn; },
    setAttribute() {}, removeAttribute() {}};
}
function panel(id) {
  const fields = Object.fromEntries(["replies","likes","reposts","comments","reload"].map(k => ["[data-wm-"+k+"]", node()]));
  fields.details = node();
  return {dataset: {noteTarget: "https://schmookey.xyz/notes/"+id+".html"},
    querySelector(s) {return fields[s];}, fields};
}
const panels = [panel("first"), panel("second"), panel("third")];
let observe;
const context = {URL, console, window: {IntersectionObserver: true}, document: {
  querySelectorAll: () => panels,
  getElementById: () => null
}, IntersectionObserver: class {
  constructor(fn) {observe = fn;}
  observe() {}
  unobserve() {}
}, safeHttpUrl: () => "", fetch: async url => {
  const target = new URL(url).searchParams.get("target");
  calls.push(target);
  const kinds = target.endsWith("first.html") ? ["like-of","like-of","in-reply-to","repost-of"] :
    target.endsWith("third.html") ? ["like-of"] : [];
  return {ok: true, json: async () => ({children: kinds.map(k => ({"wm-property": k,
    author: {name: "Test"}, content: {text: "Example"}}))})};
}};
vm.createContext(context);
vm.runInContext(code + "\ninitNoteWebmentions();", context);
function counts(p) {return ["replies","likes","reposts"].map(k=>p.fields["[data-wm-"+k+"]"].textContent);}
(async () => {
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(counts(panels[0]), ["1","2","1"]);
  assert.deepEqual(counts(panels[1]), ["0","0","0"]);
  assert.deepEqual(counts(panels[2]), ["–","–","–"]);
  assert.equal(calls.length, 2);
  observe([{target: panels[2], isIntersecting: true}]);
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(counts(panels[2]), ["0","1","0"]);
  assert.match(panels[0].fields["[data-wm-comments]"].innerHTML, /Example/);
  panels[0].fields["[data-wm-reload]"].click();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls.length, 4);
  assert.equal(calls[3], panels[0].dataset.noteTarget);
  console.log("PASS: independent Note counters, lazy loading and reload");
})().catch(err=>{console.error(err);process.exitCode=1;});
