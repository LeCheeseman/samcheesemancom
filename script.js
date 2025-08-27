// Carousel logic


// Toggle switch functionality for Featured Works filter
document.addEventListener('DOMContentLoaded', function() {
    const workToggle = document.getElementById('workToggle');
    
    if (workToggle) {
        workToggle.addEventListener('change', function() {
            const isChecked = this.checked;
            // Add functionality here to filter between Commercials and Copywriting
            console.log(isChecked ? 'Showing Copywriting works' : 'Showing Commercial works');
            
            // You can add actual filtering logic here when you have the work items
            // For example:
            // filterWorks(isChecked ? 'copywriting' : 'commercials');
        });
    }
});

// Function to filter works (placeholder for future implementation)
function filterWorks(category) {
    // This function can be implemented to show/hide work items based on category
    console.log(`Filtering works by: ${category}`);
}

// Logo wiggle animation
// --- Client logo wiggle (sequential, no recent repeats) ---
document.addEventListener('DOMContentLoaded', () => {
  // prevent multiple initialisations (hot reloads, etc.)
  if (window.__logoWiggleInit) return;
  window.__logoWiggleInit = true;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const logos = Array.from(document.querySelectorAll('.client-logos img'));
  if (prefersReduced || logos.length === 0) return;

  // clean any leftover classes
  logos.forEach(img => img.classList.remove('wiggle-cw', 'wiggle-ccw'));

  const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
  let clockwise = true;
  let animating = false;
  let timeoutId = null;

  // keep last N indices to avoid repeats
  const historyLimit = Math.max(1, Math.min(6, logos.length - 1));
  const recent = [];

  function pickIndex() {
    if (logos.length === 1) return 0;
    const blacklist = new Set(recent);
    let idx = Math.floor(Math.random() * logos.length);
    for (let i = 0; i < 20 && blacklist.has(idx); i++) {
      idx = Math.floor(Math.random() * logos.length);
    }
    return idx;
  }

  function wiggleNext() {
    if (animating) return; // strict one-at-a-time
    animating = true;

    const i = pickIndex();
    const img = logos[i];
    const cls = clockwise ? 'wiggle-cw' : 'wiggle-ccw';
    clockwise = !clockwise;

    img.classList.add(cls);
    img.addEventListener('animationend', function endHandler() {
      img.classList.remove(cls);
      img.removeEventListener('animationend', endHandler);

      // update recent history
      recent.push(i);
      if (recent.length > historyLimit) recent.shift();

      animating = false;
      timeoutId = setTimeout(wiggleNext, rand(1200, 2600)); // schedule next only after end
    }, { once: true });
  }

  timeoutId = setTimeout(wiggleNext, 1000);
});


// --- Client logo wiggle (no recent repeats) ---
document.addEventListener('DOMContentLoaded', () => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const logos = Array.from(document.querySelectorAll('.client-logos img'));
  if (prefersReduced || logos.length === 0) return;

  let clockwise = true;
  const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

  // Avoid repeating any logo that appeared in the last `historyLimit` picks
  const historyLimit = Math.max(1, Math.min(6, logos.length - 1)); // e.g. 6, but never >= logos.length
  const recent = []; // queue of recent indices

  function pickIndex() {
    if (logos.length === 1) return 0;

    const blacklist = new Set(recent);
    // Try up to 20 times to find an index not in recent history.
    // If the set is too small (e.g. few logos), it will fall back gracefully.
    let idx = Math.floor(Math.random() * logos.length);
    for (let i = 0; i < 20; i++) {
      if (!blacklist.has(idx)) break;
      idx = Math.floor(Math.random() * logos.length);
    }
    return idx;
  }

  function wiggleNext() {
    const i = pickIndex();
    const img = logos[i];
    const cls = clockwise ? 'wiggle-cw' : 'wiggle-ccw';
    clockwise = !clockwise;

    img.classList.add(cls);
    img.addEventListener('animationend', function handler() {
      img.classList.remove(cls);
      img.removeEventListener('animationend', handler);
    }, { once: true });

    // update recent history
    recent.push(i);
    if (recent.length > historyLimit) recent.shift();

    setTimeout(wiggleNext, rand(1200, 2600));
  }

  setTimeout(wiggleNext, 1000);
});

/* GRADIENT */

(function(){
  const sections = {
    nav: '.navbar',
    hero: '.hero',
    services: '.services',
    featured: '.featured-work',
    testimonials: '.rtbs'
  };

  function pct(px){ 
    const total = document.documentElement.scrollHeight || 1;
    return Math.max(0, Math.min(100, (px / total) * 100));
  }

  function topPx(sel){
    const el = document.querySelector(sel);
    if(!el) return null;
    const r = el.getBoundingClientRect();
    return r.top + window.scrollY;
  }
  function bottomPx(sel){
    const el = document.querySelector(sel);
    if(!el) return null;
    const r = el.getBoundingClientRect();
    return r.bottom + window.scrollY;
  }

  function setStops(){
    const root = document.documentElement;

    const navEndPx  = bottomPx(ids.nav);
    const heroEndPx = bottomPx(ids.hero);

    const servicesStartPx = topPx(ids.services);
    const servicesEndPx   = bottomPx(ids.services);

    const testimonialsEndPx = bottomPx(ids.testimonials) 
                           || bottomPx(ids.featured)
                           || (document.documentElement.scrollHeight - 1);

    if(navEndPx!=null)  root.style.setProperty('--nav-end', pct(navEndPx).toFixed(2)+'%');
    if(heroEndPx!=null) root.style.setProperty('--hero-end', pct(heroEndPx).toFixed(2)+'%');

    if(servicesStartPx!=null) root.style.setProperty('--services-start', pct(servicesStartPx).toFixed(2)+'%');
    if(servicesEndPx!=null)   root.style.setProperty('--services-end',   pct(servicesEndPx).toFixed(2)+'%');
    if(testimonialsEndPx!=null) root.style.setProperty('--testimonials-end', pct(testimonialsEndPx).toFixed(2)+'%');
  }

  function debounced(fn, wait){
    let t; return function(){ clearTimeout(t); t=setTimeout(fn, wait); };
  }

  window.addEventListener('load', setStops);
  window.addEventListener('resize', debounced(setStops, 150));
})();