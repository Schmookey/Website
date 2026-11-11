"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "assets/js/main.js"), "utf8");
const start = source.indexOf("const LISTEN_COVER_FALLBACK =");
const stop = source.indexOf("function initListenBrainzWidget", start);
assert.ok(start > 0 && stop > start, "Cover helpers must be present in the ListenBrainz section");
const ctx = vm.createContext({});
vm.runInContext(source.slice(start, stop), ctx);

const release = "9432fb06-bd84-4f2e-9386-b2f14e0de54d";
const group = "30ac1ded-c254-46ac-a41f-7453dada6ae7";
const listen = {
  track_metadata: {
    release_name: "The Marvelous Real",
    artist_name: "Sample Artist",
    mbid_mapping: {
      caa_id: 37026686379,
      caa_release_mbid: release,
      release_mbid: release,
      release_group_mbid: group
    }
  }
};
const candidate = ctx.listenCoverCandidates(listen);
assert.equal(candidate[0], `https://coverartarchive.org/release/${release}/37026686379-250.jpg`);
assert.equal(candidate.length, 3, "Duplicate release IDs should not create repeat URLs");
assert.equal(candidate[2], `https://coverartarchive.org/release-group/${group}/front-250`);
assert.equal(ctx.listenCoverCandidates({track_metadata:{additional_info:{release_mbid:"javascript:alert(1)"}}}).length, 0);
assert.equal(ctx.listenCoverCandidates({}).length, 0);

const image = {dataset: {}, src: "", alt: "", onerror: null, referrerPolicy: ""};
ctx.setListenCover(image, listen);
assert.equal(image.src, candidate[0]);
assert.equal(image.referrerPolicy, "no-referrer");
assert.match(image.alt, /The Marvelous Real/);
for (let i = 1; i <= candidate.length; i++) image.onerror();
assert.equal(image.src, "/assets/images/listenbrainz_logo.png");
assert.match(image.alt, /unavailable/);
assert.equal(image.onerror, null);
ctx.setListenCover(image, listen);
assert.equal(image.src, "/assets/images/listenbrainz_logo.png", "Unchanged listen should not reload broken covers");

const newListen = {track_metadata:{release_name:"Different Album",additional_info:{release_mbid:release}}};
ctx.setListenCover(image, newListen);
assert.equal(image.src, `https://coverartarchive.org/release/${release}/front-250`);
ctx.setListenCover(image, {});
assert.equal(image.src, "/assets/images/listenbrainz_logo.png");

const css = fs.readFileSync(path.join(root, "assets/css/style.css"), "utf8");
assert.match(css, /\.listen-entry-cover\s*\{/);
assert.match(source, /class="listen-entry-cover"/);
console.log("PASS: ListenBrainz cover-art candidates, safety, fallback and journal markup");
