// static/js/banner-slider.js
(() => {
  function initBanner(root) {
    if (!root) return;

    const slidesWrap = root.querySelector(".ad-banner-slides");
    if (!slidesWrap) return;

    // ✅ Works with your current markup (img.ad-slide...)
    const slides = Array.from(slidesWrap.querySelectorAll(".ad-slide"));
    if (slides.length <= 1) return;

    // Dots can be inside overlay OR directly under slidesWrap (both supported)
    const dotsWrap =
      root.querySelector(".ad-dots") ||
      slidesWrap.querySelector(".ad-dots");

    // If dots are not present or wrong count, rebuild them safely
    if (dotsWrap) {
      dotsWrap.innerHTML = "";
      slides.forEach((_, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "ad-dot" + (i === 0 ? " is-active" : "");
        b.dataset.idx = String(i);
        b.setAttribute("aria-label", `إعلان ${i + 1}`);
        dotsWrap.appendChild(b);
      });
    }

    const dots = dotsWrap ? Array.from(dotsWrap.querySelectorAll(".ad-dot")) : [];

    // Autoplay config
    const autoplay = slidesWrap.dataset.autoplay !== "0";
    const intervalMs = Number(slidesWrap.dataset.interval || "4500") || 4500;

    let idx = slides.findIndex(s => s.classList.contains("is-active"));
    if (idx < 0) idx = 0;

    let timer = null;

    function setActive(next) {
      if (next === idx) return;
      slides[idx].classList.remove("is-active");
      if (dots[idx]) dots[idx].classList.remove("is-active");

      idx = (next + slides.length) % slides.length;

      slides[idx].classList.add("is-active");
      if (dots[idx]) dots[idx].classList.add("is-active");
    }

    function next() {
      setActive(idx + 1);
    }

    function start() {
      if (!autoplay) return;
      stop();
      timer = window.setInterval(next, intervalMs);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    // Dots click
    if (dotsWrap) {
      dotsWrap.addEventListener("click", (e) => {
        const btn = e.target.closest(".ad-dot");
        if (!btn) return;
        const n = Number(btn.dataset.idx);
        if (!Number.isFinite(n)) return;
        setActive(n);
        start(); // restart autoplay after manual change
      });
    }

    // Pause on hover (desktop)
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);

    // ✅ Ensure first slide is active at init
    slides.forEach((s, i) => s.classList.toggle("is-active", i === idx));
    dots.forEach((d, i) => d.classList.toggle("is-active", i === idx));

    start();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initBanner(document.getElementById("adBanner"));
  });
})();
