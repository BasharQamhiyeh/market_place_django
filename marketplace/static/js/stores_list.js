// static/js/stores_list.js
(() => {
  "use strict";

  const filtersForm = document.getElementById("storesFiltersForm");
  const searchInput = document.getElementById("searchInput");
  const catLeft     = document.getElementById("catLeft");
  const catRight    = document.getElementById("catRight");
  const catScroll   = document.getElementById("categoryFilters");
  const resultsWrap = document.getElementById("resultsWrap");

  if (!filtersForm || !resultsWrap) return;

  const STORES_URL = "/stores/";
  const PARTIAL_URL = "/stores/partial/";

  // ── category state ────────────────────────────────────────────────────────

  function getSelectedCategories() {
    return Array.from(filtersForm.querySelectorAll('input[name="categories"]')).map(i => i.value);
  }

  function setSelectedCategories(selected) {
    filtersForm.querySelectorAll('input[name="categories"]').forEach(el => el.remove());
    selected.forEach(id => {
      const inp   = document.createElement("input");
      inp.type    = "hidden";
      inp.name    = "categories";
      inp.value   = id;
      filtersForm.appendChild(inp);
    });
  }

  function toggleCategory(categoryId) {
    let selected = getSelectedCategories();
    if (!categoryId) {
      selected = [];
    } else if (selected.includes(categoryId)) {
      selected = selected.filter(x => x !== categoryId);
    } else {
      selected.push(categoryId);
    }
    setSelectedCategories(selected);
    syncChipsUI();
  }

  function syncChipsUI() {
    const selected = getSelectedCategories();
    document.querySelectorAll(".category-chip").forEach(btn => {
      const id = btn.getAttribute("data-category-id") || "";
      if (!id) btn.classList.toggle("active", selected.length === 0);
      else     btn.classList.toggle("active", selected.includes(id));
    });
  }

  // ── fetch helpers ─────────────────────────────────────────────────────────

  function buildParams(q, categories) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    categories.forEach(id => params.append("categories", id));
    return params;
  }

  function loadResults(q, categories) {
    const params = buildParams(q, categories);
    const qs     = params.toString();

    fetch(`${PARTIAL_URL}${qs ? "?" + qs : ""}`, {
      headers: { "HX-Request": "true" }
    })
      .then(r => r.text())
      .then(html => {
        // replace the results wrapper
        const tmp = document.createElement("div");
        tmp.innerHTML = html;
        const newWrap = tmp.firstElementChild;
        if (newWrap) resultsWrap.replaceWith(newWrap);

        syncChipsUI();

        // push correct URL to browser history
        const pageUrl = `${STORES_URL}${qs ? "?" + qs : ""}`;
        history.pushState({}, "", pageUrl);
      })
      .catch(() => {});
  }

  // ── chip clicks ───────────────────────────────────────────────────────────

  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".category-chip");
    if (!chip) return;
    e.preventDefault();

    const categoryId = chip.getAttribute("data-category-id") || "";
    toggleCategory(categoryId);

    const q        = searchInput ? searchInput.value.trim() : "";
    const selected = getSelectedCategories();
    loadResults(q, selected);
  });

  // ── search ────────────────────────────────────────────────────────────────

  let searchTimer = null;

  function triggerSearch() {
    const q        = searchInput ? searchInput.value.trim() : "";
    const selected = getSelectedCategories();
    loadResults(q, selected);
  }

  if (searchInput) {
    searchInput.addEventListener("keyup", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(triggerSearch, 400);
    });
  }

  const searchForm = document.getElementById("storesSearchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      clearTimeout(searchTimer);
      triggerSearch();
    });
  }

  // ── arrow scroll ──────────────────────────────────────────────────────────

  if (catLeft  && catScroll) catLeft.addEventListener("click",  () => catScroll.scrollBy({ left: -240, behavior: "smooth" }));
  if (catRight && catScroll) catRight.addEventListener("click", () => catScroll.scrollBy({ left:  240, behavior: "smooth" }));

  syncChipsUI();
})();
