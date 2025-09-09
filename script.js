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

    const navEndPx  = bottomPx(sections.nav);
    const heroEndPx = bottomPx(sections.hero);

    const servicesStartPx = topPx(sections.services);
    const servicesEndPx   = bottomPx(sections.services);

    const testimonialsEndPx = bottomPx(sections.testimonials) 
                           || bottomPx(sections.featured)
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
(function(){
}
);
// Clients rotator (mobile only, respects reduced motion)
