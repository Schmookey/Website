// ======================================================
// SCHMOOKEY SITE MAIN SCRIPT
// Static multi-page version
// Includes:
// - Reading counter
// - More Posts (temp related posts)
// - Latest updates
// - Combined activity feed
// - Smart dates
// - Webmentions
// - ListenBrainz widgets
// ======================================================

/* =====================================================
   SECTION 01: HELPERS
===================================================== */

function escapeHTML(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatFeedDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date)) return "Unknown date";

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
}

function sortByNewest(items = []) {
  return [...items].sort((a, b) => new Date(b.date) - new Date(a.date));
}

function getFirstExistingElement(ids = []) {
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el) return el;
  }
  return null;
}

function safeHttpUrl(value) {
  if (typeof value !== "string" || !value.trim()) return "";

  try {
    const url = new URL(value.trim(), window.location.href);
    if (url.protocol !== "http:" && url.protocol !== "https:") return "";
    if (url.username || url.password) return "";
    // Only the site's own origin may use HTTP (for local development).
    // External resources and links must use HTTPS.
    if (url.origin !== window.location.origin && url.protocol !== "https:") return "";
    return url.origin === window.location.origin
      ? `${url.pathname}${url.search}${url.hash}`
      : url.href;
  } catch {
    return "";
  }
}

