/* Schmookey local site search. No external service, telemetry or cookies. */
(function () {
  "use strict";
  const INDEX_URL = "/assets/data/search-index.json";
  const SEARCH_URL = "/search.html";
  const LIMIT = 6;
  let indexPromise;

  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(INDEX_URL, { cache: "no-store" }).then(response => {
        if (!response.ok) throw new Error("Local search data unavailable");
        return response.json();
      }).then(data => {
        if (!data || !Array.isArray(data.items)) throw new Error("Invalid search data");
        return data.items.filter(item =>
          item && /^\/(?:blog|music)\/posts\/[a-zA-Z0-9_-]+\.html$/.test(item.url) &&
          (item.section === "blog" || item.section === "music") &&
          typeof item.title === "string" && typeof item.text === "string"
        );
      });
    }
    return indexPromise;
  }

  function tokens(query) {
    return String(query || "").toLocaleLowerCase("en-GB")
      .trim().split(/\s+/).filter(Boolean).slice(0, 10);
  }

  function score(item, words) {
    if (!words.length) return 0;
    const title = (item.title || "").toLocaleLowerCase("en-GB");
    const summary = (item.summary || "").toLocaleLowerCase("en-GB");
    const tags = (item.tags || []).join(" ").toLocaleLowerCase("en-GB");
    const body = (item.text || "").toLocaleLowerCase("en-GB");
    if (!words.every(word => [title, summary, tags, body].some(field => field.includes(word)))) return 0;
    return words.reduce((sum, word) => sum +
      (title.includes(word) ? 24 : 0) +
      (tags.includes(word) ? 12 : 0) +
      (summary.includes(word) ? 8 : 0) +
      (body.includes(word) ? 2 : 0), 0);
  }

  function rank(items, query, section) {
    const words = tokens(query);
    if (!words.length) return [];
    return items.filter(item => item.section === "blog" || item.section === "music")
      .map(item => ({ item, relevance: score(item, words) }))
      .filter(result => result.relevance > 0)
      .sort((a, b) => b.relevance - a.relevance ||
        (Date.parse(b.item.date || 0) || 0) - (Date.parse(a.item.date || 0) || 0))
      .map(result => result.item);
  }

  function excerpt(item, query) {
    const value = String(item.text || item.summary || "");
    const firstWord = tokens(query)[0];
    const found = firstWord ? value.toLocaleLowerCase("en-GB").indexOf(firstWord) : -1;
    const start = Math.max(0, found - 75);
    const part = value.slice(start, start + 260).trim();
    return (start ? "…" : "") + part + (start + 260 < value.length ? "…" : "");
  }

  function highlighted(text, query) {
    const fragment = document.createDocumentFragment();
    const value = String(text || "");
    const words = tokens(query).sort((a, b) => b.length - a.length);
    if (!words.length) { fragment.append(document.createTextNode(value)); return fragment; }
    const low = value.toLocaleLowerCase("en-GB");
    let cursor = 0;
    while (cursor < value.length) {
      let best = -1, length = 0;
      for (const word of words) {
        const pos = low.indexOf(word, cursor);
        if (pos !== -1 && (best < 0 || pos < best || (pos === best && word.length > length))) {
          best = pos; length = word.length;
        }
      }
      if (best < 0) { fragment.append(document.createTextNode(value.slice(cursor))); break; }
      if (best > cursor) fragment.append(document.createTextNode(value.slice(cursor, best)));
      const mark = document.createElement("mark");
      mark.textContent = value.slice(best, best + length);
      fragment.append(mark);
      cursor = best + length;
    }
    return fragment;
  }

  function resultRow(item, query, compact) {
    const entry = document.createElement(compact ? "li" : "article");
    entry.className = compact ? "site-search-suggestion" : "site-search-result";
    const link = document.createElement("a");
    link.href = item.url;
    link.append(highlighted(item.title, query));
    entry.append(link);
    const meta = document.createElement("span");
    meta.className = "site-search-category";
    meta.textContent = item.section === "music" ? "Music" : "Blog";
    entry.append(meta);
    if (!compact) {
      const excerptEl = document.createElement("p");
      excerptEl.append(highlighted(excerpt(item, query), query));
      entry.append(excerptEl);
    }
    return entry;
  }

  function createSidebarSearch() {
    const sidebar = document.querySelector("aside.sidebar.left");
    if (!sidebar) return;
    const existing = sidebar.querySelector(".site-search-widget");
    if (existing && existing.dataset.searchReady === "true") return;
    const widget = existing || document.createElement("section");
    if (!existing) {
      widget.className = "site-search-widget";
      widget.setAttribute("role", "search");
      widget.innerHTML =
      '<form class="site-search-form" action="/search.html" method="get">' +
      '<label for="site-search-input">SEARCH</label>' +
      '<div class="site-search-controls">' +
      '<input id="site-search-input" name="q" type="search" autocomplete="off" ' +
      'maxlength="160" placeholder="Search" aria-controls="site-search-suggestions" ' +
      'aria-expanded="false" aria-autocomplete="list">' +
      '<button type="submit" aria-label="Search website">SEARCH</button></div></form>' +
      '<ul id="site-search-suggestions" class="site-search-suggestions" hidden></ul>' +
      '<p class="site-search-status visually-hidden" role="status" aria-live="polite"></p>';
      sidebar.insertBefore(widget, sidebar.firstChild);
    }
    widget.dataset.searchReady = "true";
    const input = widget.querySelector("input");
    const list = widget.querySelector(".site-search-suggestions");
    const status = widget.querySelector(".site-search-status");
    let generation = 0;
    let active = -1;
    const close = () => {
      list.hidden = true; list.replaceChildren(); active = -1;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    };
    async function update() {
      const current = ++generation;
      const value = input.value.trim();
      if (value.length < 2) { close(); return; }
      try {
        const found = rank(await loadIndex(), value, "all").slice(0, LIMIT);
        if (current !== generation || document.activeElement !== input) return;
        list.replaceChildren(...found.map((item, i) => {
          const row = resultRow(item, value, true);
          row.id = "site-search-choice-" + i;
          return row;
        }));
        if (found.length) {
          const more = document.createElement("li");
          more.className = "site-search-all";
          const a = document.createElement("a");
          a.href = SEARCH_URL + "?q=" + encodeURIComponent(value);
          a.textContent = "All results";
          more.append(a); list.append(more);
        } else {
          const empty = document.createElement("li");
          empty.textContent = "No matching articles";
          list.append(empty);
        }
        list.hidden = false;
        input.setAttribute("aria-expanded", "true");
        status.textContent = found.length + (found.length === 1 ? " suggestion" : " suggestions");
      } catch (_error) {
        if (current === generation) { close(); status.textContent = "Search is temporarily unavailable."; }
      }
    }
    input.addEventListener("input", update);
    input.addEventListener("focus", update);
    input.addEventListener("keydown", event => {
      if (event.key === "Escape") { close(); return; }
      if (list.hidden) return;
      const links = [...list.querySelectorAll("a")];
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        active = event.key === "ArrowDown" ?
          (active + 1) % links.length : (active - 1 + links.length) % links.length;
        links.forEach((a, i) => a.classList.toggle("site-search-active", i === active));
        input.setAttribute("aria-activedescendant", links[active].parentElement.id || "");
      } else if (event.key === "Enter" && active >= 0 && links[active]) {
        event.preventDefault();
        window.location.assign(links[active].href);
      }
    });
    widget.addEventListener("focusout", () => {
      window.setTimeout(() => {
        if (!widget.contains(document.activeElement)) close();
      }, 100);
    });
    const query = new URLSearchParams(window.location.search).get("q");
    if (window.location.pathname.endsWith("/search.html") && query) input.value = query;
  }

  function createResultPage() {
    const region = document.getElementById("site-search-results");
    if (!region) return;
    const heading = document.getElementById("site-search-heading");
    const field = document.getElementById("site-search-page-query");
    const params = new URLSearchParams(window.location.search);
    const q = (params.get("q") || "").slice(0, 160);
    field.value = q;
    let request = 0;
    async function render() {
      const id = ++request;
      const query = field.value.trim();
      const url = new URL(window.location.href);
      if (query) url.searchParams.set("q", query); else url.searchParams.delete("q");
      url.searchParams.delete("section");
      window.history.replaceState(null, "", url);
      region.replaceChildren();
      if (!query) { heading.textContent = "Search articles"; region.textContent = "Enter a word or phrase to search blog or music posts."; return; }
      heading.textContent = 'Results for “' + query + '”';
      region.textContent = "Searching locally…";
      try {
        const found = rank(await loadIndex(), query, "all");
        if (id !== request) return;
        heading.textContent = found.length + (found.length === 1 ? " result" : " results") + ' for “' + query + '”';
        region.replaceChildren(...found.map(item => resultRow(item, query, false)));
        if (!found.length) region.textContent = "No matching articles. Try another word or phrase.";
      } catch (_error) {
        if (id === request) region.textContent = "Search data could not be loaded. Please try again.";
      }
    }
    const form = document.getElementById("site-search-page-form");
    form.addEventListener("submit", event => { event.preventDefault(); render(); });
    render();
  }

  function start() { createSidebarSearch(); createResultPage(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
}());
