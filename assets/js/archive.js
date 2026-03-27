// ======================================================
// SCHMOOKEY ARCHIVE SCRIPT
// Handles archive pages using posts.json
// Filters by data-section on #archive-list
// Examples:
//   <div id="archive-list" data-section="blog"></div>
//   <div id="archive-list" data-section="music"></div>
//   <div id="archive-list"></div>  // all posts
// ======================================================

function escapeHTML(str = "") {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatArchiveDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date)) return "Unknown date";

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric"
  });
}

function normaliseArchivePost(post) {
  if (!post || !post.url || !post.date) return null;

  const parsedDate = new Date(post.date);
  if (isNaN(parsedDate)) return null;

  return {
    title: post.title || "Untitled post",
    url: post.url,
    date: parsedDate.toISOString(),
    readingTime: Number(post.readingTime || 1),
    section: String(post.section || "").toLowerCase(),
    tags: Array.isArray(post.tags) ? post.tags : [],
    summary: post.summary || ""
  };
}

async function loadArchive() {
  const container = document.getElementById("archive-list");
  if (!container) return;

  const section = String(container.dataset.section || "").toLowerCase();

  try {
    const res = await fetch("/assets/data/posts.json");
    if (!res.ok) throw new Error("Posts failed to load");

    const rawPosts = await res.json();
    const posts = Array.isArray(rawPosts)
      ? rawPosts.map(normaliseArchivePost).filter(Boolean)
      : [];

    container.innerHTML = "";

    const filteredPosts = posts
      .filter(post => {
        if (!section) return true;
        return post.section === section;
      })
      .sort((a, b) => new Date(b.date) - new Date(a.date));

    if (!filteredPosts.length) {
      container.innerHTML = "<p>No posts found.</p>";
      return;
    }

    filteredPosts.forEach(post => {
      const el = document.createElement("article");
      el.className = "archive-entry h-entry";

      const formattedDate = formatArchiveDate(post.date);

      el.innerHTML = `
        <h2 class="p-name">
          <a class="u-url" href="${escapeHTML(post.url)}">
            ${escapeHTML(post.title)}
          </a>
        </h2>

        <time class="dt-published" datetime="${escapeHTML(post.date)}">
          ${formattedDate}
        </time>

        <span class="reading-time">
          ⏱ ${escapeHTML(post.readingTime)} min read
        </span>

        ${post.tags.length ? `
          <p class="archive-tags">
            ${escapeHTML(post.tags.join(" • "))}
          </p>
        ` : ""}
      `;

      container.appendChild(el);
    });
  } catch (err) {
    console.warn("Archive failed:", err);
    container.innerHTML = "<p>Archive failed to load.</p>";
  }
}

document.addEventListener("DOMContentLoaded", loadArchive);