async function fetchJSON(path) {
  const res = await fetch(path, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Failed to load ${path} (${res.status})`);
  }

  return res.json();
}

function safeArray(data) {
  return Array.isArray(data) ? data : [];
}

/* =====================================================
   SECTION 02: DATA NORMALISERS
===================================================== */

function normaliseActivityItem(item) {
  if (!item || !item.url || !item.date) return null;

  const parsedDate = new Date(item.date);
  if (isNaN(parsedDate)) return null;

  const safeUrl = safeHttpUrl(item.url);
  if (!safeUrl) return null;

  return {
    type: item.type || "update",
    title: item.title || "Untitled update",
    url: safeUrl,
    date: parsedDate.toISOString(),
    summary: item.summary || "",
    readingTime: item.readingTime || null
  };
}

function normalisePostItem(item) {
  if (!item || !item.url || !item.date) return null;

  const parsedDate = new Date(item.date);
  if (isNaN(parsedDate)) return null;

  const safeUrl = safeHttpUrl(item.url);
  if (!safeUrl) return null;

  return {
    title: item.title || "Untitled post",
    url: safeUrl,
    date: parsedDate.toISOString(),
    summary: item.summary || "",
    readingTime: item.readingTime || null,
    section: item.section || "post",
    tags: safeArray(item.tags)
  };
}

/* =====================================================
   SECTION 03: SITE DATA LOADERS + CACHE
===================================================== */

let SITE_DATA_CACHE = null;
let POSTS_CACHE = null;
let UPDATES_CACHE = null;

async function loadPostsData() {
  if (POSTS_CACHE) return POSTS_CACHE;

  try {
    const posts = await fetchJSON("/assets/data/posts.json");
    POSTS_CACHE = safeArray(posts).map(normalisePostItem).filter(Boolean);
    return POSTS_CACHE;
  } catch (err) {
    console.warn("Posts data error:", err);
    POSTS_CACHE = [];
    return POSTS_CACHE;
  }
}

async function loadUpdatesData() {
  if (UPDATES_CACHE) return UPDATES_CACHE;

  try {
    const updates = await fetchJSON("/assets/data/site-updates.json");
    UPDATES_CACHE = safeArray(updates).map(normaliseActivityItem).filter(Boolean);
    return UPDATES_CACHE;
  } catch (err) {
    console.warn("Updates data error:", err);
    UPDATES_CACHE = [];
    return UPDATES_CACHE;
  }
}

async function loadSiteData() {
  if (SITE_DATA_CACHE) return SITE_DATA_CACHE;

  try {
    const [updates, posts] = await Promise.all([
      loadUpdatesData(),
      loadPostsData()
    ]);

    const postUpdates = posts.map(post => ({
      type: post.section || "post",
      title: post.title,
      url: post.url,
      date: post.date,
      summary: post.summary || `Reading time: ${post.readingTime || 1} min read.`,
      readingTime: post.readingTime || null
    }));

    SITE_DATA_CACHE = [...updates, ...postUpdates]
      .map(normaliseActivityItem)
      .filter(Boolean);

    return SITE_DATA_CACHE;
  } catch (err) {
    console.warn("Site data error:", err);
    SITE_DATA_CACHE = [];
    return SITE_DATA_CACHE;
  }
}

/* =====================================================
   SECTION 04: COMBINED ACTIVITY FEED
   Expected container IDs:
   - site-updates
   - activity-feed
===================================================== */

async function loadActivityFeed() {
  const container = getFirstExistingElement([
    "site-updates",
    "activity-feed"
  ]);

  if (!container) return;

  try {
    const updates = await loadSiteData();
    const sorted = sortByNewest(updates).slice(0, 10);

    if (!sorted.length) {
      container.innerHTML = "<p>No updates yet.</p>";
      return;
    }

    container.innerHTML = sorted.map(item => `
      <article class="activity-card ${escapeHTML(item.type)}">
        <h3>
          <a href="${escapeHTML(item.url)}">
            ${escapeHTML(item.title)}
          </a>
        </h3>
        <small>
          ${formatFeedDate(item.date)}
          • ${escapeHTML((item.type || "update").toUpperCase())}
        </small>
        <p>${escapeHTML(item.summary || "")}</p>
      </article>
    `).join("");
  } catch (err) {
    console.warn("Feed failed:", err);
    container.innerHTML = "<p>Updates failed to load.</p>";
  }
}

/* =====================================================
   SECTION 05: MORE POSTS / TEMP RELATED POSTS
   Expected container IDs:
   - related-posts
   - recent-posts
   - recent-posts-list
===================================================== */

async function loadRecentPosts() {
  const container = getFirstExistingElement([
    "related-posts",
    "recent-posts",
    "recent-posts-list"
  ]);

  if (!container) return;

  try {
    const posts = await loadPostsData();
    const currentPath = window.location.pathname.replace(/\/index\.html$/, "/");

    const filtered = posts.filter(post => {
      const postPath = String(post.url || "").replace(/\/index\.html$/, "/");
      return postPath !== currentPath;
    });

    const sorted = sortByNewest(filtered).slice(0, 5);

    if (!sorted.length) {
      container.innerHTML = `<li class="related-entry">No posts yet.</li>`;
      return;
    }

    container.innerHTML = sorted.map(post => `
      <li class="related-entry">
        <h3>
          <a href="${escapeHTML(post.url)}">${escapeHTML(post.title)}</a>
        </h3>
        <small>${formatFeedDate(post.date)}</small>
      </li>
    `).join("");
  } catch (err) {
    console.warn("More posts failed:", err);
    container.innerHTML = `<li class="related-entry">More posts failed to load.</li>`;
  }
}

/* =====================================================
   SECTION 06: LATEST UPDATES
   Expected container IDs:
   - latest-updates
   - latest-updates-list
===================================================== */

async function loadLatestUpdates() {
  const container = getFirstExistingElement([
    "latest-updates",
    "latest-updates-list"
  ]);

  if (!container) return;

  try {
    const updates = await loadSiteData();
    const sorted = sortByNewest(updates).slice(0, 5);

    if (!sorted.length) {
      container.innerHTML = "<li>No updates yet.</li>";
      return;
    }

    container.innerHTML = sorted.map(update => `
      <li class="latest-update-item">
        <a href="${escapeHTML(update.url)}">${escapeHTML(update.title)}</a>
        <small>
          ${formatFeedDate(update.date)}
          • ${escapeHTML((update.type || "update").toUpperCase())}
        </small>
      </li>
    `).join("");
  } catch (err) {
    console.warn("Latest updates failed:", err);
    container.innerHTML = "<li>Latest updates failed to load.</li>";
  }
}

/* =====================================================
   SECTION 07: WEBRING SCRIPTS
===================================================== */

// Do not turn a data-src attribute into permission to execute arbitrary JS.
// The page currently uses only these providers; review this list if a ring changes.
const APPROVED_WEBRING_SCRIPTS = new Set([
  "https://dotcomboom.neocities.org/linux/ring.js",
  "https://cdring.neocities.org/cdring/onionring-variables.js",
  "https://cdring.neocities.org/cdring/onionring-widget.js"
]);

function safeApprovedScriptUrl(value) {
  if (typeof value !== "string" || !value.trim()) return "";
  try {
    const url = new URL(value.trim(), window.location.href);
    if (url.username || url.password || url.search || url.hash) return "";
    // Our own JS assets may be added in the future without editing this list.
    if (url.origin === window.location.origin && /^\/assets\/js\/[a-zA-Z0-9_-]+\.js$/.test(url.pathname)) {
      return url.pathname;
    }
    return APPROVED_WEBRING_SCRIPTS.has(url.href) ? url.href : "";
  } catch {
    return "";
  }
}

function initWebringScripts() {
  document.querySelectorAll(".webring-script").forEach(container => {
    const src = safeApprovedScriptUrl(container.dataset.src || "");
    if (!src) return;

    // DOM comparison avoids injecting untrusted text into a CSS selector.
    if (Array.from(container.querySelectorAll("script[src]"))
      .some(script => script.getAttribute("src") === src)) return;

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onerror = () => console.warn("Webring failed:", src);

    container.appendChild(script);
  });
}

/* =====================================================
   SECTION 08: SMART DATES
===================================================== */

function initSmartDates() {
  document.querySelectorAll(".auto-date").forEach(el => {
    const date = el.dataset.date ? new Date(el.dataset.date) : new Date();

    if (isNaN(date)) return;

    const formatDate = d =>
      d.toLocaleDateString("en-GB", {
        year: "numeric",
        month: "long"
      });

    const diffMonths =
      (new Date().getFullYear() - date.getFullYear()) * 12 +
      (new Date().getMonth() - date.getMonth());

    const timeAgo =
      diffMonths <= 0 ? "this month" :
      diffMonths === 1 ? "1 month ago" :
      diffMonths < 12 ? `${diffMonths} months ago` :
      `${Math.floor(diffMonths / 12)} year(s) ago`;

    el.textContent = `${formatDate(date)} (${timeAgo})`;
  });
}

/* =====================================================
   SECTION 09: WEBRING UNLOCK EFFECT
===================================================== */

window.triggerWebringUnlock = function () {
  const box = document.getElementById("webring-unlock");
  if (!box) return;

  box.classList.remove("show");
  void box.offsetWidth;
  box.classList.add("show");

  for (let i = 0; i < 18; i++) {
    const s = document.createElement("div");
    s.className = "sparkle";

    const x = (Math.random() - 0.5) * 200 + "px";
    const y = (Math.random() - 0.5) * 200 + "px";

    s.style.left = "50%";
    s.style.top = "50%";
    s.style.setProperty("--x", x);
    s.style.setProperty("--y", y);

    document.body.appendChild(s);
    setTimeout(() => s.remove(), 900);
  }
};

/* =====================================================
   SECTION 10: POST HUD
===================================================== */

function initPostHUD() {
  // HUD date and time are now written directly in the HTML.
  // No JS needed here.
}

/* =====================================================
   SECTION 11: READING TIME
   Expected output IDs:
   - reading-time
===================================================== */

function initReadingTime() {
  const content = document.querySelector(".e-content");
  const output = document.getElementById("reading-time");

  if (!content || !output) return;

  const text = (content.textContent || "").trim();
  const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
  const minutes = Math.max(1, Math.round(words / 210));

  output.textContent = `${minutes} min read`;
}

/* =====================================================
   SECTION 12: READING COUNTER / VISIT COUNTER
   Static-site safe local counter using localStorage.
   Expected output IDs:
   - reading-counter
   - read-count
   - visit-count
===================================================== */

function initReadingCounter() {
  const output = getFirstExistingElement([
    "reading-counter",
    "read-count",
    "visit-count"
  ]);

  if (!output) return;

  const pageKey = `schmookey-page-views:${window.location.pathname}`;
  let count = 0;

  try {
    count = parseInt(localStorage.getItem(pageKey) || "0", 10);
    count += 1;
    localStorage.setItem(pageKey, String(count));
  } catch (err) {
    console.warn("Reading counter unavailable:", err);
    return;
  }

  output.textContent = `${count} visit${count === 1 ? "" : "s"}`;
}

/* =====================================================
   SECTION 12B: WEBMENTIONS / FEDIVERSE REPLIES
   Expected output IDs:
   - comments-list
   - mention-count
   - wm-likes
   - wm-reposts
   - wm-replies
   - load-comments-btn
===================================================== */

function getWebmentionTarget() {
  const canonical = document.querySelector('link[rel="canonical"]')?.href;
  if (canonical) return canonical;

  const url = new URL(window.location.href);
  url.hash = "";
  url.search = "";

  if (!url.pathname.endsWith(".html")) {
    url.pathname = `${url.pathname.replace(/\/$/, "")}.html`;
  }

  return url.toString();
}

function initWebmentions() {
  const container = document.getElementById("comments-list");
  const countEl = document.getElementById("mention-count");
  const likesEl = document.getElementById("wm-likes");
  const repostsEl = document.getElementById("wm-reposts");
  const repliesEl = document.getElementById("wm-replies");
  const loadBtn = document.getElementById("load-comments-btn");

  if (!container) return;

  let isLoading = false;

  function safeHTML(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatWebmentionDate(dateString) {
    if (!dateString) return "Unknown time";

    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Unknown time";

    const datePart = date.toLocaleDateString("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric"
    });

    const timePart = date.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });

    return `${datePart} • ${timePart}`;
  }

  function getTypeLabel(property) {
    if (property === "in-reply-to") return "REPLY";
    if (property === "like-of") return "LIKE";
    if (property === "repost-of") return "BOOST";
    return "SIGNAL";
  }

  function renderMentionItem(m) {
    const property = m["wm-property"] || "";
    const author = safeHTML(m.author?.name || "Unknown traveller");
    const authorUrl = safeHttpUrl(m.author?.url || "");
    const authorPhoto = safeHttpUrl(m.author?.photo || "");
    const url = safeHttpUrl(m.url || "");
    const published = m.published || m["wm-received"] || "";
    const timestamp = formatWebmentionDate(published);
    const typeLabel = getTypeLabel(property);

    const rawText =
      m.content?.text ||
      m.content?.html ||
      (property === "like-of"
        ? "Liked this post."
        : property === "repost-of"
        ? "Boosted this post."
        : "Replied to this post.");

    const content = safeHTML(rawText);

    const avatar = authorPhoto
      ? `
        <img
          class="reply-avatar"
          src="${safeHTML(authorPhoto)}"
          alt=""
          loading="lazy"
          decoding="async"
          referrerpolicy="no-referrer"
        >
      `
      : `
        <div class="reply-avatar reply-avatar-fallback" aria-hidden="true">
          ${safeHTML(author.charAt(0).toUpperCase())}
        </div>
      `;

    const authorNameHTML = authorUrl
      ? `<a href="${safeHTML(authorUrl)}" target="_blank" rel="noopener noreferrer">${author}</a>`
      : `<span>${author}</span>`;

    const mentionActionHTML = url
      ? `<a href="${safeHTML(url)}" target="_blank" rel="noopener noreferrer">Open transmission ↗</a>`
      : `<span>Original link unavailable</span>`;

    return `
      <article class="terminal-entry" data-type="${safeHTML(typeLabel.toLowerCase())}">
        <div class="terminal-entry-head">
          <div class="terminal-entry-avatar">
            ${avatar}
          </div>

          <div class="terminal-entry-meta">
            <p class="terminal-entry-author">${authorNameHTML}</p>
            <p class="terminal-entry-system">
              <span class="entry-type">${safeHTML(typeLabel)}</span>
              <span class="entry-separator">•</span>
              <time datetime="${safeHTML(String(published))}">${safeHTML(timestamp)}</time>
            </p>
          </div>
        </div>

        <div class="terminal-entry-body">
          <p>${content}</p>
        </div>

        <div class="terminal-entry-actions">
          ${mentionActionHTML}
        </div>
      </article>
    `;
  }

  async function loadWebmentions() {
    if (isLoading) return;
    isLoading = true;

    if (loadBtn) {
      loadBtn.disabled = true;
      loadBtn.setAttribute("aria-busy", "true");
    }

    container.innerHTML = `
      <div class="terminal-log-status">
        <p>Scanning Fediverse transmissions...</p>
      </div>
    `;

    try {
      const targetUrl = getWebmentionTarget();
      const target = encodeURIComponent(targetUrl);

      console.log("Webmention target:", targetUrl);

      const res = await fetch(
        `https://webmention.io/api/mentions.jf2?target=${target}`
      );

      if (!res.ok) {
        throw new Error("Webmentions request failed");
      }

      const data = await res.json();
      const mentions = Array.isArray(data.children) ? data.children : [];

      const sortedMentions = [...mentions].sort((a, b) => {
        const aDate = new Date(a.published || a["wm-received"] || 0).getTime();
        const bDate = new Date(b.published || b["wm-received"] || 0).getTime();
        return bDate - aDate;
      });

      const visibleMentions = sortedMentions.filter(m => {
        const property = m["wm-property"];
        return (
          property === "in-reply-to" ||
          property === "repost-of" ||
          property === "like-of"
        );
      });

      let likes = 0;
      let reposts = 0;
      let replies = 0;

      visibleMentions.forEach(m => {
        const property = m["wm-property"];
        if (property === "like-of") likes++;
        if (property === "repost-of") reposts++;
        if (property === "in-reply-to") replies++;
      });

      if (countEl) {
        countEl.textContent = `${visibleMentions.length} mention${visibleMentions.length === 1 ? "" : "s"}`;
      }
      if (likesEl) likesEl.textContent = String(likes);
      if (repostsEl) repostsEl.textContent = String(reposts);
      if (repliesEl) repliesEl.textContent = String(replies);

      if (!visibleMentions.length) {
        container.innerHTML = `
          <div class="terminal-log empty-terminal-log">
            <p>No transmissions received yet.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="terminal-log">
          ${visibleMentions.map(renderMentionItem).join("")}
        </div>
      `;
    } catch (error) {
      console.warn("Webmentions failed:", error);

      if (countEl) countEl.textContent = "0 mentions";
      if (likesEl) likesEl.textContent = "0";
      if (repostsEl) repostsEl.textContent = "0";
      if (repliesEl) repliesEl.textContent = "0";

      container.innerHTML = `
        <div class="terminal-log error-terminal-log">
          <p>Transmission scan failed.</p>
        </div>
      `;
    } finally {
      isLoading = false;

      if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.removeAttribute("aria-busy");
      }
    }
  }

  if (loadBtn) {
    loadBtn.addEventListener("click", loadWebmentions);
  }

  loadWebmentions();
}

