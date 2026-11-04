# Website security notes

This website is static: it has no PHP scripts, application server, database credentials or npm build service.

## Client-side safeguards

- Article URLs in `posts.json` must point to local `/blog/posts/*.html` or `/music/posts/*.html` pages. They are validated before being inserted into archive links.
- Dynamic `.webring-script[data-src]` loading accepts only listed script URLs from the two current ring providers, or local JavaScript under `/assets/js/`.
- General external URLs used by widgets must be HTTPS; HTTP is allowed only for the site's own origin during local testing.
- External user-provided text in Webmentions, ListenBrainz and other widgets is escaped or set with `textContent`.

## Residual risks and future work

`webrings.html` includes provider-hosted scripts that execute with the page's privileges. If those scripts are compromised, visitors could be exposed to malicious code. The preferred long-term fix is to replace remote scripts with trusted, reviewed static markup, or isolate integrations in a sandboxed iframe where feasible without breaking functionality.

A **Content Security Policy (CSP)** is recommended, but must be tested first. The site currently relies on multiple third-party integrations and embedded resources; deploying an untested CSP could disable music widgets, webmentions, web-rings or fonts. Start with a host-header Report-Only policy on hosting that supports it. A `<meta>` tag is not equivalent to CSP Report-Only and does not support all directives.

This repository does not include security credentials. Do not commit API tokens or secrets.
