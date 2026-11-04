// ======================================================
// SCHMOOKEY SITE MAIN SCRIPT
// Stable multi-page version
// Includes:
// - Reading counter
// - More Posts (temp related posts)
// - Latest updates
// - Combined activity feed
// ======================================================

/* =====================================================
   SECTION 01: HELPERS
===================================================== */

function escapeHTML(str = "") {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
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

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Failed to load ${path}`);
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

  return {
    type: item.type || "update",
    title: item.title || "Untitled update",
    url: item.url,
    date: parsedDate.toISOString(),
    summary: item.summary || "",
    readingTime: item.readingTime || null
  };
}

function normalisePostItem(item) {
  if (!item || !item.url || !item.date) return null;

  const parsedDate = new Date(item.date);
  if (isNaN(parsedDate)) return null;

  return {
    title: item.title || "Untitled post",
    url: item.url,
    date: parsedDate.toISOString(),
    summary: item.summary || "",
    readingTime: item.readingTime || null,
    section: item.section || "",
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
          <a href="${item.url}">
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

  if (!container) {
    console.warn("More posts: no related/recent posts container found");
    return;
  }

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
          <a href="${post.url}">${escapeHTML(post.title)}</a>
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
    const updates = await loadUpdatesData();
    const sorted = sortByNewest(updates).slice(0, 5);

    if (!sorted.length) {
      container.innerHTML = "<li>No updates yet.</li>";
      return;
    }

    container.innerHTML = sorted.map(update => `
      <li class="latest-update-item">
        <a href="${update.url}">${escapeHTML(update.title)}</a>
        <small>${formatFeedDate(update.date)}</small>
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

function initWebringScripts() {
  document.querySelectorAll(".webring-script").forEach(container => {
    const src = container.dataset.src;
    if (!src) return;

    if (container.querySelector(`script[src="${src}"]`)) return;

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onerror = () => console.warn("Webring failed:", src);

    container.appendChild(script);
  });
}

/* =====================================================
   SECTION 09: SMART DATES
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
   SECTION 10: WEBRING UNLOCK EFFECT
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
   SECTION 11: POST HUD
===================================================== */

function initPostHUD() {
  const timeSource = document.querySelector(".dt-published");
  const dateEl = document.getElementById("hudDate");
  const timeEl = document.getElementById("hudTime");

  if (!timeSource || !dateEl || !timeEl) return;

  const datetime = timeSource.getAttribute("datetime");
  if (!datetime) return;

  const postDate = new Date(datetime);
  if (isNaN(postDate)) return;

  dateEl.textContent = postDate.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric"
  });

  timeEl.textContent = postDate.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}

/* =====================================================
   SECTION 12: READING TIME
   Expected output IDs:
   - reading-time
===================================================== */

function initReadingTime() {
  const content = document.querySelector(".e-content");
  const output = document.getElementById("reading-time");

  if (!content) {
    console.warn("Reading time: .e-content not found");
    return;
  }

  if (!output) {
    console.warn("Reading time: #reading-time not found");
    return;
  }

  const text = (content.textContent || "").trim();
  const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
  const minutes = Math.max(1, Math.round(words / 210));

  output.textContent = `${minutes} min read`;
}

/* =====================================================
   SECTION 13: READING COUNTER / VISIT COUNTER
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
   SECTION 14: PAGE INITIALISER
===================================================== */

function initPage() {
  initWebringScripts();
  initSmartDates();
  initPostHUD();
  initReadingTime();
  initReadingCounter();

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
   SECTION 15: PWA REGISTRATION
===================================================== */

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then(() => console.log("Service Worker registered"))
      .catch(err => console.log("SW failed:", err));
  });
}