/* =====================================================
   SECTION 13: LISTENBRAINZ WIDGET (STABLE VERSION)
   - No cover art lookup
   - Always uses ListenBrainz logo
===================================================== */

function initListenBrainzWidget(username = "jon_cass") {
  const coverEl = document.getElementById("listen-cover");
  const trackEl = document.getElementById("listen-track");
  const artistEl = document.getElementById("listen-artist");
  const albumEl = document.getElementById("listen-album");
  const linkEl = document.getElementById("listen-link");

  if (!coverEl || !trackEl || !artistEl || !linkEl) return;

  const POLL_MS = 30000;
  const STATIC_COVER = "/assets/images/listenbrainz_logo.png";
  const PROFILE_URL = `https://listenbrainz.org/user/${encodeURIComponent(username)}`;

  // Always set static image
  coverEl.src = STATIC_COVER;
  coverEl.alt = "ListenBrainz logo";

  async function fetchListenJSON(url) {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`ListenBrainz request failed (${response.status})`);
    }

    return response.json();
  }

  async function getPlayingNow() {
    const url = `https://api.listenbrainz.org/1/user/${encodeURIComponent(username)}/playing-now`;
    const data = await fetchListenJSON(url);
    return data?.payload?.listens?.[0] || null;
  }

  async function getLatestListen() {
    const url = `https://api.listenbrainz.org/1/user/${encodeURIComponent(username)}/listens?count=1`;
    const data = await fetchListenJSON(url);
    return data?.payload?.listens?.[0] || null;
  }

  function renderText(listen, isNowPlaying) {
    const meta = listen?.track_metadata || {};
    const info = meta?.additional_info || {};

    const track = meta.track_name || "Unknown track";
    const artist = meta.artist_name || "Unknown artist";
    const album = meta.release_name || "Unknown release";

    trackEl.textContent = track;
    artistEl.textContent = artist;

    if (albumEl) {
      albumEl.textContent = album;
    }

    linkEl.href = PROFILE_URL;
    linkEl.textContent = isNowPlaying
      ? "ListenBrainz · Live"
      : "ListenBrainz";

    if (info.recording_mbid) {
      linkEl.href = `https://listenbrainz.org/player/?recording_mbids=${encodeURIComponent(info.recording_mbid)}`;
    }
  }

  let updateInProgress = false;

  async function updateWidget() {
    if (document.hidden || updateInProgress) return;
    updateInProgress = true;

    try {
      const playingNow = await getPlayingNow().catch(() => null);
      const listen = playingNow || await getLatestListen();
      const isNowPlaying = Boolean(playingNow);

      if (!listen) {
        trackEl.textContent = "No listens found";
        artistEl.textContent = "";
        if (albumEl) albumEl.textContent = "";

        linkEl.href = PROFILE_URL;
        linkEl.textContent = "ListenBrainz";

        return;
      }

      renderText(listen, isNowPlaying);

      // Always keep static image (no overrides)
      coverEl.src = STATIC_COVER;

    } catch (error) {
      console.warn("ListenBrainz widget error:", error);

      trackEl.textContent = "Couldn’t load music";
      artistEl.textContent = "";
      if (albumEl) albumEl.textContent = "";

      coverEl.src = STATIC_COVER;

      linkEl.href = PROFILE_URL;
      linkEl.textContent = "ListenBrainz";
    } finally {
      updateInProgress = false;
    }
  }

  updateWidget();
  setInterval(updateWidget, POLL_MS);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) updateWidget();
  });
}
/* =====================================================
   SECTION 14: LISTENING JOURNAL
   Expected IDs:
   - listening-log
   - listening-count
===================================================== */

