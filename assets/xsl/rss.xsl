<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <!-- Display the canonical RSS feed as a website in browsers.
       The XML is not replaced, so feed readers still receive RSS 2.0. -->
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="en-GB">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <meta name="color-scheme" content="dark"/>
        <title><xsl:value-of select="rss/channel/title"/> — RSS Feed</title>
        <style type="text/css">
          * { box-sizing: border-box; }
          body {
            margin: 0; padding: 28px 16px 56px;
            background: #0b0f1f; color: #e6ecff;
            font: 16px/1.65 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }
          a { color: #95b7ff; text-underline-offset: 3px; }
          a:hover { color: #fff; }
          a:focus-visible { outline: 3px solid #ff6671; outline-offset: 4px; }
          .container { max-width: 860px; margin: 0 auto; }
          .masthead {
            border: 3px solid #1e40ff; border-radius: 8px;
            background: #101728; box-shadow: 0 5px 0 #000;
            overflow: hidden;
          }
          .masthead-top {
            display: flex; flex-wrap: wrap; justify-content: space-between;
            align-items: center; gap: 12px; padding: 18px 22px;
            background: #141b31;
          }
          .brand {
            font: 700 15px/1.5 ui-monospace, "DejaVu Sans Mono", monospace;
            letter-spacing: 0.08em; color: #fff; text-transform: uppercase;
          }
          .format {
            border: 1px solid #7289ce; border-radius: 4px;
            padding: 3px 10px; color: #dce5ff; font-size: 12px;
            font-weight: 700; letter-spacing: 0.07em;
          }
          .stripe { height: 5px; background: #d62828; }
          .intro { padding: 20px 22px 22px; }
          h1 { font-size: clamp(26px, 5vw, 36px); line-height: 1.2; margin: 0 0 10px; color: #fff; }
          .intro p { margin: 0 0 18px; color: #d1d7ec; }
          .site-link {
            display: inline-block; border: 2px solid #df5261; border-radius: 4px;
            padding: 9px 14px; background: #841e30; color: #fff;
            font-weight: 700; text-decoration: none;
          }
          .site-link:hover { background: #b02a40; color: #fff; }
          .feed-note {
            margin: 20px 0 24px; border-left: 4px solid #1e40ff;
            padding: 4px 15px; color: #c6cce3; font-size: 14px;
          }
          .feed-note p { margin: 6px 0; }
          code {
            overflow-wrap: anywhere; color: #fff;
            background: #222b49; padding: 2px 5px; border-radius: 3px;
          }
          .section-heading {
            margin: 28px 0 14px; color: #a6b9ff;
            font: 700 13px/1.5 ui-monospace, "DejaVu Sans Mono", monospace;
            text-transform: uppercase; letter-spacing: 0.1em;
          }
          .entries { display: grid; gap: 14px; }
          .entry {
            background: #11182b; border: 2px solid #2b407c;
            border-radius: 6px; padding: 18px 20px;
            box-shadow: 0 3px 0 #000;
          }
          .entry h2 { margin: 0 0 6px; font-size: 19px; line-height: 1.4; }
          .entry h2 a { color: #fff; }
          .entry h2 a:hover { color: #b8cbff; }
          .date { margin: 0 0 12px; font-size: 13px; color: #abb7d7; }
          .summary { margin: 0 0 14px; overflow-wrap: anywhere; color: #e0e3f0; }
          .read-more { font-weight: 700; color: #ff9ca4; }
          footer { margin-top: 28px; color: #aab5d1; font-size: 13px; }
          @media (max-width: 540px) {
            body { padding: 12px 10px 36px; }
            .masthead-top, .intro { padding-left: 15px; padding-right: 15px; }
            .entry { padding: 14px 15px; }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <header class="masthead">
            <div class="masthead-top">
              <span class="brand">Schmookey.xyz</span>
              <span class="format">RSS 2.0</span>
            </div>
            <div class="stripe"></div>
            <div class="intro">
              <h1>RSS Feed</h1>
              <p><xsl:value-of select="rss/channel/description"/></p>
              <a class="site-link" href="https://schmookey.xyz/">Visit Schmookey's World</a>
            </div>
          </header>
          <aside class="feed-note" aria-label="How to subscribe">
            <p>This is an RSS feed. Copy <code>https://schmookey.xyz/feed.xml</code> into your favourite feed reader to subscribe.</p>
          </aside>
          <main id="updates">
            <h2 class="section-heading">Latest updates (<xsl:value-of select="count(rss/channel/item)"/>)</h2>
            <div class="entries">
              <xsl:for-each select="rss/channel/item">
                <article class="entry">
                  <h2>
                    <xsl:choose>
                      <xsl:when test="starts-with(normalize-space(link), 'https://schmookey.xyz/')">
                        <a href="{normalize-space(link)}"><xsl:value-of select="title"/></a>
                      </xsl:when>
                      <xsl:otherwise><xsl:value-of select="title"/></xsl:otherwise>
                    </xsl:choose>
                  </h2>
                  <p class="date"><xsl:value-of select="substring(pubDate, 6, 11)"/></p>
                  <p class="summary"><xsl:value-of select="description"/></p>
                  <xsl:if test="starts-with(normalize-space(link), 'https://schmookey.xyz/')">
                    <a class="read-more" href="{normalize-space(link)}">Read on the website &#8594;</a>
                  </xsl:if>
                </article>
              </xsl:for-each>
            </div>
          </main>
          <footer>
            <p>This page is an accessible browser view of the same RSS feed used by feed readers.</p>
          </footer>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
