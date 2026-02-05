// static/js/stores_list.js
(() => {
  "use strict";

  const filtersForm = document.getElementById("storesFiltersForm");
  const searchInput = document.getElementById("searchInput");
  if (!filtersForm) return;

  function getSelectedCategories() {
    return Array.from(filtersForm.querySelectorAll('input[name="categories"]')).map(i => i.value);
  }

  function setSelectedCategories(selected) {
    filtersForm.querySelectorAll('input[name="categories"]').forEach(el => el.remove());
    selected.forEach(id => {
      const inp = document.createElement("input");
      inp.type = "hidden";
      inp.name = "categories";
      inp.value = id;
      filtersForm.appendChild(inp);
    });
  }

  function syncChipsUI() {
    const selected = getSelectedCategories();
    document.querySelectorAll(".category-chip").forEach(btn => {
      const id = btn.getAttribute("data-category-id") || "";
      if (!id) btn.classList.toggle("active", selected.length === 0);
      else btn.classList.toggle("active", selected.includes(id));
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

  // Category click: update state, then trigger HTMX custom event once
  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".category-chip");
    if (!chip) return;

    e.preventDefault();

    const categoryId = chip.getAttribute("data-category-id") || "";
    toggleCategory(categoryId);

    // Reset page on filter change
    chip.dataset.resetPage = "1";

    // Trigger custom event that HTMX listens to
    if (window.htmx) window.htmx.trigger(chip, "filtersChanged");
  });

  // Ensure q is current + page reset handled
  document.body.addEventListener("htmx:configRequest", (e) => {

    const elt = e.detail.elt;
    if (elt && elt.classList && elt.classList.contains("category-chip") && elt.dataset.resetPage === "1") {
      e.detail.parameters.page = "1";
      delete elt.dataset.resetPage;
    }
  });

  document.body.addEventListener("htmx:afterSwap", () => syncChipsUI());

  syncChipsUI();
})();