async function loadListeningJournal(username, limit = 100) {
  const container = document.getElementById("listening-log");
  const countEl = document.getElementById("listening-count");

  if (!container) return;

  const url = `https://api.listenbrainz.org/1/user/${encodeURIComponent(username)}/listens?count=${limit}`;

  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`ListenBrainz request failed (${response.status})`);
    }

    const data = await response.json();
    const listens = Array.isArray(data?.payload?.listens) ? data.payload.listens : [];

    if (!listens.length) {
      container.innerHTML = `<p class="listening-status">No recent listens found.</p>`;
      if (countEl) countEl.textContent = "0 ENTRIES";
      return;
    }

    const seen = new Set();
    const uniqueListens = [];

    for (const listen of listens) {
      const track = (listen.track_metadata?.track_name || "Unknown track").trim();
      const artist = (listen.track_metadata?.artist_name || "Unknown artist").trim();
      const release = (listen.track_metadata?.release_name || "").trim();

      const key = `${track}::${artist}::${release}`.toLowerCase();

      if (!seen.has(key)) {
        seen.add(key);
        uniqueListens.push(listen);
      }
    }

    if (countEl) {
      countEl.textContent = `${uniqueListens.length} UNIQUE ENTRIES`;
    }

    const grouped = {};

    for (const listen of uniqueListens) {
      const listenedAt = listen.listened_at
        ? new Date(listen.listened_at * 1000)
        : null;

      const groupLabel =
        listenedAt && !isNaN(listenedAt.getTime())
          ? listenedAt.toLocaleDateString("en-GB", {
              day: "numeric",
              month: "short",
              year: "numeric"
            })
          : "Unknown Date";

      if (!grouped[groupLabel]) {
        grouped[groupLabel] = [];
      }

      grouped[groupLabel].push(listen);
    }

    const sortedGroups = Object.entries(grouped).sort((a, b) => {
      const aDate = new Date(a[1][0]?.listened_at ? a[1][0].listened_at * 1000 : 0).getTime();
      const bDate = new Date(b[1][0]?.listened_at ? b[1][0].listened_at * 1000 : 0).getTime();
      return bDate - aDate;
    });

    const html = sortedGroups.map(([dateLabel, entries]) => {
      const sortedEntries = [...entries].sort((a, b) => {
        const aTime = a.listened_at || 0;
        const bTime = b.listened_at || 0;
        return bTime - aTime;
      });

      const entriesHtml = sortedEntries.map(listen => {
        const track = listen.track_metadata?.track_name || "Unknown track";
        const artist = listen.track_metadata?.artist_name || "Unknown artist";
        const release = listen.track_metadata?.release_name || "Unknown release";

        const listenedAt = listen.listened_at
          ? new Date(listen.listened_at * 1000)
          : null;

        const timeFormatted =
          listenedAt && !isNaN(listenedAt.getTime())
            ? listenedAt.toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit"
              })
            : "Unknown time";

        return `
          <article class="listen-entry">
            <div class="listen-entry-header">
              <h3 class="listen-entry-title">${escapeHTML(track)}</h3>
              <span class="listen-entry-time">${escapeHTML(timeFormatted)}</span>
            </div>
            <div class="listen-entry-meta">
              <span><strong class="listen-label">Artist:</strong> ${escapeHTML(artist)}</span>
              <span><strong class="listen-label">Release:</strong> ${escapeHTML(release)}</span>
            </div>
          </article>
        `;
      }).join("");

      return `
        <section class="listen-day-group">
          <h2 class="listen-day-heading">${escapeHTML(dateLabel)}</h2>
          <div class="listen-day-entries">
            ${entriesHtml}
          </div>
        </section>
      `;
    }).join("");

    container.innerHTML = html;
  } catch (error) {
    console.warn("Listening journal error:", error);
    container.innerHTML = `<p class="listening-status">Failed to load listening journal.</p>`;
    if (countEl) countEl.textContent = "ERROR";
  }
}

