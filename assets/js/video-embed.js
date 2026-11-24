// Load the privacy-enhanced player only after explicit link activation.
(function () {
  "use strict";
  for (const panel of document.querySelectorAll(".video-embed[data-youtube-id]")) {
    const id = panel.dataset.youtubeId;
    const link = panel.querySelector(".video-load");
    if (!link || !/^[A-Za-z0-9_-]{11}$/.test(id)) continue;
    link.addEventListener("click", event => {
      // Preserve ordinary modified-click navigation and the no-JS link.
      if (event.defaultPrevented || event.button !== 0 ||
          event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const player = document.createElement("iframe");
      player.title = link.querySelector(".video-load-title")?.textContent.trim() || "YouTube video";
      player.src = "https://www.youtube-nocookie.com/embed/" + id;
      player.referrerPolicy = "strict-origin-when-cross-origin";
      player.allowFullscreen = true;
      player.tabIndex = 0;
      link.replaceWith(player);
      player.focus();
    }, { once: false });
  }
})();
