/* Progressive enhancement of simple .image-carousel > figure markup.
 * No timers, network data, HTML injection, or third-party dependencies.
 */
(function () {
  "use strict";
  function element(tag, className, text) {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function enhance(gallery) {
    if (gallery.hasAttribute("data-enhanced")) return;
    const slides = Array.from(gallery.children).filter(node => node.tagName === "FIGURE" && node.querySelector("img"));
    // Empty and single-image containers remain ordinary HTML.
    if (slides.length < 2) return;
    const title = gallery.getAttribute("aria-label") || "Image gallery";
    const heading = element("div", "gallery-heading", title);
    const frame = element("div", "gallery-slides");
    const controls = element("div", "gallery-controls");
    const counter = element("span", "gallery-counter");
    counter.setAttribute("aria-hidden", "true");
    const indicators = element("div", "gallery-indicators");
    indicators.setAttribute("role", "group");
    indicators.setAttribute("aria-label", "Choose image");
    const status = element("div", "gallery-announcement");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.setAttribute("aria-atomic", "true");
    for (const node of [heading, controls, status]) node.setAttribute("data-carousel-ui", "");

    function arrow(direction, label, file) {
      const button = element("button", "gallery-button gallery-" + direction);
      button.type = "button";
      button.setAttribute("aria-label", label + " image");
      const icon = document.createElement("img");
      icon.src = "/assets/images/" + file + ".svg";
      icon.alt = "";
      icon.width = 32;
      icon.height = 32;
      const caption = element("span", "", label);
      if (direction === "prev") button.append(icon, caption);
      else button.append(caption, icon);
      return button;
    }

    const prev = arrow("prev", "Previous", "back");
    const next = arrow("next", "Next", "forward");
    let index = 0;
    const jumps = slides.map((_slide, i) => {
      const button = element("button", "gallery-jump");
      button.type = "button";
      button.setAttribute("aria-label", "Show image " + (i + 1) + " of " + slides.length);
      button.addEventListener("click", () => show(i));
      indicators.append(button);
      return button;
    });
    const pad = n => String(n).padStart(2, "0");

    function show(i, announce = true) {
      index = (i + slides.length) % slides.length;
      slides.forEach((slide, j) => {
        slide.hidden = j !== index;
        jumps[j].setAttribute("aria-current", j === index ? "true" : "false");
      });
      counter.textContent = pad(index + 1) + " / " + pad(slides.length);
      if (announce) {
        const caption = slides[index].querySelector("figcaption");
        const description = caption?.textContent.trim() || slides[index].querySelector("img").alt || "";
        status.textContent = "Image " + (index + 1) + " of " + slides.length + (description ? ": " + description : "");
      }
    }
    controls.append(prev, counter, next, indicators);
    prev.addEventListener("click", () => show(index - 1));
    next.addEventListener("click", () => show(index + 1));
    gallery.addEventListener("keydown", event => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
          (event.target !== gallery && !controls.contains(event.target))) return;
      const destination = {ArrowLeft:index - 1, ArrowRight:index + 1, Home:0, End:slides.length - 1};
      if (!Object.prototype.hasOwnProperty.call(destination, event.key)) return;
      event.preventDefault();
      show(destination[event.key]);
    });

    // Move existing figures, retaining alt text, captions, links and microformats.
    gallery.insertBefore(heading, slides[0]);
    gallery.insertBefore(frame, slides[0]);
    for (const slide of slides) {
      slide.classList.add("gallery-slide");
      frame.append(slide);
    }
    gallery.append(controls, status);
    gallery.setAttribute("role", "group");
    gallery.setAttribute("aria-roledescription", "carousel");
    gallery.setAttribute("aria-label", title);
    gallery.tabIndex = 0;
    gallery.setAttribute("data-enhanced", "");
    show(0, false);
  }

  function init() {
    for (const gallery of document.querySelectorAll(".image-carousel")) enhance(gallery);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, {once:true});
  else init();
})();
