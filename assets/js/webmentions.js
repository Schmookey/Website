// =============================
// WEBMENTIONS (Neocities SAFE)
// =============================

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("webmentions");
  const countEl = document.getElementById("mention-count");
  const likesEl = document.getElementById("wm-likes");
  const repostsEl = document.getElementById("wm-reposts");
  const repliesEl = document.getElementById("wm-replies");

  if (!container) return;

  const escapeHTML = (str = "") =>
    str
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  try {
    const target = encodeURIComponent(window.location.href);

    const res = await fetch(
      `https://webmention.io/api/mentions.jf2?target=${target}`
    );

    if (!res.ok) throw new Error("Webmentions failed");

    const data = await res.json();
    const mentions = data.children || [];

    if (countEl) countEl.textContent = String(mentions.length);

    let likes = 0;
    let reposts = 0;
    let replies = 0;

    mentions.forEach(m => {
      const property = m["wm-property"];
      if (property === "like-of") likes++;
      if (property === "repost-of") reposts++;
      if (property === "in-reply-to") replies++;
    });

    if (likesEl) likesEl.textContent = `${likes}`;
    if (repostsEl) repostsEl.textContent = `${reposts}`;
    if (repliesEl) repliesEl.textContent = `${replies}`;

    const replyHTML = mentions
      .filter(m => m["wm-property"] === "in-reply-to")
      .map(m => {
        const author = escapeHTML(m.author?.name || "Someone");
        const content = escapeHTML(m.content?.text || "mentioned this post.");
        const url = m.url || "#";

        return `
          <article class="webmention">
            <p><strong>${author}</strong></p>
            <p>${content}</p>
            <p><a href="${url}" target="_blank" rel="noopener noreferrer">View reply ↗</a></p>
          </article>
        `;
      })
      .join("");

    container.innerHTML = replyHTML || "<p>No replies yet.</p>";
  } catch (err) {
    console.warn("Webmentions failed:", err);
    container.innerHTML = "<p>Webmentions failed to load.</p>";
  }
});
