/* Article-only two-column Mega Drive layout.
 * Preserves the original banner, navigation, article, h-entry and social badges.
 * Recommendations use the local posts.json, with no tracking or third-party API.
 */
(function () {
  "use strict";
  const DATA_URL = "/assets/data/posts.json";
  const GENERIC_TAGS = new Set(["blog", "music", "update", "updates"]);
  const path = window.location.pathname;
  if (!/^\/(?:blog|music)\/posts\/[A-Za-z0-9_-]+\.html$/.test(path)) return;

  function normalise(post) {
    if (!post || typeof post.title !== "string" || typeof post.url !== "string" ||
        !/^\/(?:blog|music)\/posts\/[A-Za-z0-9_-]+\.html$/.test(post.url) ||
        !["blog", "music"].includes(post.section)) return null;
    return {
      url: post.url,
      title: typeof post.cardTitle === "string" ? post.cardTitle : post.title,
      section: post.section,
      date: Date.parse(post.date) || 0,
      tags: Array.isArray(post.tags)
        ? post.tags.map(tag => String(tag).toLocaleLowerCase("en-GB")) : []
    };
  }

  function matchingTags(a, b) {
    const tags = new Set(a.tags.filter(tag => !GENERIC_TAGS.has(tag)));
    return b.tags.filter(tag => tags.has(tag));
  }

  function moduleSection(className, heading, aria) {
    const section = document.createElement("section");
    section.className = "article-sidebar-module " + className;
    section.setAttribute("aria-label", aria);
    const title = document.createElement("h2");
    title.textContent = heading;
    section.append(title);
    const list = document.createElement("ul");
    list.className = "article-sidebar-list";
    section.append(list);
    return { section, list };
  }

  function link(post, detail) {
    const item = document.createElement("li");
    const anchor = document.createElement("a");
    anchor.href = post.url;
    anchor.textContent = post.title;
    item.append(anchor);
    if (detail) {
      const label = document.createElement("small");
      label.textContent = detail;
      item.append(label);
    }
    return item;
  }

  function showPosts(current, posts, related, more) {
    // Shared meaningful tags can match across blog and music articles.
    // Never recommend the article currently being read.
    const candidates = posts.filter(item => item.url !== current.url);
    const ranked = candidates.map(item => ({
      item,
      common: matchingTags(current, item),
      score: matchingTags(current, item).length * 12 +
        (current.section === item.section ? 2 : 0)
    })).sort((a, b) => b.score - a.score || b.item.date - a.item.date);

    // Music articles appear only when they genuinely share a topic.
    const similar = ranked.filter(pair => pair.common.length > 0)
      .slice(0, 3).map(pair => pair.item);
    // Fill remaining slots with recent blog articles if few tags overlap.
    const blogPosts = candidates.filter(item => item.section === "blog")
      .sort((a, b) => b.date - a.date);
    for (const item of blogPosts) {
      if (similar.length >= 3) break;
      if (!similar.some(other => other.url === item.url)) similar.push(item);
    }

    related.list.replaceChildren(...similar.map(item => {
      const common = matchingTags(current, item);
      const label = common.length ? common.slice(0, 2).join(" · ") :
        item.section.toUpperCase();
      return link(item, label);
    }));

    // More Posts remains a chronological list of blog articles only.
    const seen = new Set(similar.map(item => item.url));
    const recent = blogPosts.filter(item => !seen.has(item.url))
      .slice(0, 4);
    more.list.replaceChildren(...recent.map(item => link(item, "BLOG")));
    if (!similar.length) related.section.hidden = true;
    if (!recent.length) more.section.hidden = true;
  }

  async function init() {
    const article = document.querySelector("main > article.post-container.h-entry");
    const layout = article && article.closest(".layout");
    const left = layout && layout.querySelector(":scope > aside.sidebar.left");
    if (!article || !left || left.querySelector(".article-related-posts")) return;

    const related = moduleSection("article-related-posts", "RELATED POSTS", "Related articles");
    const more = moduleSection("article-more-posts", "MORE POSTS", "Other recent articles");
    related.list.append(link({ url: "/blog/", title: "Browse the blog" }));
    more.list.append(link({ url: "/blog/", title: "Browse all posts" }));

    const badges = left.querySelector(".badge-grid");
    const existingTitle = left.querySelector("h2");
    let social = null;
    if (badges) {
      social = document.createElement("section");
      social.className = "article-sidebar-module article-social-badges";
      social.setAttribute("aria-label", "Social links and 88 by 31 buttons");
      const heading = document.createElement("h2");
      heading.textContent = "SOCIALS";
      social.append(heading);
      badges.classList.add("article-badge-grid");
      social.append(badges); // move existing nodes and keep their original links
      if (existingTitle && existingTitle.textContent.trim().toUpperCase() === "SOCIALS") {
        existingTitle.remove();
      }
    }
    left.append(related.section, more.section);
    if (social) left.append(social);
    // The class is added only after the modules exist, so mobile layout remains
    // complete if scripts are disabled or data fetching fails.
    layout.classList.add("article-layout");
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error("Posts data unavailable");
      const data = await response.json();
      if (!Array.isArray(data)) throw new Error("Unexpected posts data");
      const posts = data.map(normalise).filter(Boolean);
      const current = posts.find(item => item.url === path);
      if (!current) throw new Error("Article missing from posts.json");
      showPosts(current, posts, related, more);
    } catch (_error) {
      related.section.hidden = true;
      more.list.replaceChildren(link({ url: "/blog/", title: "Browse all posts" }));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}());
