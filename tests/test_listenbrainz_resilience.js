// Offline regression checks for fault-tolerant ListenBrainz loading.
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const source = fs.readFileSync(path.join(__dirname, "..", "assets/js/main.js"), "utf8");

const widget = source.slice(source.indexOf("function initListenBrainzWidget("),
                            source.indexOf("/* =====================================================\n   SECTION 14:", source.indexOf("function initListenBrainzWidget(")));
const journal = source.slice(source.indexOf("async function loadListeningJournal("),
                             source.indexOf("/* =====================================================\n   SECTION 15:", source.indexOf("async function loadListeningJournal(")));
const init = source.slice(source.indexOf("function initPage() {"),
                          source.indexOf("document.addEventListener(\"DOMContentLoaded\"", source.indexOf("function initPage() {")));

assert.ok(widget.includes('const POLL_MS = 60000;'), "Widget refresh should be conservative");
assert.ok(widget.includes("let lastGoodListen = false;"));
assert.ok(widget.includes("lastGoodListen = true;"));
assert.ok(widget.includes("if (!lastGoodListen)"), "Retain successful listen during temporary outages");
assert.ok(widget.includes("getPlayingNow().catch(() => null)"), "Fallback to recent listens");
assert.ok(widget.includes("getLatestListen()"), "Recent listens fallback exists");
assert.ok(journal.includes("new AbortController()"), "Bound a hanging journal request");
assert.ok(journal.includes("clearTimeout(timeout)"), "Release the request timeout");
assert.ok(journal.includes("retry.addEventListener(\"click\""), "Provide manual retry");
assert.ok(journal.includes("loadListeningJournal(username, limit)"), "Retry original user and limit");
assert.ok(journal.includes("container.replaceChildren()"), "Replace stale error UI safely");
assert.ok(!journal.includes('innerHTML = `<p class="listening-status">Failed to load'), "Old permanent error removed");
assert.ok(init.indexOf('initListenBrainzWidget("jon_cass")') <
          init.indexOf("initWebringScripts()"), "Load music before unrelated widgets");
assert.ok(init.includes('try { initListenBrainzWidget("jon_cass"); }'), "Music startup isolated");
assert.ok(init.includes('try { loadListeningJournal("jon_cass", 100); }'), "Journal startup isolated");
console.log("PASS: ListenBrainz outage fallback, manual retry, timeout and isolated startup");
