"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.join(__dirname, "..");
const origin = "https://schmookey.xyz";
const location = {origin, href: origin + "/blog-archive.html", pathname: "/blog-archive.html"};

function testArchiveLinks() {
  const src = fs.readFileSync(path.join(root, "assets/js/archive.js"), "utf8");
  const ctx = vm.createContext({window: {location}, document: {addEventListener() {}}, URL, Date});
  vm.runInContext(src, ctx);
  const safe = ctx.safeArchivePostUrl;
  for (const url of ["/blog/posts/post1.html", "/blog/posts/august_updates.html", "/music/posts/listenbrainz.html"]) {
    assert.equal(safe(url), url);
  }
  for (const url of ["javascript:alert(1)", "data:text/html,bad", "//evil.example/blog/posts/post1.html", "https://evil.example/blog/posts/post1.html", "/blog/posts/../../evil.html", "/blog/posts/post1.html?x=1", "/blog/posts/post1.html#bad", "/not-our-article.html", " /blog/posts/post1.html%0a"]) {
    assert.equal(safe(url), "", `rejected: ${url}`);
  }
  assert.equal(ctx.normaliseArchivePost({url: "javascript:alert(1)",date: "2026-01-01"}), null);
  assert.equal(ctx.normaliseArchivePost({url: "/blog/posts/post1.html",date: "2026-01-01",title:"Safe"}).url, "/blog/posts/post1.html");
}

function testMainHelpers() {
  const src = fs.readFileSync(path.join(root, "assets/js/main.js"), "utf8");
  // Only run the helper definitions and script-allowlist functions, not browser initialisation.
  const first = src.slice(0, src.indexOf("/* =====================================================\n   SECTION 02"));
  const scripts = src.slice(src.indexOf("// Do not turn a data-src"), src.indexOf("/* =====================================================\n   SECTION 08"));
  const ctx = vm.createContext({window: {location}, document: {}, URL, Set, Array, String});
  vm.runInContext(first + "\n" + scripts, ctx);
  assert.equal(ctx.safeHttpUrl("https://trakt.tv/something"), "https://trakt.tv/something");
  assert.equal(ctx.safeHttpUrl("/about.html"), "/about.html");
  assert.equal(ctx.safeHttpUrl("javascript:alert(1)"), "");
  assert.equal(ctx.safeHttpUrl("http://evil.example/"), "");
  assert.equal(ctx.safeHttpUrl("https://u:p@evil.example/"), "");
  assert.equal(ctx.safeApprovedScriptUrl("https://cdring.neocities.org/cdring/onionring-widget.js"), "https://cdring.neocities.org/cdring/onionring-widget.js");
  assert.equal(ctx.safeApprovedScriptUrl("/assets/js/main.js"), "/assets/js/main.js");
  assert.equal(ctx.safeApprovedScriptUrl("https://evil.example/script.js"), "");
  assert.equal(ctx.safeApprovedScriptUrl("https://cdring.neocities.org/malicious.js"), "");
  assert.equal(ctx.safeApprovedScriptUrl("https://cdring.neocities.org/cdring/onionring-widget.js?surprise=1"), "");
}

testArchiveLinks();
testMainHelpers();
console.log("PASS: JavaScript URL and dynamic-script security tests");
