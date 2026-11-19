// Archive rendering continues to filter, escape metadata, and link the whole card.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.resolve(__dirname, "../assets/js/archive.js"), "utf8");
const posts = [
  {title:"A & B <script>",url:"/blog/posts/post1.html",date:"2026-11-16T12:00:00Z",
   readingTime:5,section:"blog",tags:["retro","blog"],cardBlurb:"An example <b> summary."},
  {title:"Music entry",url:"/music/posts/listenbrainz.html",date:"2026-11-15T12:00:00Z",
   readingTime:3,section:"music",tags:["music"],cardBlurb:"Favourite track."},
  {title:"Reject external",url:"https://evil.example/blog/posts/x.html",date:"2026-11-17T12:00:00Z",
   section:"blog",cardBlurb:"Should never render."}
];

async function render(section) {
  const container = {
    dataset:{section},
    innerHTML:"",
    cards:[],
    appendChild(child) { this.cards.push(child); }
  };
  const context = vm.createContext({
    window:{location:{origin:"https://schmookey.xyz"}},
    URL,
    Date,
    console,
    document:{
      getElementById(id){ return id==="archive-list" ? container : null; },
      createElement(tag){assert.equal(tag,"article");return {className:"",innerHTML:""};},
      addEventListener(){}
    },
    fetch:async()=>({ok:true,json:async()=>posts})
  });
  vm.runInContext(source,context);
  await context.loadArchive();
  return container.cards;
}

(async()=>{
  const blog = await render("blog");
  const music = await render("music");
  assert.equal(blog.length,1,"Only valid blog posts render");
  assert.equal(music.length,1,"Only music posts render");
  assert.equal(blog[0].className,"archive-entry h-entry");
  assert.match(blog[0].innerHTML,/class="p-name"/);
  assert.match(blog[0].innerHTML,/class="u-url" href="\/blog\/posts\/post1.html"/);
  assert.match(blog[0].innerHTML,/class="dt-published"/);
  assert.match(blog[0].innerHTML,/class="reading-time"/);
  assert.match(blog[0].innerHTML,/class="archive-summary"/);
  assert.match(blog[0].innerHTML,/class="archive-tags"/);
  assert.match(blog[0].innerHTML,/A &amp; B &lt;script&gt;/);
  assert.match(blog[0].innerHTML,/An example &lt;b&gt; summary\./);
  assert.doesNotMatch(blog[0].innerHTML,/<script>/);
  assert.match(music[0].innerHTML,/class="u-url" href="\/music\/posts\/listenbrainz.html"/);
  assert.match(music[0].innerHTML,/Favourite track\./);
  assert.doesNotMatch(blog[0].innerHTML,/Should never render/);
  console.log("PASS: archive filtering, safe links, blurbs, metadata and escaping");
})().catch(e=>{console.error(e);process.exitCode=1;});
