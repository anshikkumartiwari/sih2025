// Basic UX interactions for the dashboard
(function(){
  const form = document.getElementById('scan-form');
  const btn = document.getElementById('scan-btn');
  const progress = document.getElementById('progress');
  const urlInput = document.getElementById('product_url');
  const counters = document.querySelectorAll('[data-counter]');

  if (form && btn && progress && urlInput) {
    form.addEventListener('submit', function(){
      progress.classList.remove('hidden');
      btn.disabled = true;
      // Save to recent
      try{
        const u = urlInput.value.trim();
        if (u){
          const recent = JSON.parse(localStorage.getItem('recent_urls')||'[]');
          if (!recent.includes(u)){
            recent.unshift(u);
            if (recent.length > 8) recent.length = 8;
            localStorage.setItem('recent_urls', JSON.stringify(recent));
          }
        }
      }catch(e){}
    });
  }

  // Animate counters on home hero
  if (counters.length) {
    const animate = (el) => {
      const targetStr = el.getAttribute('data-counter');
      const isPercent = targetStr.endsWith('%');
      const target = parseInt(targetStr.replace('%',''), 10) || 0;
      let value = 0;
      const steps = 40;
      const inc = Math.max(1, Math.round(target/steps));
      const timer = setInterval(() => {
        value += inc;
        if (value >= target) { value = target; clearInterval(timer); }
        el.textContent = isPercent ? (value + '%') : value;
      }, 30);
    };
    const onView = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{ if (e.isIntersecting) { animate(e.target); onView.unobserve(e.target); } });
    },{threshold:0.4});
    counters.forEach(el=> onView.observe(el));
  }
})();
