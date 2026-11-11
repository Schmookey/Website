/* Shared ListenBrainz "Now Playing / Last Played" card.
 * Public browser-side API: no token, GitHub Actions or server-side code required.
 * Safe textContent rendering; artwork is restricted to Cover Art Archive MBIDs.
 */
(function () {
  "use strict";

  const USERNAME = "jon_cass";
  const PROFILE = "https://listenbrainz.org/user/" + encodeURIComponent(USERNAME);
  const API = "https://api.listenbrainz.org/1/user/" + encodeURIComponent(USERNAME);
  const FALLBACK_COVER = "/assets/images/listenbrainz_logo.png";
  const REFRESH_MS = 60000;
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  function validUuid(value) {
    return typeof value === "string" && UUID_RE.test(value) ? value.toLowerCase() : "";
  }

  function getCoverUrl(listen) {
    const metadata = listen?.track_metadata || {};
    const mapping = metadata.mbid_mapping || listen?.mbid_mapping || {};
    const additional = metadata.additional_info || {};
    const release = validUuid(
      mapping.caa_release_mbid || mapping.release_mbid || additional.release_mbid
    );
    if (release) return "https://coverartarchive.org/release/" + release + "/front-250";
    const releaseGroup = validUuid(mapping.release_group_mbid || additional.release_group_mbid);
    if (releaseGroup) return "https://coverartarchive.org/release-group/" + releaseGroup + "/front-250";
    return "";
  }

  function normaliseListen(listen, playingNow) {
    if (!listen || typeof listen !== "object" || !listen.track_metadata) return null;
    const metadata = listen.track_metadata;
    const text = (value, fallback) =>
      typeof value === "string" && value.trim() ? value.trim() : fallback;
    const unixTime = Number(listen.listened_at);
    const date = Number.isFinite(unixTime) && unixTime > 0
      ? new Date(unixTime * 1000) : null;
    return {
      track: text(metadata.track_name, "Unknown track"),
      artist: text(metadata.artist_name, "Unknown artist"),
      album: text(metadata.release_name, "Unknown release"),
      playingNow: Boolean(playingNow),
      timestamp: date && !Number.isNaN(date.getTime()) ? date : null,
      coverUrl: getCoverUrl(listen)
    };
  }

  function updateArtwork(image, info) {
    if (!image) return;
    const desired = info?.coverUrl || FALLBACK_COVER;
    const coverAlt = info?.coverUrl
      ? "Cover artwork for " + info.album
      : "ListenBrainz logo";
    image.alt = coverAlt;
    if (image.dataset.currentCover === desired) return;
    image.dataset.currentCover = desired;
    image.onerror = function () {
      image.onerror = null;
      image.dataset.currentCover = FALLBACK_COVER;
      image.src = FALLBACK_COVER;
      image.alt = "ListenBrainz logo";
    };
    image.src = desired;
  }

  function renderCard(root, info, failed) {
    const field = name => root.querySelector("[data-listen-" + name + "]");
    const state = field("state");
    const track = field("track");
    const artist = field("artist");
    const album = field("album");
    const time = field("time");
    const link = field("link");

    if (state) {
      state.textContent = failed ? "UNAVAILABLE" : info?.playingNow ? "LIVE" : "LAST PLAYED";
      state.dataset.status = failed ? "error" : info?.playingNow ? "live" : "previous";
    }
    if (track) track.textContent = info?.track || (failed ? "ListenBrainz unavailable" : "No recent listens");
    if (artist) artist.textContent = info?.artist || "";
    if (album) album.textContent = info?.album || "";
    if (time) {
      time.textContent = info?.playingNow ? "Playing now" : info?.timestamp
        ? "Listened " + info.timestamp.toLocaleString("en-GB", {
            day: "numeric", month: "short", year: "numeric",
            hour: "2-digit", minute: "2-digit"
          }) : "";
      if (info?.timestamp && !info.playingNow) {
        time.setAttribute("datetime", info.timestamp.toISOString());
      } else {
        time.removeAttribute("datetime");
      }
    }
    if (link) {
      link.href = PROFILE;
      link.textContent = "View on ListenBrainz";
    }
    updateArtwork(field("cover"), info);
  }

  async function getListen(path) {
    const response = await fetch(API + path, {
      headers: { Accept: "application/json" },
      cache: "no-store"
    });
    if (!response.ok) throw new Error("ListenBrainz returned HTTP " + response.status);
    const data = await response.json();
    return Array.isArray(data?.payload?.listens) ? data.payload.listens[0] || null : null;
  }

  function start() {
    const cards = Array.from(document.querySelectorAll("[data-listenbrainz-feature]"));
    if (!cards.length) return;

    let active = false;
    let lastUpdated = 0;
    async function refresh() {
      if (document.hidden || active || Date.now() - lastUpdated < 15000) return;
      active = true;
      lastUpdated = Date.now();
      try {
        // A real playing-now response has priority. Never label an old listen "live".
        const live = await getListen("/playing-now").catch(() => null);
        const latest = live || await getListen("/listens?count=1");
        const info = normaliseListen(latest, Boolean(live));
        cards.forEach(card => renderCard(card, info, false));
      } catch (error) {
        console.warn("ListenBrainz embed:", error);
        cards.forEach(card => renderCard(card, null, true));
      } finally {
        active = false;
      }
    }
    refresh();
    window.setInterval(refresh, REFRESH_MS);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { validUuid, getCoverUrl, normaliseListen };
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", start);
    } else {
      start();
    }
  }
}());
