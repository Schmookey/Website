"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "blog/posts/snluk.html"), "utf8");
assert.match(html, /data-youtube-id="3ct68JZKsZ8"/);
assert.match(html, /href="https:\/\/www.youtube.com\/watch\?v=3ct68JZKsZ8"/);
assert.doesNotMatch(html, /<iframe\b[^>]*youtube/i);
assert.doesNotMatch(html, /<(?:img|link)\b[^>]*(?:ytimg\.com|youtube(?:-nocookie)?\.com)/i);
const js = fs.readFileSync(path.join(root, "assets/js/video-embed.js"), "utf8");

function setup(id) {
  let handler, replaced, created = 0, focused = false;
  const link = {
    addEventListener(name, callback) { assert.equal(name, "click"); handler = callback; },
    querySelector() { return {textContent: "Video title"}; },
    replaceWith(player) { replaced = player; }
  };
  const panel = {dataset: {youtubeId:id}, querySelector() { return link; }};
  const document = {
    querySelectorAll() { return [panel]; },
    createElement(tag) {
      assert.equal(tag, "iframe"); created++;
      return {focus() { focused = true; }};
    }
  };
  vm.runInNewContext(js, {document});
  return {get handler(){return handler;}, get created(){return created;},
    get replaced(){return replaced;}, get focused(){return focused;}};
}
const valid = setup("3ct68JZKsZ8");
assert.equal(valid.created, 0);
valid.handler({button:0,ctrlKey:true,preventDefault(){throw Error("Modified click intercepted");}});
assert.equal(valid.created, 0);
let prevented = false;
valid.handler({button:0,preventDefault(){prevented = true;}});
assert.equal(prevented, true);
assert.equal(valid.created, 1);
assert.equal(valid.replaced.src, "https://www.youtube-nocookie.com/embed/3ct68JZKsZ8");
assert.equal(valid.replaced.title, "Video title");
assert.equal(valid.replaced.allowFullscreen, true);
assert.equal(valid.focused, true);
const unsafe = setup("https://evil.example/");
assert.equal(unsafe.handler, undefined);
assert.equal(unsafe.created, 0);
console.log("PASS: YouTube player requires explicit activation and valid ID");
