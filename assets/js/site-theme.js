/* Schmookey: optional SNES light palette. Existing Mega Drive styling stays
 * byte-for-byte the default when the theme is not selected. */
(() => {
  "use strict";

  const KEY = "schmookey-theme-v1";
  const ATTR = "data-schmookey-theme";
  const CSS = "/assets/css/snes-light-theme.css";
  const doc = document.documentElement;

  function readTheme() {
    try {
      return localStorage.getItem(KEY) === "light" ? "light" : "dark";
    } catch {
      // The site still works when storage is blocked/private.
      return "dark";
    }
  }

  function saveTheme(theme) {
    try { localStorage.setItem(KEY, theme); } catch { /* storage unavailable */ }
  }

  function applyTheme(theme, button) {
    const selected = theme === "light" ? "light" : "dark";
    doc.setAttribute(ATTR, selected);
    if (!button) return;
    button.setAttribute("aria-pressed", selected === "light" ? "true" : "false");
    const other = selected === "light" ? "dark" : "light";
    button.setAttribute("aria-label", "Switch to " + other + " mode");
    button.setAttribute("title", "Switch to " + other + " mode");
    button.innerHTML = selected === "light" ? SUN_ICON : MOON_ICON;
  }

  // Original pixel artwork, not emoji or a network-dependent icon font.
  const SUN_ICON = `<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <path fill="#b35b00" d="M11 1h2v4h-2zM11 19h2v4h-2zM1 11h4v2H1zM19 11h4v2h-4zM4 4h2v2H4zM18 4h2v2h-2zM4 18h2v2H4zM18 18h2v2h-2z"/>
    <path fill="#ffbf13" d="M9 6h6v2h2v2h2v4h-2v2h-2v2H9v-2H7v-2H5v-4h2V8h2z"/>
    <path fill="#ffe56b" d="M9 9h6v5H9z"/>
  </svg>`;
  const MOON_ICON = `<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <path fill="#dfe8ff" d="M9 2h4v2H9zM7 4h3v2H7zM5 6h3v3H5zM3 9h3v6H3zM5 15h3v3H5zM7 18h3v2H7zM10 20h6v2h-6zM16 18h3v2h-3zM19 15h2v3h-2zM18 13h2v2h-2zM12 11h7v2h-7zM10 8h6v3h-6zM9 6h4v2H9z"/>
    <path fill="#ffffff" d="M5 9h3v6H5zM7 15h3v3H7zM10 18h6v2h-6z"/>
  </svg>`;

  // One final stylesheet, loaded after each page's existing CSS, so the
  // additional theme can recolour panels without replacing their styles.
  if (!document.querySelector('link[data-schmookey-theme-css]')) {
    const sheet = document.createElement("link");
    sheet.rel = "stylesheet";
    sheet.href = CSS;
    sheet.dataset.schmookeyThemeCss = "true";
    document.head.appendChild(sheet);
  }

  // Read as soon as the script is loaded; never infer the new theme from the
  // legacy 'body.light' class, which existing pages already use while dark.
  let current = readTheme();
  applyTheme(current);

  function initToggle() {
    const nav = document.querySelector("nav.menu");
    if (!nav) return;

    const home = [...nav.querySelectorAll("a[href]")].find(a => {
      try {
        return new URL(a.getAttribute("href"), document.baseURI).pathname === "/index.html";
      } catch { return false; }
    });
    if (!home || nav.querySelector(".site-theme-toggle")) return;

    const button = document.createElement("button");
    button.className = "site-theme-toggle";
    button.type = "button";
    button.addEventListener("click", () => {
      current = current === "light" ? "dark" : "light";
      saveTheme(current);
      applyTheme(current, button);
    });
    // Exactly to the LEFT of Home; no existing navigation links are moved.
    nav.insertBefore(button, home);
    applyTheme(current, button);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initToggle, {once: true});
  } else {
    initToggle();
  }
})();
