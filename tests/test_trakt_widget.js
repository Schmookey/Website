"use strict";
const assert = require("node:assert/strict");
const widget = require("../assets/js/trakt-history.js");

assert.equal(widget.allowedLink("javascript:alert(1)"), "https://trakt.tv/users/pat13nt_z3r0");
assert.equal(widget.allowedLink("https://evil.example/test"), "https://trakt.tv/users/pat13nt_z3r0");
assert.equal(widget.allowedLink("https://trakt.tv/shows/the-sopranos"), "https://trakt.tv/shows/the-sopranos");
assert.equal(widget.allowedLink("https://trakt.tv.evil.example"), "https://trakt.tv/users/pat13nt_z3r0");
assert.equal(widget.allowedPoster("javascript:alert(1)"), "");
assert.equal(widget.allowedPoster("https://evil.example/poster.jpg"), "");
assert.equal(widget.allowedPoster("/assets/images/trakt/the-sopranos.jpg"), "/assets/images/trakt/the-sopranos.jpg");
assert.equal(widget.allowedPoster("https://image.tmdb.org/t/p/w200/abc.jpg"), "https://image.tmdb.org/t/p/w200/abc.jpg");
assert.equal(widget.normalise({}), null);
assert.equal(widget.normalise({title:"<script>alert(1)</script>",type:"TV Show",season:1,episode_number:2}).title, "<script>alert(1)</script>");
assert.equal(widget.normalise({title:"Test",type:"Movie",watched_at:"2026-11-11T12:00:00Z"}).date.toISOString(), "2026-11-11T12:00:00.000Z");
assert.deepEqual(widget.snapshotEntries({generated_at:null,items:[{title:"Old sample",type:"TV Show"}]}), []);
assert.deepEqual(widget.snapshotEntries({generated_at:"",items:[{title:"Old sample",type:"TV Show"}]}), []);
const recent = widget.snapshotEntries({generated_at:"2026-11-11T14:00:00Z",items:[{title:"New watch",type:"Movie"}]});
assert.equal(recent.length, 1);
assert.equal(recent[0].title, "New watch");
// Keep the About card aligned with the shared ListenBrainz/BookWyrm styles.
const fs = require("node:fs");
const path = require("node:path");
const about = fs.readFileSync(path.join(__dirname, "..", "about.html"), "utf8");
const css = fs.readFileSync(path.join(__dirname, "..", "assets/css/style.css"), "utf8");
assert.match(about, /id="trakt-latest-card"[\s\S]*class="media-card trakt-about-card trakt-pending"/);
assert.match(about, /class="media-label">Last Watched/);
assert.match(about, /class="media-title">Coming Soon/);
assert.match(css, /\.trakt-live-widget \.trakt-about-card \.media-title\s*\{\s*font-size: 12px/);
assert.match(css, /\.trakt-live-widget \.trakt-about-card \.media-label\s*\{\s*font-size: 11px/);

console.log("PASS: Trakt widget URL allowlists and metadata tests");
