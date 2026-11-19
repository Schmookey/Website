"use strict";
// A DOM-free regression test. No browser, network, existing page edits or deps.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const js = fs.readFileSync(path.join(root, "assets/js/site-theme.js"), "utf8");
const main = fs.readFileSync(path.join(root, "assets/js/main.js"), "utf8");
const css = fs.readFileSync(path.join(root, "assets/css/snes-light-theme.css"), "utf8");

function simulate(savedTheme, blockedStorage = false) {
  const store = {};
  if (savedTheme) store["schmookey-theme-v1"] = savedTheme;
  const links = [
    {getAttribute: () => "/index.html", name: "Home"},
    {getAttribute: () => "/about.html", name: "About"}
  ];
  const events = {};
  const attrs = {};
  const scripts = [];
  const nav = {
    querySelector(sel) {return sel === ".site-theme-toggle" ? this.button : null;},
    querySelectorAll() { return links; },
    insertBefore(button, anchor) {
      assert.equal(anchor.name, "Home");
      this.button = button;
      this.insertedBeforeHome = true;
    }
  };
  const doc = {
    readyState: "complete",
    baseURI: "https://schmookey.xyz/",
    documentElement: {setAttribute(key, value) {attrs[key] = value;}},
    head: {appendChild(node) {scripts.push(node);}},
    querySelector(sel) {
      if (sel === "nav.menu") return nav;
      if (sel === "link[data-schmookey-theme-css]") return scripts.find(s => s.dataset?.schmookeyThemeCss) || null;
      return null;
    },
    createElement(tag) {
      const node = {tag, dataset:{}, attributes:{},
        setAttribute(k,v) {this.attributes[k] = v;},
        addEventListener(k, fn) {events[k] = fn;}
      };
      return node;
    }
  };
  const context = vm.createContext({
    document: doc,
    URL,
    localStorage: {
      getItem(k) {if(blockedStorage) throw new Error("Denied");return store[k] || null;},
      setItem(k,v) {if(blockedStorage) throw new Error("Denied");store[k]=v;}
    }
  });
  vm.runInContext(js, context);
  return {attrs, scripts, nav, events, store};
}

const initial = simulate();
assert.equal(initial.attrs["data-schmookey-theme"], "dark");
assert.equal(initial.nav.insertedBeforeHome, true);
assert.equal(initial.nav.button.attributes["aria-pressed"], "false");
assert.equal(initial.nav.button.attributes["aria-label"], "Switch to light mode");
assert.match(initial.nav.button.innerHTML, /<svg/);
assert.equal(initial.scripts.length, 1);
assert.equal(initial.scripts[0].href, "/assets/css/snes-light-theme.css");
initial.events.click();
assert.equal(initial.attrs["data-schmookey-theme"], "light");
assert.equal(initial.store["schmookey-theme-v1"], "light");
assert.equal(initial.nav.button.attributes["aria-pressed"], "true");
assert.equal(initial.nav.button.attributes["aria-label"], "Switch to dark mode");
initial.events.click();
assert.equal(initial.attrs["data-schmookey-theme"], "dark");
assert.equal(initial.store["schmookey-theme-v1"], "dark");
const restored = simulate("light");
assert.equal(restored.attrs["data-schmookey-theme"], "light");
const blocked = simulate(null, true);
assert.equal(blocked.attrs["data-schmookey-theme"], "dark");
blocked.events.click();
assert.equal(blocked.attrs["data-schmookey-theme"], "light",
  "The toggle works even without localStorage");

assert.match(main, /script\.src = "\/assets\/js\/site-theme\.js"/);
assert.match(css, /data-schmookey-theme="light"/);
assert.match(css, /--snes-red: #e60012/);
assert.match(css, /--snes-ink: #000000/);
assert.match(css, /--snes-shell: #b9bac2/);
assert.match(css, /\.site-theme-toggle\s*\{/);
assert.match(css, /border-radius: 50%/);
assert.doesNotMatch(css, /body\.light\s*\{/);
assert.doesNotMatch(css, /\.profile-card\s*\{/,
  "The bespoke trading card must not be restyled directly");
assert.doesNotMatch(css, /\.site-banner img\s*\{/,
  "The existing banner artwork is preserved");
assert.doesNotMatch(js, /body\.classList\.|document\.body\.className/,
  "Never rewrite existing body theme classes");

console.log("PASS: standalone site-wide toggle, persistence, button placement, SNES palette, and original styling");
