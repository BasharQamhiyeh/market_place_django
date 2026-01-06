// static/js/banner-slider.js
(() => {
  "use strict";

  function initBanner(root) {
    if (!root) return;

    // Prevent double init (if script is loaded twice, or HTMX partial swap, etc.)
    if (root.dataset.bannerInit === "1") return;
    root.dataset.bannerInit = "1";

    const slidesWrap = root.querySelector(".ad-banner-slides");
    if (!slidesWrap) return;

    const slides = Array.from(slidesWrap.querySelectorAll(".ad-slide"));
    if (slides.length <= 1) return;

    // Dots are inside root
    const dotsWrap = root.querySelector(".ad-dots");

    // Build dots exactly matching slides
    let dots = [];
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
      dots = Array.from(dotsWrap.querySelectorAll(".ad-dot"));
    }

    const autoplay = slidesWrap.dataset.autoplay !== "0";
    const intervalMs = Number(slidesWrap.dataset.interval || "4500") || 4500;

    let idx = slides.findIndex((s) => s.classList.contains("is-active"));
    if (idx < 0) idx = 0;

    let timer = null;

    function applyActiveState() {
      slides.forEach((s, i) => s.classList.toggle("is-active", i === idx));
      dots.forEach((d, i) => d.classList.toggle("is-active", i === idx));
    }

    function setActive(next) {
      idx = (next + slides.length) % slides.length;
      applyActiveState();
    }

    function next() {
      setActive(idx + 1);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function start() {
      if (!autoplay) return;
      stop();
      timer = window.setInterval(next, intervalMs);
    }

    // Dots click
    if (dotsWrap) {
      dotsWrap.addEventListener("click", (e) => {
        const btn = e.target.closest(".ad-dot");
        if (!btn) return;
        const n = Number(btn.dataset.idx);
        if (!Number.isFinite(n)) return;
        setActive(n);
        start(); // restart autoplay
      });
    }

    // Pause on hover (desktop)
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);

    // Ensure initial state
    applyActiveState();
    start();
  }

  function initAllBanners() {
    document.querySelectorAll("[data-banner]").forEach(initBanner);
  }

  // Normal load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllBanners, { once: true });
  } else {
    initAllBanners();
  }

  // Optional: if you ever use HTMX later, this keeps it working on swapped content
  document.addEventListener("htmx:afterSwap", initAllBanners);
})();
