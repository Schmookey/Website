// Dependency-free DOM regression test for the real carousel component.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.join(__dirname, "..");
const source = fs.readFileSync(path.join(root, "assets/js/image-carousel.js"), "utf8");
class Node {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.children = []; this.attrs = {}; this.events = {};
    this.className = ""; this.textContent = ""; this.hidden = false;
    this.classList = {add: name => {this.className += " " + name;}};
  }
  append(...nodes) {for (const node of nodes) {if (node.parent) node.parent.children.splice(node.parent.children.indexOf(node),1); this.children.push(node); node.parent=this;}}
  insertBefore(node, before) {this.children.splice(this.children.indexOf(before),0,node);node.parent=this;}
  setAttribute(k,v) {this.attrs[k]=String(v);}
  getAttribute(k) {return this.attrs[k] ?? null;}
  hasAttribute(k) {return Object.hasOwn(this.attrs,k);}
  addEventListener(k,fn) {this.events[k]=fn;}
  contains(node) {return node===this || this.children.some(child=>child.contains(node));}
  querySelector(selector) {for(const child of this.children) {if (child.tagName===selector.toUpperCase() || (selector.startsWith(".") && child.className.split(" ").includes(selector.slice(1)))) return child; const match=child.querySelector(selector); if(match)return match;}return null;}
}
function gallery(count, label) {
  const node = new Node("div");
  if(label)node.setAttribute("aria-label",label);
  const figures = Array.from({length:count},(_,i)=>{
    const fig=new Node("figure"),img=new Node("img"),cap=new Node("figcaption");
    img.alt="Photo "+i; cap.textContent="Caption "+i;
    fig.append(img,cap);node.append(fig);return fig;
  });
  return {node,figures};
}
const a=gallery(3,"Recent purchases"), b=gallery(2), single=gallery(1), empty=gallery(0);
const document={readyState:"complete",createElement:tag=>new Node(tag),querySelectorAll:()=>[a.node,b.node,single.node,empty.node]};
vm.runInNewContext(source,{document});
const controls=a.node.querySelector(".gallery-controls");
const counter=a.node.querySelector(".gallery-counter");
const status=a.node.querySelector(".gallery-announcement");
const jumps=a.node.querySelector(".gallery-indicators").children;
const hidden = g=>g.figures.map(f=>f.hidden);
assert.deepEqual(hidden(a),[false,true,true]);
assert.deepEqual(hidden(b),[false,true]);
assert.equal(counter.textContent,"01 / 03");
assert.equal(a.node.getAttribute("aria-label"),"Recent purchases");
assert.equal(a.node.tabIndex,0);
assert.equal(a.node.querySelector(".gallery-prev").querySelector("img").src,"/assets/images/back.svg");
assert.equal(a.node.querySelector(".gallery-next").querySelector("img").src,"/assets/images/forward.svg");
a.node.querySelector(".gallery-next").events.click();
assert.deepEqual(hidden(a),[true,false,true]);
assert.equal(counter.textContent,"02 / 03");
assert.equal(status.textContent,"Image 2 of 3: Caption 1");
assert.equal(jumps[1].getAttribute("aria-current"),"true");
assert.deepEqual(hidden(b),[false,true]);
jumps[2].events.click();
assert.equal(counter.textContent,"03 / 03");
a.node.querySelector(".gallery-next").events.click();
assert.equal(counter.textContent,"01 / 03");
a.node.querySelector(".gallery-prev").events.click();
assert.equal(counter.textContent,"03 / 03");
let prevented=false;
a.node.events.keydown({target:controls.children[0],key:"Home",preventDefault(){prevented=true;}});
assert.equal(prevented,true);
assert.equal(counter.textContent,"01 / 03");
a.node.events.keydown({target:a.node,key:"End",preventDefault(){}});
assert.equal(counter.textContent,"03 / 03");
a.node.events.keydown({target:a.figures[2].children[0],key:"ArrowLeft",preventDefault(){throw Error("should not intercept article content");}});
assert.equal(counter.textContent,"03 / 03");
assert.equal(single.node.hasAttribute("data-enhanced"),false);
assert.equal(empty.node.hasAttribute("data-enhanced"),false);
assert.equal(single.figures[0].hidden,false);
const originalChildren=a.node.children.length;
vm.runInNewContext(source,{document});
assert.equal(a.node.children.length,originalChildren);
assert.equal(a.figures[0].querySelector("figcaption").textContent,"Caption 0");

// Loader: nothing requested on a normal article; stylesheet precedes the script.
const main=fs.readFileSync(path.join(root,"assets/js/main.js"),"utf8");
const loader=main.slice(main.indexOf("(function loadImageCarousel()"));
let present=false;const requests=[];
const loaderDoc={readyState:"complete",createElement:tag=>new Node(tag),head:{appendChild:n=>requests.push(n)},querySelector(selector){
  if(selector===".image-carousel")return present?{}:null;
  return requests.find(n=>n.hasAttribute("data-image-carousel") && (selector.startsWith("link")?n.tagName==="LINK":n.tagName==="SCRIPT"))||null;
}};
vm.runInNewContext(loader,{document:loaderDoc});
assert.equal(requests.length,0);
present=true;
vm.runInNewContext(loader,{document:loaderDoc});
assert.equal(requests.length,1);
assert.equal(requests[0].href,"/assets/css/image-carousel.css");
requests[0].onload();
assert.equal(requests.length,2);
assert.equal(requests[1].src,"/assets/js/image-carousel.js");
vm.runInNewContext(loader,{document:loaderDoc});
assert.equal(requests.length,2);
console.log("PASS: independent carousels, wraparound, indicators, keyboard, captions, single-image fallback, idempotence and conditional loader");