/* =====================================================
   SECTION 15: PAGE INITIALISER
===================================================== */

function initPage() {
  initWebringScripts();
  initSmartDates();
  initPostHUD();
  initReadingTime();
  initReadingCounter();
  initWebmentions();

  initListenBrainzWidget("jon_cass");
  loadListeningJournal("jon_cass", 100);

  loadActivityFeed();
  loadRecentPosts();
  loadLatestUpdates();
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("MAIN.JS LOADED");
  initPage();
});

window.SCHMOOKEY_initPage = initPage;

/* =====================================================
   BOOKWYRM / NOW READING (LOCAL JSON VERSION)
===================================================== */

(async function () {
  const isAboutPage =
    window.location.pathname === "/about" ||
    window.location.pathname === "/about/" ||
    window.location.pathname.endsWith("/about.html");

  if (!isAboutPage) return;

  const widget = document.getElementById("bookwyrm-now-reading");
  if (!widget) return;

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, m => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[m]));
  }

  try {
    const response = await fetch("/assets/data/now-reading.json", {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`Could not load local reading data (${response.status})`);
    }

    const book = await response.json();

    if (!book || !book.title) {
      widget.innerHTML = `
        <p class="bookwyrm-status">No current read found.</p>
      `;
      return;
    }

    const bookLink = safeHttpUrl(book.link) || "https://bookwyrm.social/";
    const bookCover = safeHttpUrl(book.cover || "");

    widget.innerHTML = `
      ${bookCover ? `
        <img
          class="bookwyrm-cover"
          src="${escapeHtml(bookCover)}"
          alt="Cover of ${escapeHtml(book.title)}"
          loading="lazy"
        >
      ` : ""}
      <div class="bookwyrm-info">
        <p class="bookwyrm-label">CURRENTLY READING</p>
        <h3 class="bookwyrm-title">
          <a href="${escapeHtml(bookLink)}" rel="noopener noreferrer">
            ${escapeHtml(book.title)}
          </a>
        </h3>
        ${book.author ? `<p class="bookwyrm-author">by ${escapeHtml(book.author)}</p>` : ""}
        ${book.updated ? `<p class="bookwyrm-date">Updated: ${escapeHtml(book.updated)}</p>` : ""}
      </div>
    `;
  } catch (error) {
    console.error("BookWyrm widget error:", error);
    widget.innerHTML = `
      <p class="bookwyrm-status">Couldn’t load reading data right now.</p>
      <p class="bookwyrm-status">${escapeHtml(error.message || "Unknown error")}</p>
    `;
  }
})();

