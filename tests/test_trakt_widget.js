"use strict";
const assert = require("node:assert/strict");
const widget = require("../assets/js/trakt-history.js");
// The URL is copied from the owner’s actual Trakt account, not a guessed slug.
assert.equal(widget.allowedLink(""), "https://app.trakt.tv/profile/Pati3nt_Z3ro");

assert.equal(widget.allowedLink("javascript:alert(1)"), "https://app.trakt.tv/profile/Pati3nt_Z3ro");
assert.equal(widget.allowedLink("https://evil.example/test"), "https://app.trakt.tv/profile/Pati3nt_Z3ro");
assert.equal(widget.allowedLink("https://trakt.tv/shows/the-sopranos"), "https://trakt.tv/shows/the-sopranos");
assert.equal(widget.allowedLink("https://trakt.tv.evil.example"), "https://app.trakt.tv/profile/Pati3nt_Z3ro");
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
// Refreshes automatically from public GitHub data, falling back to the
// existing Neocities JSON. No Trakt or TMDB token is sent to the browser.
(async () => {
  const realFetch = global.fetch;
  const remote = "https://raw.githubusercontent.com/Schmookey/Website/main/assets/data/trakt-history.json";
  const local = "/assets/data/trakt-history.json";
  const makeResponse = (iso, title) => ({
    ok: true, json: async () => ({
      generated_at: iso, items: [{title, type: "TV Show"}]
    })
  });
  try {
    const remoteCalls = [];
    global.fetch = async (url, opts) => {
      remoteCalls.push({url, opts});
      if (url !== remote) throw new Error("Unexpected secondary request");
      return makeResponse("2026-11-13T06:43:23Z", "Fresh GitHub watch");
    };
    const liveItems = await widget.loadSnapshot();
    assert.equal(liveItems[0].title, "Fresh GitHub watch");
    assert.equal(remoteCalls.length, 1);
    assert.equal(remoteCalls[0].opts.credentials, "omit");
    assert.equal(remoteCalls[0].opts.cache, "no-store");

    const fallbackCalls = [];
    global.fetch = async (url) => {
      fallbackCalls.push(url);
      if (url === remote) throw new Error("Network or CORS failure");
      assert.equal(url, local);
      return makeResponse("2026-11-12T15:30:06Z", "Saved Neocities watch");
    };
    const fallbackItems = await widget.loadSnapshot();
    assert.equal(fallbackItems[0].title, "Saved Neocities watch");
    assert.deepEqual(fallbackCalls, [remote,local]);

    const badRemoteCalls = [];
    global.fetch = async (url) => {
      badRemoteCalls.push(url);
      if (url === remote) return {ok: true, json: async () => ({generated_at:null, items:[]})};
      return makeResponse("2026-11-12T15:30:06Z", "Valid local watch");
    };
    assert.equal((await widget.loadSnapshot())[0].title,"Valid local watch");
    assert.deepEqual(badRemoteCalls,[remote,local]);
  } finally {
    global.fetch = realFetch;
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
// Keep the About card aligned with the shared ListenBrainz/BookWyrm styles.
const fs = require("node:fs");
const path = require("node:path");
const about = fs.readFileSync(path.join(__dirname, "..", "about.html"), "utf8");
const css = fs.readFileSync(path.join(__dirname, "..", "assets/css/style.css"), "utf8");
assert.match(about, /id="trakt-latest-card"[\s\S]*class="media-card trakt-about-card h-entry"/);
assert.match(about, /class="media-label">Last Watched/);
assert.match(about, /class="media-title p-name">\s*<a class="u-watch-of"/);
assert.match(about, /TRAKT_MF2_START:[\s\S]*TRAKT_MF2_END/);
assert.match(css, /\.trakt-live-widget \.trakt-about-card \.media-title\s*\{\s*font-size: 12px/);
assert.match(css, /\.trakt-live-widget \.trakt-about-card \.media-label\s*\{\s*font-size: 11px/);

// About sidebar visual consistency: one font scale and no underlined links.
assert.match(css, /\.sidebar\.right \.media-widget \.media-meta \.media-label\s*\{\s*font-size: 11px/);
assert.match(css, /\.sidebar\.right \.media-widget \.media-meta \.media-title\s*\{\s*font-size: 12px/);
assert.match(css, /\.sidebar\.right #latest-listen #listen-link\s*\{\s*white-space: nowrap/);
assert.match(css, /\.sidebar\.right \.trakt-live-widget \.trakt-live-links\s*\{\s*margin: 6px 0 0 64px/);
assert.match(css, /\.sidebar\.right \.trakt-live-widget \.trakt-about-card \.media-title a:hover[\s\S]*?text-decoration: none;/);

console.log("PASS: Trakt widget URL allowlists and metadata tests");
