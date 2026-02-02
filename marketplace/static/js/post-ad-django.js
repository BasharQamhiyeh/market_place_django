// static/js/post-ad-django.js
document.addEventListener("DOMContentLoaded", () => {
  // ===== Helpers =====
  function safeJsonFromScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent || "null"); } catch { return null; }
  }

  function clearErrors() {
    document.querySelectorAll(".field-error.js-error").forEach(e => e.remove());
    document.querySelectorAll(".error-border").forEach(e => e.classList.remove("error-border"));
  }

  // Same style as title: red border + message after the control
  function showErrorAfter(field, message) {
    clearErrors();
    field.classList.add("error-border");
    const p = document.createElement("p");
    p.className = "field-error js-error";
    p.textContent = "⚠️ " + message;
    field.insertAdjacentElement("afterend", p);
    field.scrollIntoView({ behavior: "smooth", block: "center" });
    if (typeof field.focus === "function") field.focus();
  }

  // Same style as category container: message after block/container
  function showErrorBelow(elem, message) {
    clearErrors();
    const p = document.createElement("p");
    p.className = "field-error js-error";
    p.textContent = "⚠️ " + message;
    elem.insertAdjacentElement("afterend", p);
    elem.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearFieldError(field) {
    if (!field) return;
    field.classList.remove("error-border");
    const next = field.nextElementSibling;
    if (next && next.classList.contains("field-error")) next.remove();
  }

  function clearErrorAfterContainer(container) {
    if (!container) return;
    container.classList.remove("error-border");
    const next = container.nextElementSibling;
    if (next && next.classList.contains("field-error")) next.remove();
  }

  // for radio/checkbox blocks
  function setBlockInvalid(block, on) {
    if (!block) return;
    if (on) {
      block.classList.add("error-border");
    } else {
      block.classList.remove("error-border");
      const next = block.nextElementSibling;
      if (next && next.classList.contains("field-error") && next.classList.contains("js-error")) next.remove();
    }
  }

  // ✅ IMPORTANT: stop Chrome "Please fill out this field" ONLY for dynamic attributes
  // (no form novalidate needed)
  function stripRequiredFromAttributeFields() {
    if (!attributeFields) return;
    attributeFields
      .querySelectorAll("input[required], select[required], textarea[required]")
      .forEach(el => el.removeAttribute("required"));
  }

  // ===== Elements =====
  const form = document.getElementById("addAdForm");

  let isSubmitting = false;
  const submitBtn = form?.querySelector('button[type="submit"], input[type="submit"]');
  const submitBtnOriginalText = submitBtn?.tagName === "BUTTON" ? submitBtn.textContent : null;

  function unlockSubmit() {
    isSubmitting = false;
    if (!submitBtn) return;
    submitBtn.disabled = false;
    submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
    submitBtn.removeAttribute("aria-busy");
    if (submitBtn.tagName === "BUTTON" && submitBtnOriginalText != null) {
      submitBtn.textContent = submitBtnOriginalText;
    }
  }
  unlockSubmit();

  const titleInput = document.getElementById("adTitle");

  const imageDropzone = document.getElementById("imageDropzone");
  const imageInput = document.getElementById("imageInput");
  const previewContainer = document.getElementById("previewContainer");
  const mainPhotoIndexInput = document.getElementById("main_photo_index");

  // ===== Edit page (existing photos) =====
  const existingPhotos = document.getElementById("existingPhotos"); // container for current photos (optional)
  const selectedMainPhotoInput = document.getElementById("selected_main_photo"); // hidden input (optional)

    // ✅ init: if template didn't set selected_main_photo, read it from the DOM
    if (existingPhotos && selectedMainPhotoInput) {
      if (!(selectedMainPhotoInput.value || "").trim()) {
        const mainBox = existingPhotos.querySelector(".upload-preview.main[data-photo-id]");
        if (mainBox) selectedMainPhotoInput.value = mainBox.getAttribute("data-photo-id") || "";
      }
    }

  const levelsRoot = document.getElementById("category-levels");

    // ✅ Lock category change on edit page BUT allow auto-prefill (programmatic clicks)
    const lockCategoryEl = document.getElementById("lockCategoryEdit");
    const LOCK_CATEGORY = !!lockCategoryEl;

    if (levelsRoot && LOCK_CATEGORY) {
      // Block ONLY user interactions, not JS .click() used for prefill
      levelsRoot.addEventListener(
        "click",
        (e) => {
          if (e.isTrusted) {
            e.preventDefault();
            e.stopPropagation();
          }
        },
        true
      );

      levelsRoot.addEventListener(
        "keydown",
        (e) => {
          if (e.isTrusted) {
            e.preventDefault();
            e.stopPropagation();
          }
        },
        true
      );
    }



  const categoryIdInput = document.getElementById("categoryIdInput");
  const attributeFields = document.getElementById("attribute-fields");

    const listingIdEl = document.getElementById("listingId");
    const listingTypeEl = document.getElementById("listingType"); // "item" or "request"

    // ✅ Edit page: if attributes already rendered with initial values, remember current category
    if (attributeFields && attributeFields.querySelector(".attr-block") && categoryIdInput?.value) {
      attributeFields.dataset.currentCategory = String(categoryIdInput.value);
      attributeFields.dataset.hasInitial = "1";
    }
    const KEEP_INITIAL_ATTRS = !!(attributeFields && attributeFields.dataset.hasInitial === "1");


  const descField = document.getElementById("desc");
  const aiBtn = document.getElementById("aiBtn");
  const priceInput = document.getElementById("priceInput");

  const cityInput = document.getElementById("cityInput");
  const citySelect = document.getElementById("citySelect");
  const cityList = document.getElementById("cityList");
  const citySearch = document.getElementById("citySearch");

  const newBtn = document.getElementById("newBtn");
  const usedBtn = document.getElementById("usedBtn");
  const conditionVal = document.getElementById("conditionValue");

  const acceptTerms = document.getElementById("acceptTerms");
  const termsBox = document.getElementById("termsBox");

  // ===== Clear errors as user fixes inputs =====
  document.querySelectorAll("#addAdForm input, #addAdForm textarea, #addAdForm select").forEach(field => {
    field.addEventListener("input", () => clearFieldError(field));
    field.addEventListener("change", () => clearFieldError(field));
  });

  imageInput?.addEventListener("change", () => clearFieldError(imageDropzone));
  previewContainer?.addEventListener("click", () => clearFieldError(previewContainer));
  levelsRoot?.addEventListener("click", () => clearErrorAfterContainer(levelsRoot));

  cityList?.querySelectorAll("#cityOptions li")?.forEach(li => {
    li.addEventListener("click", () => clearFieldError(cityInput));
  });

  acceptTerms?.addEventListener("change", () => clearErrorAfterContainer(termsBox));

  form?.addEventListener("input", unlockSubmit, { capture: true });
  form?.addEventListener("change", unlockSubmit, { capture: true });

  // ===== Dynamic attributes: OTHER toggle + clear its errors =====
  function isOtherWrapperVisible(otherWrap) {
    if (!otherWrap) return false;
    if (otherWrap.classList.contains("hidden")) return false;
    const ds = (otherWrap.style && otherWrap.style.display) || "";
    if (ds && ds.toLowerCase() === "none") return false;
    return otherWrap.offsetParent !== null;
  }

  function initAttributeLogic(root) {
    const scope = root || document;
    const attrsRoot = scope.querySelector("#attrsRoot");
    if (!attrsRoot) return;

    function syncOtherForBlock(block) {
  const otherWrap = block.querySelector(".other-wrapper");
  if (!otherWrap) return;

  const name = block.dataset.fieldName;
  if (!name) return;

  const otherInput = otherWrap.querySelector("input, textarea, select");
  const otherHasText = !!(otherInput && (otherInput.value || "").trim());

  // detect if "__other__" is selected NOW (never force it here)
  let isOtherSelected = false;

  const sel = block.querySelector(`select[name="${CSS.escape(name)}"]`);
  if (sel) {
    if (sel.multiple) {
      isOtherSelected = Array.from(sel.selectedOptions).some(o => o.value === "__other__");
    } else {
      isOtherSelected = (sel.value || "") === "__other__";
    }
  } else {
    const inputs = Array.from(block.querySelectorAll(`input[name="${CSS.escape(name)}"]`));
    isOtherSelected = inputs.some(i => i.checked && i.value === "__other__");
  }

  // show/hide OTHER field only based on selection
  otherWrap.style.display = isOtherSelected ? "block" : "none";
  otherWrap.classList.toggle("hidden", !isOtherSelected);

  // if user selected other, keep whatever value exists visible/editable
  // if user selected something else, KEEP the value but just hide it (so they can change without deleting)
}




    attrsRoot.querySelectorAll(".attr-block").forEach(block => {
      if (block.dataset.bound === "1") return;

      block.addEventListener("input", (e) => {
        const t = e.target;
        if (!t) return;
        clearFieldError(t);
        setBlockInvalid(block, false);
      }, true);

      block.addEventListener("change", (e) => {
        const t = e.target;
        if (!t) return;
        clearFieldError(t);
        setBlockInvalid(block, false);
        if (t.matches('input[type="radio"], input[type="checkbox"], select')) {
          syncOtherForBlock(block);
        }
      }, true);

      block.dataset.bound = "1";

// ✅ PREFILL ONCE: if OTHER input has text, select "__other__" ONCE at page load
if (block.dataset.otherInitDone !== "1") {
  const otherWrap = block.querySelector(".other-wrapper");
  const otherInput = otherWrap?.querySelector("input, textarea, select");
  const otherHasText = !!(otherInput && (otherInput.value || "").trim());

  if (otherHasText) {
    const name = block.dataset.fieldName;

    // If select exists
    const sel = block.querySelector(`select[name="${CSS.escape(name)}"]`);
    if (sel) {
      if (sel.multiple) {
        const opt = Array.from(sel.options).find(o => o.value === "__other__");
        if (opt) opt.selected = true;
      } else {
        sel.value = "__other__";
      }
    } else {
      // Radio/checkbox: check "__other__"
      const otherChoice = block.querySelector(
        `input[name="${CSS.escape(name)}"][value="__other__"]`
      );
      if (otherChoice) otherChoice.checked = true;
    }
  }

  block.dataset.otherInitDone = "1";
}

syncOtherForBlock(block);


    });

    if (!attrsRoot.dataset.otherBound) {
      attrsRoot.addEventListener("change", (e) => {
        const t = e.target;
        if (!t) return;
        const block = t.closest(".attr-block");
        if (!block) return;
        if (t.matches('input[type="radio"], input[type="checkbox"], select')) {
          syncOtherForBlock(block);
        }
      }, true);
      attrsRoot.dataset.otherBound = "1";
    }
  }

  function validateRequiredAttributes() {
    const blocks = Array.from(attributeFields?.querySelectorAll(".attr-block[data-required='1']") || []);

    for (const block of blocks) {
      const labelEl = block.querySelector(".label");
      const labelText = labelEl ? labelEl.textContent.trim() : "القيمة";

      const mainRadios = Array.from(block.querySelectorAll(":scope input[type='radio']:not(.other-wrapper input)"));
      const mainCheckboxes = Array.from(block.querySelectorAll(":scope input[type='checkbox']:not(.other-wrapper input)"));
      const mainSelect = block.querySelector(":scope select:not(.other-wrapper select)");
      const mainText = block.querySelector(":scope input[type='text']:not(.other-wrapper input), :scope input[type='number']:not(.other-wrapper input), :scope textarea:not(.other-wrapper textarea)");

      if (mainRadios.length) {
        const ok = mainRadios.some(r => r.checked);
        if (!ok) {
          setBlockInvalid(block, true);
          showErrorBelow(block, `الرجاء اختيار ${labelText}`);
          return false;
        }
      } else if (mainCheckboxes.length) {
        const ok = mainCheckboxes.some(c => c.checked);
        if (!ok) {
          setBlockInvalid(block, true);
          showErrorBelow(block, `الرجاء اختيار ${labelText}`);
          return false;
        }
      } else if (mainSelect) {
        if (!(mainSelect.value || "").trim()) {
          showErrorAfter(mainSelect, `الرجاء اختيار ${labelText}`);
          return false;
        }
      } else if (mainText) {
        if (!((mainText.value || "").trim())) {
          showErrorAfter(mainText, `الرجاء إدخال ${labelText}`);
          return false;
        }
      }

      const otherWrap = block.querySelector(".other-wrapper");
      if (otherWrap && isOtherWrapperVisible(otherWrap)) {
        const otherInput = otherWrap.querySelector("input[type='text'], input[type='number'], textarea");
        if (otherInput && !((otherInput.value || "").trim())) {
          showErrorAfter(otherInput, `الرجاء إدخال ${labelText}`);
          return false;
        }
      }
    }

    return true;
  }

  // init once on first render
  stripRequiredFromAttributeFields();      // ✅ add
  initAttributeLogic(attributeFields);

  // ===== Tabs =====
  const termsNav = document.getElementById("termsNav");
  const termsScroll = document.getElementById("termsScroll");
  if (termsNav && termsScroll) {
    const navLinks = termsNav.querySelectorAll(".nav-link");
    const panels = termsScroll.querySelectorAll(".term-panel");
    navLinks.forEach(link => {
      link.addEventListener("click", () => {
        const tab = link.getAttribute("data-tab");
        navLinks.forEach(l => l.classList.remove("active"));
        link.classList.add("active");
        panels.forEach(panel => {
          if (panel.getAttribute("data-tab") === tab) {
            panel.classList.add("active");
            panel.classList.remove("hidden");
          } else {
            panel.classList.remove("active");
            panel.classList.add("hidden");
          }
        });
      });
    });
  }

  // ===== Condition =====
  function paintCondition(val) {
    if (!newBtn || !usedBtn || !conditionVal) return;
    if (val === "used") {
      usedBtn.style.background = "var(--rukn-orange)";
      usedBtn.style.color = "white";
      newBtn.style.background = "white";
      newBtn.style.color = "var(--muted)";
      conditionVal.value = "used";
    } else {
      newBtn.style.background = "var(--rukn-orange)";
      newBtn.style.color = "white";
      usedBtn.style.background = "white";
      usedBtn.style.color = "var(--muted)";
      conditionVal.value = "new";
    }
  }
  paintCondition(conditionVal?.value === "used" ? "used" : "new");
  newBtn?.addEventListener("click", () => paintCondition("new"));
  usedBtn?.addEventListener("click", () => paintCondition("used"));

  // ===== Images =====
  let filesState = [];

  function syncInputFiles() {
    const dt = new DataTransfer();
    filesState.forEach(f => dt.items.add(f));
    imageInput.files = dt.files;
  }

  function setMainIndex(idxOrNull) {
    if (idxOrNull === null || idxOrNull === undefined) mainPhotoIndexInput.value = "";
    else mainPhotoIndexInput.value = String(idxOrNull);
  }

  function renderPreviews() {
    previewContainer.innerHTML = "";
    filesState.forEach((file, idx) => {
      const div = document.createElement("div");
      div.className = "upload-preview";
      if (mainPhotoIndexInput.value !== "" && Number(mainPhotoIndexInput.value) === idx) div.classList.add("main");

      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);

      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "✕";

      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const curMain = mainPhotoIndexInput.value === "" ? null : Number(mainPhotoIndexInput.value);
        filesState.splice(idx, 1);
        if (curMain === idx) setMainIndex(null);
        else if (curMain !== null && curMain > idx) setMainIndex(curMain - 1);
        syncInputFiles();
        renderPreviews();
      });

      div.addEventListener("click", () => {
          setMainIndex(idx);

          // ✅ new main chosen => clear existing main selection + remove its UI highlight
          if (selectedMainPhotoInput) selectedMainPhotoInput.value = "";
          if (existingPhotos) {
            existingPhotos.querySelectorAll(".upload-preview.main").forEach(el => el.classList.remove("main"));
          }

          renderPreviews();
        });



      div.appendChild(img);
      div.appendChild(btn);
      previewContainer.appendChild(div);
    });
  }

    // ===== Existing photos: choose main (edit) =====
    // ===== Existing photos (edit): same UI as new previews =====
  if (existingPhotos && selectedMainPhotoInput) {
    existingPhotos.addEventListener("click", (e) => {
      const removeBtn = e.target.closest(".js-remove-existing");
      if (removeBtn) {
        e.preventDefault();
        e.stopPropagation();

        const pid = removeBtn.getAttribute("data-photo-id");
        if (!pid) return;

        // tick the hidden checkbox so backend deletes it
        const cb = document.getElementById(`delete_photo_${pid}`);
        if (cb) cb.checked = true;

        // remove preview from UI
        const box = existingPhotos.querySelector(`.upload-preview[data-photo-id="${pid}"]`);
        if (box) box.remove();

        // if we removed the selected main, clear it
        if ((selectedMainPhotoInput.value || "") === String(pid)) {
          selectedMainPhotoInput.value = "";
        }

        // if nothing selected as main anymore, try to select first remaining existing photo
        const first = existingPhotos.querySelector(".upload-preview[data-photo-id]");
        if (first && !selectedMainPhotoInput.value) {
          const firstId = first.getAttribute("data-photo-id");
          selectedMainPhotoInput.value = firstId || "";
          first.classList.add("main");
        }

        return;
      }

      const box = e.target.closest(".upload-preview[data-photo-id]");
      if (!box) return;

      // set main on existing
      existingPhotos.querySelectorAll(".upload-preview").forEach(p => p.classList.remove("main"));
      box.classList.add("main");

      const pid = box.getAttribute("data-photo-id");
      selectedMainPhotoInput.value = pid || "";

      // if main chosen from existing => clear main index of new uploads
      if (mainPhotoIndexInput) mainPhotoIndexInput.value = "";

      // remove "main" highlight from new previews if any
      renderPreviews();
    });
  }



  imageDropzone?.addEventListener("click", (e) => {
    e.preventDefault();
    imageInput.click();
  });

  imageInput?.addEventListener("change", () => {
    const files = Array.from(imageInput.files || []);
    if (!files.length) return;
    filesState = filesState.concat(files.filter(f => f && f.type && f.type.startsWith("image/")));
    syncInputFiles();
    renderPreviews();
  });

  imageDropzone?.addEventListener("dragover", (e) => {
    e.preventDefault();
    imageDropzone.classList.add("ring-2", "ring-[var(--rukn-orange)]", "bg-orange-50");
  });
  imageDropzone?.addEventListener("dragleave", (e) => {
    e.preventDefault();
    imageDropzone.classList.remove("ring-2", "ring-[var(--rukn-orange)]", "bg-orange-50");
  });
  imageDropzone?.addEventListener("drop", (e) => {
    e.preventDefault();
    imageDropzone.classList.remove("ring-2", "ring-[var(--rukn-orange)]", "bg-orange-50");
    const files = Array.from(e.dataTransfer?.files || []);
    if (!files.length) return;
    filesState = filesState.concat(files.filter(f => f && f.type && f.type.startsWith("image/")));
    syncInputFiles();
    renderPreviews();
  });

  // ===== City dropdown =====
  function openCity() { cityList.classList.remove("hidden"); citySearch.focus(); }
  function closeCity() { cityList.classList.add("hidden"); }

  cityInput?.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); openCity(); });
  citySearch?.addEventListener("click", (e) => e.stopPropagation());

  citySearch?.addEventListener("input", () => {
    const val = (citySearch.value || "").toLowerCase();
    const items = cityList.querySelectorAll("#cityOptions li");
    items.forEach(li => { li.style.display = li.textContent.toLowerCase().includes(val) ? "block" : "none"; });
  });

  cityList?.querySelectorAll("#cityOptions li")?.forEach(li => {
    li.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      cityInput.value = li.textContent.trim();
      citySelect.value = li.dataset.value || "";
      closeCity();
    });
  });

  // ===== Categories hierarchical + attributes reload =====
  const categoryTree = safeJsonFromScript("category-tree-data") || [];
  const selectedPath = safeJsonFromScript("selected-category-path") || [];
  const categoryDynamicHint = document.getElementById("categoryDynamicHint");

  function nodeName(n) { return (n && (n.name || n.name_ar || n.name_en || n.label || n.title || n.text)) || ""; }
  function nodeChildren(n) { return (n && (n.children || n.subcategories || n.subs || n.items || n.nodes)) || []; }
  function nodeId(n) { const v = (n && (n.id ?? n.pk ?? n.value)) ?? null; return v == null ? null : String(v); }
  function nodeChildLabel(n) { return (n && typeof n.child_label === "string") ? n.child_label.trim() : ""; }

  function setHint(text) {
    if (!categoryDynamicHint) return;
    const t = (text || "").trim();
    if (!t) { categoryDynamicHint.textContent = ""; categoryDynamicHint.classList.add("hidden"); return; }
    categoryDynamicHint.textContent = t;
    categoryDynamicHint.classList.remove("hidden");
  }

  function closeAllCategoryPanels(exceptPanel = null) {
    levelsRoot.querySelectorAll(".cat-panel").forEach(p => {
      if (exceptPanel && p === exceptPanel) return;
      p.classList.add("hidden");
    });
  }

  let attrsFetchController = null;

  async function loadAttributesForCategory(categoryId) {
    const tpl = attributeFields?.getAttribute("data-url-template");
    if (!tpl || !attributeFields || !categoryId) return;

    if (!KEEP_INITIAL_ATTRS) attributeFields.innerHTML = "";

    if (attrsFetchController) attrsFetchController.abort();
    attrsFetchController = new AbortController();

    const baseUrl = tpl.replace(/0\/?$/, `${categoryId}/`);

    const qs = new URLSearchParams();

    // ✅ pass listing_id + kind so backend can load correct instance (item/request)
    if (listingIdEl && (listingIdEl.value || "").trim()) qs.set("listing_id", listingIdEl.value.trim());
    if (listingTypeEl && (listingTypeEl.value || "").trim()) qs.set("kind", listingTypeEl.value.trim());

    const url = qs.toString() ? `${baseUrl}?${qs.toString()}` : baseUrl;

    try {
      const resp = await fetch(url, {
        credentials: "same-origin",
        signal: attrsFetchController.signal,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resp.ok) return;

      attributeFields.innerHTML = await resp.text();

      stripRequiredFromAttributeFields();   // ✅ add (prevents Chrome popup)
      initAttributeLogic(attributeFields);
    } catch (err) {
      if (err && err.name === "AbortError") return;
    }
  }

  function createSearchableLevel(levelIndex, nodes, labelText) {
    const wrap = document.createElement("div");
    wrap.className = "space-y-1";
    wrap.dataset.levelWrap = String(levelIndex);

    const lbl = document.createElement("label");
    lbl.className = "label";
    lbl.textContent = (labelText || "").trim() || (levelIndex === 0 ? "القسم" : "القسم الفرعي");

    const input = document.createElement("input");
    input.type = "text";
    input.readOnly = true;
    input.className = "input-field cursor-pointer text-sm";
    input.placeholder = levelIndex === 0 ? "اختر القسم الرئيسي" : (labelText ? `اختر ${labelText}` : "اختر القسم الفرعي");
    input.dataset.level = String(levelIndex);

    const panel = document.createElement("div");
    panel.className = "cat-panel mt-2 w-full bg-white border border-orange-200 rounded-xl shadow-lg hidden";
    panel.style.position = "relative";
    panel.style.zIndex = "9999";

    const searchBoxWrap = document.createElement("div");
    searchBoxWrap.className = "p-2 border-b border-orange-100";

    const search = document.createElement("input");
    search.type = "text";
    search.placeholder = "🔍 بحث...";
    search.className = "w-full border border-orange-100 rounded-lg py-1.5 px-3 text-sm";
    searchBoxWrap.appendChild(search);

    const ul = document.createElement("ul");
    ul.className = "max-h-52 overflow-y-auto text-sm";

    const liNodes = nodes.map(n => {
      const li = document.createElement("li");
      li.className = "p-2 hover:bg-orange-50 cursor-pointer";
      li.textContent = nodeName(n);
      li.dataset.id = nodeId(n) || "";
      ul.appendChild(li);
      return { li, node: n, inputRef: input };
    });

    function openPanel() {
      closeAllCategoryPanels(panel);
      panel.classList.remove("hidden");
      search.value = "";
      liNodes.forEach(({ li }) => { li.style.display = "block"; });
      setTimeout(() => search.focus(), 0);
    }
    function closePanel() { panel.classList.add("hidden"); }

    input.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); openPanel(); });
    panel.addEventListener("click", (e) => e.stopPropagation());
    search.addEventListener("click", (e) => e.stopPropagation());

    search.addEventListener("input", () => {
      const q = (search.value || "").toLowerCase();
      liNodes.forEach(({ li }) => { li.style.display = li.textContent.toLowerCase().includes(q) ? "block" : "none"; });
    });

    liNodes.forEach(({ li, node, inputRef }) => {
      li.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();

        clearErrorAfterContainer(levelsRoot);

        inputRef.value = nodeName(node);
        closePanel();

        Array.from(levelsRoot.querySelectorAll("[data-level-wrap]"))
          .filter(w => Number(w.dataset.levelWrap) > levelIndex)
          .forEach(w => w.remove());

        const children = nodeChildren(node);

        if (children.length) {
          categoryIdInput.value = "";

          // ✅ لا تمسح الـ attributes المعبّاية في صفحة التعديل أثناء بناء المسار
          if (attributeFields && !KEEP_INITIAL_ATTRS) attributeFields.innerHTML = "";

          if (attrsFetchController) attrsFetchController.abort();

          const nextLabel = nodeChildLabel(node) || "القسم الفرعي";
          setHint(nodeChildLabel(node));
          createSearchableLevel(levelIndex + 1, children, nextLabel);
          return;
        }



        setHint("");
        const newCatId = nodeId(node) || "";
        categoryIdInput.value = newCatId;

        // ✅ if we already have initial attributes rendered for same category (edit page), don't reload
        if (
          attributeFields &&
          attributeFields.dataset.hasInitial === "1" &&
          attributeFields.dataset.currentCategory === newCatId &&
          attributeFields.querySelector(".attr-block")
        ) {
          return;
        }

        if (attributeFields) {
          attributeFields.dataset.currentCategory = newCatId;
          attributeFields.dataset.hasInitial = "0";
        }

        if (newCatId) await loadAttributesForCategory(newCatId);


      });
    });

    panel.appendChild(searchBoxWrap);
    panel.appendChild(ul);
    wrap.appendChild(lbl);
    wrap.appendChild(input);
    wrap.appendChild(panel);
    levelsRoot.appendChild(wrap);
  }

  if (levelsRoot && Array.isArray(categoryTree)) {
    levelsRoot.innerHTML = "";
    setHint("");
    createSearchableLevel(0, categoryTree, "القسم");
    document.addEventListener("click", () => closeAllCategoryPanels(), { capture: true });

    if (Array.isArray(selectedPath) && selectedPath.length) {
      const pathIds = selectedPath.map(x => (typeof x === "object" ? String(x.id ?? x.pk ?? x.value ?? "") : String(x)));
      let currentNodes = categoryTree;

      for (let level = 0; level < pathIds.length; level++) {
        const id = pathIds[level];
        const wrap = levelsRoot.querySelector(`[data-level-wrap="${level}"]`);
        if (!wrap) break;
        const li = wrap.querySelector(`li[data-id="${id}"]`);
        if (!li) break;
        li.click();
        const chosen = currentNodes.find(n => nodeId(n) === id);
        if (!chosen) break;
        currentNodes = nodeChildren(chosen);
      }
    }
  }

  document.addEventListener("click", () => closeCity());

  // ===== AI =====
  aiBtn?.addEventListener("click", () => {
    const title = (titleInput?.value || "").trim();
    if (!title) {
      showErrorAfter(titleInput, "الرجاء إدخال عنوان الإعلان قبل توليد الوصف");
      return;
    }

    const hasNewImages = filesState.length > 0;
    const hasExistingImages = !!(existingPhotos && existingPhotos.querySelector(".upload-preview[data-photo-id]"));

    if (!hasNewImages && !hasExistingImages) {
      showErrorBelow(imageDropzone, "الرجاء إضافة صور للإعلان");
      return;
    }



    const condTxt = conditionVal?.value === "used" ? "مستعمل بحالة جيدة" : "جديد وغير مستخدم";
    descField.value =
      `📦 ${title}\n` +
      `• الحالة: ${condTxt}\n` +
      `• المنتج بحالة ممتازة ومرفق صور واضحة.\n` +
      `✅ تواصل للشراء أو الاستفسار.`;
  });

  // ===== Submit validation =====
  form?.addEventListener("submit", (e) => {
    if (isSubmitting) {
      e.preventDefault();
      return;
    }

    unlockSubmit();
    clearErrors();

    if (!titleInput.value.trim()) {
      e.preventDefault();
      showErrorAfter(titleInput, "الرجاء إدخال عنوان الإعلان");
      unlockSubmit();
      return;
    }

    if (!categoryIdInput.value) {
      e.preventDefault();
      showErrorBelow(levelsRoot, "الرجاء اختيار القسم حتى آخر مستوى");
      unlockSubmit();
      return;
    }

    if (!validateRequiredAttributes()) {
      e.preventDefault();
      unlockSubmit();
      return;
    }

    const hasNewImages = filesState.length > 0;
    const hasExistingImages = !!(
      existingPhotos &&
      existingPhotos.querySelector(".upload-preview[data-photo-id]")
    );

    if (!hasNewImages && !hasExistingImages) {
      e.preventDefault();
      showErrorBelow(imageDropzone, "الرجاء إضافة صور للإعلان");
      unlockSubmit();
      return;
    }




    const hasMainNew = mainPhotoIndexInput && mainPhotoIndexInput.value !== "";
    const hasMainExisting = selectedMainPhotoInput && (selectedMainPhotoInput.value || "").trim() !== "";

    // In edit: allow existing main or new main
    if (!hasMainNew && !hasMainExisting) {
      e.preventDefault();
      showErrorBelow(previewContainer, "الرجاء اختيار صورة رئيسية");
      unlockSubmit();
      return;
    }


    if (!descField.value.trim()) {
      e.preventDefault();
      showErrorAfter(descField, "الرجاء كتابة وصف للمنتج");
      unlockSubmit();
      return;
    }

    if (!priceInput.value) {
      e.preventDefault();
      showErrorAfter(priceInput, "الرجاء إدخال السعر");
      unlockSubmit();
      return;
    }

    if (!citySelect.value) {
      e.preventDefault();
      showErrorAfter(cityInput, "الرجاء اختيار المدينة");
      unlockSubmit();
      return;
    }

    // ✅ Always require accepting terms (create + edit)
    if (!acceptTerms) {
      e.preventDefault();
      alert("Checkbox acceptTerms is missing from the page HTML.");
      unlockSubmit();
      return;
    }

    if (!acceptTerms.checked) {
      e.preventDefault();
      showErrorBelow(termsBox || acceptTerms, "الرجاء الموافقة على الشروط قبل الحفظ");
      unlockSubmit();
      return;
    }


    isSubmitting = true;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add("opacity-60", "cursor-not-allowed");
      submitBtn.setAttribute("aria-busy", "true");
      if (submitBtn.tagName === "BUTTON") submitBtn.textContent = "جاري الإرسال...";
    }
  });
});
