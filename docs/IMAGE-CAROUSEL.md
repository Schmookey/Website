# Chunky 16-bit image carousel

Drop this optional block anywhere inside the article's `.e-content` in a blog or music post. No separate CSS or script tags are necessary when the page already loads the shared `main.js`.

```html
<div class="image-carousel">
  <figure>
    <img src="/assets/images/FIRST-IMAGE.webp" alt="FIRST IMAGE DESCRIPTION" loading="lazy" decoding="async">
    <figcaption>FIRST IMAGE CAPTION</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/SECOND-IMAGE.webp" alt="SECOND IMAGE DESCRIPTION" loading="lazy" decoding="async">
    <figcaption>SECOND IMAGE CAPTION</figcaption>
  </figure>
</div>
```

Copy another `figure` inside the same div for each additional image. Use real local image filenames, useful alt text and your own captions. For an optional descriptive gallery title, add `aria-label="Recent purchases"` to the outer div. Multiple carousels on one page are independent; ordinary standalone `figure.post-image` blocks continue to work.

The shared loader fetches the component's local CSS and JavaScript only when a carousel container is present. The controls use the existing back and forward SVGs. Images retain their proportions, the existing Mega Drive/NES theme switch controls the palette, and there is no autoplay. Keyboard users can Tab to a carousel or its controls, then use Left/Right, Home/End or the individual buttons. If the script cannot load, all original figures remain visible. Print mode shows all slides. With fewer than two images the block remains ordinary image markup.

The existing blog template includes a commented-out example that can be copied into music articles as well; this repository has no separate music article template. For offline preview, run the site's local HTTP server as described in the root README.
