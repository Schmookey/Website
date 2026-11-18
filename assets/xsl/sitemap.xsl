<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9" exclude-result-prefixes="sm">
  <!-- Browser-only view. Crawlers still receive the standard XML sitemap. -->
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <xsl:variable name="urls" select="sm:urlset/sm:url"/>
    <xsl:variable name="blog" select="$urls[starts-with(sm:loc, 'https://schmookey.xyz/blog/') or sm:loc = 'https://schmookey.xyz/blog-archive.html']"/>
    <xsl:variable name="music" select="$urls[starts-with(sm:loc, 'https://schmookey.xyz/music/') or sm:loc = 'https://schmookey.xyz/music-archive.html']"/>
    <xsl:variable name="notes" select="$urls[starts-with(sm:loc, 'https://schmookey.xyz/notes/')]"/>
    <xsl:variable name="pages" select="$urls[not(starts-with(sm:loc, 'https://schmookey.xyz/blog/')) and not(sm:loc = 'https://schmookey.xyz/blog-archive.html') and not(starts-with(sm:loc, 'https://schmookey.xyz/music/')) and not(sm:loc = 'https://schmookey.xyz/music-archive.html') and not(starts-with(sm:loc, 'https://schmookey.xyz/notes/'))]"/>
    <html lang="en-GB">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <meta name="color-scheme" content="dark"/>
        <title>Schmookey.xyz — Sitemap</title>
        <style type="text/css">
          * { box-sizing: border-box; }
          body { margin: 0; padding: 28px 16px 56px; background: #0b0f1f; color: #e6ecff;
                 font: 16px/1.65 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
          a { color: #a7c0ff; text-underline-offset: 3px; }
          a:hover { color: #fff; }
          a:focus-visible { outline: 3px solid #ff6671; outline-offset: 4px; }
          .container { max-width: 860px; margin: 0 auto; }
          .masthead { border: 3px solid #1e40ff; border-radius: 8px; background: #101728;
                      box-shadow: 0 5px 0 #000; overflow: hidden; }
          .masthead-top { display: flex; flex-wrap: wrap; justify-content: space-between;
                          align-items: center; gap: 12px; padding: 18px 22px; background: #141b31; }
          .brand { font: 700 15px/1.5 ui-monospace, "DejaVu Sans Mono", monospace;
                   letter-spacing: 0.08em; color: #fff; text-transform: uppercase; }
          .format { border: 1px solid #7289ce; border-radius: 4px; padding: 3px 10px;
                    color: #dce5ff; font-size: 12px; font-weight: 700; letter-spacing: 0.07em; }
          .stripe { height: 5px; background: #d62828; }
          .intro { padding: 20px 22px 22px; }
          h1 { font-size: clamp(26px, 5vw, 36px); line-height: 1.2; margin: 0 0 10px; color: #fff; }
          .intro p { margin: 0 0 18px; color: #d1d7ec; }
          .site-link { display: inline-block; border: 2px solid #df5261; border-radius: 4px;
                       padding: 9px 14px; background: #841e30; color: #fff;
                       font-weight: 700; text-decoration: none; }
          .site-link:hover { background: #b02a40; color: #fff; }
          .explain { margin: 22px 0 12px; padding: 5px 15px; border-left: 4px solid #1e40ff;
                     color: #c6cce3; font-size: 14px; }
          .explain p { margin: 5px 0; }
          .shortcut { display: flex; flex-wrap: wrap; gap: 8px; margin: 20px 0 26px; }
          .shortcut a { display: inline-block; padding: 5px 10px; background: #182447;
                        border: 1px solid #5176d1; border-radius: 4px; font-size: 13px; }
          .group { margin: 0 0 18px; padding: 18px 20px; background: #11182b;
                   border: 2px solid #2b407c; border-radius: 6px; box-shadow: 0 3px 0 #000; }
          .group h2 { margin: 0 0 13px; color: #fff; font-size: 20px; line-height: 1.4; }
          .count { margin-left: 10px; font-size: 13px; font-weight: normal; color: #abb7d7; }
          .links { margin: 0; padding: 0; list-style: none; }
          .links li { padding: 12px 0; border-top: 1px solid #2e3a5c; overflow-wrap: anywhere; }
          .page-link { font-weight: 650; color: #e0e8ff; }
          .path { margin-top: 3px; color: #aab8d7; font-size: 13px; overflow-wrap: anywhere; }
          .lastmod { margin-top: 4px; color: #aab8d7; font-size: 12px; }
          footer { margin-top: 25px; color: #aab5d1; font-size: 13px; }
          @media (max-width: 540px) {
            body { padding: 12px 10px 36px; }
            .masthead-top, .intro { padding-left: 15px; padding-right: 15px; }
            .group { padding: 14px 15px; }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <header class="masthead">
            <div class="masthead-top">
              <span class="brand">Schmookey.xyz</span>
              <span class="format">XML Sitemap</span>
            </div>
            <div class="stripe"></div>
            <div class="intro">
              <h1>Sitemap</h1>
              <p>Explore the public pages, blog posts, music articles and Notes on Schmookey.xyz.</p>
              <a class="site-link" href="https://schmookey.xyz/">Visit Website</a>
            </div>
          </header>
          <aside class="explain">
            <p>This is a readable view of the XML sitemap. Search engines receive the same list of <xsl:value-of select="count($urls)"/> public URLs.</p>
          </aside>
          <nav class="shortcut" aria-label="Sitemap sections">
            <a href="#site-pages">Site pages</a>
            <a href="#blog">Blog</a>
            <a href="#music">Music</a>
            <a href="#notes">Notes</a>
          </nav>
          <main>
            <xsl:call-template name="section">
              <xsl:with-param name="heading" select="'Site pages'"/>
              <xsl:with-param name="section-id" select="'site-pages'"/>
              <xsl:with-param name="items" select="$pages"/>
            </xsl:call-template>
            <xsl:call-template name="section">
              <xsl:with-param name="heading" select="'Blog'"/>
              <xsl:with-param name="section-id" select="'blog'"/>
              <xsl:with-param name="items" select="$blog"/>
            </xsl:call-template>
            <xsl:call-template name="section">
              <xsl:with-param name="heading" select="'Music'"/>
              <xsl:with-param name="section-id" select="'music'"/>
              <xsl:with-param name="items" select="$music"/>
            </xsl:call-template>
            <xsl:call-template name="section">
              <xsl:with-param name="heading" select="'Notes'"/>
              <xsl:with-param name="section-id" select="'notes'"/>
              <xsl:with-param name="items" select="$notes"/>
            </xsl:call-template>
          </main>
          <footer>
            <p>The sitemap is generated automatically from published content. For new updates, see the <a href="https://schmookey.xyz/feed.xml">RSS feed</a>.</p>
          </footer>
        </div>
      </body>
    </html>
  </xsl:template>

  <xsl:template name="section">
    <xsl:param name="heading"/>
    <xsl:param name="section-id"/>
    <xsl:param name="items"/>
    <section class="group" id="{$section-id}">
      <h2><xsl:value-of select="$heading"/><span class="count">(<xsl:value-of select="count($items)"/>)</span></h2>
      <ul class="links">
        <xsl:for-each select="$items">
          <xsl:variable name="url" select="normalize-space(sm:loc)"/>
          <li>
            <a class="page-link" href="{$url}">
              <xsl:choose>
                <xsl:when test="$url = 'https://schmookey.xyz/'">Home</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/about.html'">About</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/now.html'">Now</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/listening.html'">Now Listening</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/now-watching.html'">Now Watching</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/random/'">Random</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/webrings.html'">Webrings</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/changelog.html'">Changelog</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/privacy.html'">Privacy Policy</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/blog/'">Blog Home</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/blog-archive.html'">Blog Archive</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/music/'">Music Home</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/music-archive.html'">Music Archive</xsl:when>
                <xsl:when test="$url = 'https://schmookey.xyz/notes/'">Notes Home</xsl:when>
                <xsl:when test="starts-with($url, 'https://schmookey.xyz/notes/')">
                  <xsl:text>Note</xsl:text>
                  <xsl:if test="sm:lastmod"><xsl:text> — </xsl:text><xsl:value-of select="sm:lastmod"/></xsl:if>
                </xsl:when>
                <xsl:when test="contains($url, '/posts/')">
                  <xsl:variable name="slug" select="translate(substring-before(substring-after($url, '/posts/'), '.html'), '_-', '  ')"/>
                  <xsl:value-of select="concat(translate(substring($slug, 1, 1), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), substring($slug, 2))"/>
                </xsl:when>
                <xsl:otherwise><xsl:value-of select="substring-after($url, 'https://schmookey.xyz/')"/></xsl:otherwise>
              </xsl:choose>
            </a>
            <div class="path"><xsl:value-of select="substring-after($url, 'https://schmookey.xyz')"/></div>
            <xsl:if test="sm:lastmod">
              <div class="lastmod">Last updated: <xsl:value-of select="sm:lastmod"/></div>
            </xsl:if>
          </li>
        </xsl:for-each>
      </ul>
    </section>
  </xsl:template>
</xsl:stylesheet>
