// ehyun.design — autoplay muted loops when on screen; click-to-load video players
(function () {
  var vids = [].slice.call(document.querySelectorAll('video[data-auto]'));
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) {
    vids.forEach(function (v) { v.preload = 'metadata'; });
  } else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) {
          v.preload = 'auto';
          var p = v.play();
          if (p && p.catch) p.catch(function () { v.addEventListener('canplay', function () { v.play().catch(function () {}); }, { once: true }); });
        } else v.pause();
      });
    }, { rootMargin: '200px 0px' });
    vids.forEach(function (v) { io.observe(v); });
  }
  [].slice.call(document.querySelectorAll('button[data-embed]')).forEach(function (b) {
    b.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.className = 'm';
      f.src = b.getAttribute('data-embed');
      f.allow = 'autoplay; fullscreen; picture-in-picture; encrypted-media';
      f.allowFullscreen = true;
      f.title = b.getAttribute('aria-label') || 'Video';
      var frame = b.querySelector('.frame');
      frame.innerHTML = '';
      frame.appendChild(f);
      b.replaceWith(frame);
    });
  });
  if (!reduce) [].slice.call(document.querySelectorAll('button[data-autoplay]')).forEach(function (b) { b.click(); });
  var y = document.getElementById('yr'); if (y) y.textContent = new Date().getFullYear();
})();