/* =====================================================
   TRAKT / CURRENTLY WATCHING
===================================================== */

(async function () {
  const isAboutPage =
    window.location.pathname === "/about" ||
    window.location.pathname === "/about/" ||
    window.location.pathname.endsWith("/about.html");

  if (!isAboutPage) return;

  const widget = document.getElementById("trakt-widget");
  if (!widget) return;

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, m => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[m]));
  }

  try {
    const response = await fetch("/assets/data/last-watched.json", {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`Could not load Trakt data (${response.status})`);
    }

    const item = await response.json();

    if (!item || !item.title) {
      widget.innerHTML = `
        <p class="trakt-status">Nothing currently watching.</p>
      `;
      return;
    }

    const metaParts = [];

    if (item.season) metaParts.push(`Season ${item.season}`);
    if (item.type) metaParts.push(item.type);
    if (item.year) metaParts.push(String(item.year));

    const traktLink = safeHttpUrl(item.link) || "https://trakt.tv/";
    const traktCover = safeHttpUrl(item.cover || "");

    widget.innerHTML = `
      ${traktCover ? `
        <img
          class="trakt-cover"
          src="${escapeHtml(traktCover)}"
          alt="Poster for ${escapeHtml(item.title)}"
          loading="lazy"
        >
      ` : ""}
      <div class="trakt-info">
        <p class="trakt-label">CURRENTLY WATCHING</p>
        <h3 class="trakt-title">
          <a href="${escapeHtml(traktLink)}" rel="noopener noreferrer">
            ${escapeHtml(item.title)}
          </a>
        </h3>
        ${metaParts.length ? `<p class="trakt-meta">${escapeHtml(metaParts.join(" • "))}</p>` : ""}
        ${item.updated ? `<p class="trakt-date">Updated: ${escapeHtml(item.updated)}</p>` : ""}
      </div>
    `;
  } catch (error) {
    console.error("Trakt widget error:", error);
    widget.innerHTML = `
      <p class="trakt-status">Couldn’t load Trakt data right now.</p>
      <p class="trakt-status">${escapeHtml(error.message || "Unknown error")}</p>
    `;
  }
})();

