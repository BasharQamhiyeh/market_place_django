// static/js/post-request-django.js
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

  // ✅ mockup-style error (after block, not weird radio styling)
  function showErrorBelow(elem, message) {
    clearErrors();
    const p = document.createElement("p");
    p.className = "field-error js-error";
    p.textContent = "⚠️ " + message;
    elem.insertAdjacentElement("afterend", p);
    elem.scrollIntoView({ behavior: "smooth", block: "center" });
  }

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

  // ✅ highlight only the container block (attrs), not radios themselves
  function setBlockInvalid(block, on) {
    if (!block) return;
    if (on) {
      block.classList.add("error-border");
    } else {
      block.classList.remove("error-border");
      const next = block.nextElementSibling;
      if (next && next.classList.contains("field-error")) next.remove();
    }
  }

  // ===== Elements =====
  const form = document.getElementById("addRequestForm");

  // ✅ Double-submit protection (doesn't block retry after validation errors)
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

  function lockSubmit() {
    isSubmitting = true;
    if (!submitBtn) return;
    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-60", "cursor-not-allowed");
    submitBtn.setAttribute("aria-busy", "true");
    if (submitBtn.tagName === "BUTTON") submitBtn.textContent = "جاري الإرسال...";
  }

  // ✅ Safety: always allow submitting again when page renders
  unlockSubmit();

  const titleInput = document.getElementById("requestTitle");

  // category
  const levelsRoot = document.getElementById("category-levels");
  const categoryIdInput = document.getElementById("categoryIdInput");
  const attributeFields = document.getElementById("attribute-fields");

  // condition
  const newBtn = document.getElementById("newBtn");
  const usedBtn = document.getElementById("usedBtn");
  const anyBtn = document.getElementById("anyBtn");
  const conditionVal = document.getElementById("conditionValue");

  // desc / budget / ai
  const descField = document.getElementById("desc");
  const budgetField = document.getElementById("budgetField");
  const aiBtn = document.getElementById("aiBtn");

  // city dropdown
  const cityInput = document.getElementById("cityInput");
  const citySelect = document.getElementById("citySelect");
  const cityList = document.getElementById("cityList");
  const citySearch = document.getElementById("citySearch");

  // terms
  const acceptTerms = document.getElementById("acceptTerms");
  const termsBox = document.getElementById("termsBox");

  // popups
  const successPopup = document.getElementById("successPopup");
  const termsPopup = document.getElementById("termsPopup");
  const privacyPopup = document.getElementById("privacyPopup");
  const openTermsLink = document.getElementById("openTerms");
  const openPrivacyLink = document.getElementById("openPrivacy");
  const closeTermsBtn = document.getElementById("closeTerms");
  const closePrivacyBtn = document.getElementById("closePrivacy");

  // ===== Clear errors as user fixes inputs =====
  document.querySelectorAll("#addRequestForm input, #addRequestForm textarea, #addRequestForm select").forEach(field => {
    field.addEventListener("input", () => clearFieldError(field));
    field.addEventListener("change", () => clearFieldError(field));
  });

  // category widget click clears category error
  levelsRoot?.addEventListener("click", () => clearErrorAfterContainer(levelsRoot));

  // city click clears
  cityList?.querySelectorAll("#cityOptions li")?.forEach(li => {
    li.addEventListener("click", () => clearFieldError(cityInput));
  });

  // terms clears
  acceptTerms?.addEventListener("change", () => clearErrorAfterContainer(termsBox));

  // condition clears (if you ever show it there)
  const conditionBox = document.getElementById("conditionBox");
  conditionBox?.addEventListener("click", () => clearErrorAfterContainer(conditionBox));

  // ✅ If user changes anything after an error, re-enable submit
  form?.addEventListener("input", unlockSubmit, { capture: true });
  form?.addEventListener("change", unlockSubmit, { capture: true });

  // ===== REQUIRED ATTRIBUTES VALIDATION (EARLY + MOCKUP STYLE) =====
  function initAttributeRequiredValidation(root) {
    const scope = root || document;

    scope.querySelectorAll(".attr-block").forEach(block => {
      if (block.dataset.reqBound === "1") return;

      block.addEventListener("change", (e) => {
        const t = e.target;
        if (!t) return;
        if (t.matches('input[type="radio"], input[type="checkbox"], select')) {
          setBlockInvalid(block, false);
        }
      });

      block.addEventListener("input", (e) => {
        const t = e.target;
        if (!t) return;
        if (t.matches('input[type="text"], input[type="number"], textarea')) {
          setBlockInvalid(block, false);
        }
      });

      block.dataset.reqBound = "1";
    });
  }

  function validateRequiredAttributes() {
    const blocks = attributeFields?.querySelectorAll(".attr-block[data-required='1']") || [];

    for (const block of blocks) {
      const labelEl = block.querySelector(".label");
      const labelText = labelEl ? labelEl.textContent.trim() : "القيمة";

      const radios = block.querySelectorAll("input[type='radio']");
      if (radios.length) {
        const checked = Array.from(radios).some(r => r.checked);
        if (!checked) {
          setBlockInvalid(block, true);
          showErrorBelow(block, `الرجاء اختيار ${labelText}`);
          return false;
        }
      }

      const checkboxes = block.querySelectorAll("input[type='checkbox']");
      if (checkboxes.length) {
        const checked = Array.from(checkboxes).some(c => c.checked);
        if (!checked) {
          setBlockInvalid(block, true);
          showErrorBelow(block, `الرجاء اختيار ${labelText}`);
          return false;
        }
      }

      const selects = block.querySelectorAll("select");
      if (selects.length) {
        const ok = Array.from(selects).every(s => (s.value || "").trim() !== "");
        if (!ok) {
          setBlockInvalid(block, true);
          showErrorBelow(block, `الرجاء اختيار ${labelText}`);
          return false;
        }
      }

      const txt = block.querySelector("input[type='text'], input[type='number'], textarea");
      if (txt && (txt.value || "").trim() === "") {
        setBlockInvalid(block, true);
        showErrorBelow(block, `الرجاء إدخال ${labelText}`);
        return false;
      }
    }

    return true;
  }

  initAttributeRequiredValidation(attributeFields);

  // ===== Tabs =====
  const termsNav = document.getElementById("termsNav");
  const termsScroll = document.getElementById("termsScroll");
  if (termsNav && termsScroll) {
    const navLinks = termsNav.querySelectorAll(".nav-link");
    const panels = termsScroll.querySelectorAll(".term-panel");
    navLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
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

  // ===== Condition (3 states) =====
  function paintCondition(val) {
    const btns = [newBtn, usedBtn, anyBtn].filter(Boolean);
    btns.forEach(b => { b.style.background = "white"; b.style.color = "var(--muted)"; });

    const chosen = val === "new" ? newBtn : val === "used" ? usedBtn : anyBtn;
    if (chosen) { chosen.style.background = "var(--rukn-orange)"; chosen.style.color = "white"; }
    if (conditionVal) conditionVal.value = val || "any";
  }

  paintCondition((conditionVal?.value || "any") === "new" ? "new" : (conditionVal?.value === "used" ? "used" : "any"));
  newBtn?.addEventListener("click", () => paintCondition("new"));
  usedBtn?.addEventListener("click", () => paintCondition("used"));
  anyBtn?.addEventListener("click", () => paintCondition("any"));

  // ===== City dropdown =====
  function openCity() {
    if (!cityList || !citySearch) return;
    cityList.classList.remove("hidden");
    citySearch.focus();
  }
  function closeCity() {
    cityList?.classList.add("hidden");
  }

  cityInput?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    openCity();
  });

  citySearch?.addEventListener("click", (e) => e.stopPropagation());

  citySearch?.addEventListener("input", () => {
    const val = (citySearch.value || "").toLowerCase();
    const items = cityList?.querySelectorAll("#cityOptions li") || [];
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

  // ===== Categories hierarchical + attributes reload (FIX: clear old attrs + cancel old fetch) =====
  const categoryTree = safeJsonFromScript("category-tree-data") || [];
  const selectedPath = safeJsonFromScript("selected-category-path") || [];

  function nodeName(n) {
    return (n && (n.name || n.name_ar || n.name_en || n.label || n.title || n.text)) || "";
  }
  function nodeChildren(n) {
    return (n && (n.children || n.subcategories || n.subs || n.items || n.nodes)) || [];
  }
  function nodeId(n) {
    const v = (n && (n.id ?? n.pk ?? n.value)) ?? null;
    return v == null ? null : String(v);
  }
  function nodeChildLabel(n) {
    return (n && typeof n.child_label === "string") ? n.child_label.trim() : "";
  }

  function closeAllCategoryPanels(exceptPanel = null) {
    levelsRoot?.querySelectorAll(".cat-panel").forEach(p => {
      if (exceptPanel && p === exceptPanel) return;
      p.classList.add("hidden");
    });
  }

  // ✅ cancel old requests so old attrs can’t come back
  let attrsFetchController = null;

  async function loadAttributesForCategory(categoryId) {
    const tpl = attributeFields?.getAttribute("data-url-template");
    if (!tpl || !attributeFields || !categoryId) return;

    // ✅ remove old attrs immediately
    attributeFields.innerHTML = "";

    // ✅ abort previous fetch
    if (attrsFetchController) attrsFetchController.abort();
    attrsFetchController = new AbortController();

    const url = tpl.replace(/0\/?$/, `${categoryId}/`);

    try {
      const resp = await fetch(url, {
        credentials: "same-origin",
        signal: attrsFetchController.signal,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resp.ok) return;

      attributeFields.innerHTML = await resp.text();

      // re-bind after inject
      initAttributeRequiredValidation(attributeFields);
      initAttributeOtherLogic(attributeFields);
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
      li.dataset.hasChildren = nodeChildren(n).length ? "1" : "0";
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
    function closePanel() {
      panel.classList.add("hidden");
    }

    input.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openPanel();
    });

    panel.addEventListener("click", (e) => e.stopPropagation());
    search.addEventListener("click", (e) => e.stopPropagation());

    search.addEventListener("input", () => {
      const q = (search.value || "").toLowerCase();
      liNodes.forEach(({ li }) => {
        li.style.display = li.textContent.toLowerCase().includes(q) ? "block" : "none";
      });
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

        // ✅ not final level -> clear attrs + abort old fetch
        if (children.length) {
          categoryIdInput.value = "";
          if (attributeFields) attributeFields.innerHTML = "";
          if (attrsFetchController) attrsFetchController.abort();

          const nextLabel = nodeChildLabel(node) || "القسم الفرعي";
          createSearchableLevel(levelIndex + 1, children, nextLabel);
          return;
        }

        categoryIdInput.value = nodeId(node) || "";
        if (categoryIdInput.value) await loadAttributesForCategory(categoryIdInput.value);
      });
    });

    input.addEventListener("keydown", (e) => { if (e.key === "Escape") closePanel(); });
    search.addEventListener("keydown", (e) => { if (e.key === "Escape") closePanel(); });

    panel.appendChild(searchBoxWrap);
    panel.appendChild(ul);

    wrap.appendChild(lbl);
    wrap.appendChild(input);
    wrap.appendChild(panel);
    levelsRoot.appendChild(wrap);
  }

  if (levelsRoot && Array.isArray(categoryTree)) {
    levelsRoot.innerHTML = "";
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

  function initAttributeOtherLogic(root) {
    const scope = root || document;
    const attrsRoot = scope.querySelector("#attrsRoot");
    if (!attrsRoot) return;

    function syncBlock(block) {
      const otherWrap = block.querySelector(".other-wrapper");
      if (!otherWrap) return;
      const name = block.dataset.fieldName;
      if (!name) return;

      const inputs = Array.from(block.querySelectorAll(`input[name="${CSS.escape(name)}"]`));
      if (!inputs.length) return;

      const show = inputs.some(i => i.checked && i.value === "__other__");
      otherWrap.style.display = show ? "block" : "none";
    }

    attrsRoot.querySelectorAll(".attr-block").forEach(syncBlock);

    if (!attrsRoot.dataset.otherBound) {
      attrsRoot.addEventListener("change", (e) => {
        const t = e.target;
        if (!t || t.tagName !== "INPUT") return;
        const block = t.closest(".attr-block");
        if (!block) return;
        syncBlock(block);
      });
      attrsRoot.dataset.otherBound = "1";
    }
  }

  initAttributeOtherLogic(attributeFields);

  // ===== AI (template) =====
  aiBtn?.addEventListener("click", () => {
    const title = (titleInput?.value || "").trim();
    if (!title) {
      showErrorAfter(titleInput, "الرجاء إدخال عنوان لطلب الشراء قبل توليد الوصف");
      return;
    }

    const cond = (conditionVal?.value || "any");
    let conditionText = "لا يهم (جديد أو مستعمل)";
    if (cond === "new") conditionText = "جديد فقط";
    if (cond === "used") conditionText = "مستعمل بحالة جيدة";

    descField.value =
      `🔎 طلب شراء: ${title}\n` +
      `• الحالة المطلوبة: ${conditionText}.\n` +
      `• أفضّل أن يكون المنتج بحالة جيدة وخالٍ من العيوب المؤثرة على الاستخدام.\n` +
      `• أرحّب بالعروض المناسبة ضمن الميزانية المذكورة.\n` +
      `✅ الرجاء تزويدي بتفاصيل المنتج وصور واضحة عند التواصل.`;
  });

  // ===== Popups =====
  function openOverlay(el) {
    if (!el) return;
    el.classList.remove("hidden");
    el.classList.add("flex");
  }
  function closeOverlay(el) {
    if (!el) return;
    el.classList.remove("flex");
    el.classList.add("hidden");
  }

  openTermsLink?.addEventListener("click", (e) => {
    e.preventDefault();
    openOverlay(termsPopup);
  });

  openPrivacyLink?.addEventListener("click", (e) => {
    e.preventDefault();
    openOverlay(privacyPopup);
  });

  closeTermsBtn?.addEventListener("click", () => closeOverlay(termsPopup));
  closePrivacyBtn?.addEventListener("click", () => closeOverlay(privacyPopup));

  document.addEventListener("click", (e) => {
    closeCity();
    if (e.target === termsPopup) closeOverlay(termsPopup);
    if (e.target === privacyPopup) closeOverlay(privacyPopup);
  });

  // ===== Submit validation (keep normal submit to Django) =====
  form?.addEventListener("submit", (e) => {
    if (isSubmitting) {
      e.preventDefault();
      return;
    }

    clearErrors();

    // 1 — Title
    if (!titleInput.value.trim()) {
      e.preventDefault();
      showErrorAfter(titleInput, "الرجاء إدخال عنوان لطلب الشراء");
      unlockSubmit();
      return;
    }

    // 2 — Category
    if (!categoryIdInput.value) {
      e.preventDefault();
      showErrorBelow(levelsRoot, "الرجاء اختيار القسم حتى آخر مستوى");
      unlockSubmit();
      return;
    }

    // ✅ 3 — Attributes (RIGHT AFTER CATEGORY)
    if (!validateRequiredAttributes()) {
      e.preventDefault();
      unlockSubmit();
      return;
    }

    // 4 — Description
    if (!descField.value.trim()) {
      e.preventDefault();
      showErrorAfter(descField, "الرجاء كتابة وصف للمنتج المطلوب أو توليده بالذكاء الاصطناعي");
      unlockSubmit();
      return;
    }

    // 5 — Budget
    if (!budgetField.value) {
      e.preventDefault();
      showErrorAfter(budgetField, "الرجاء إدخال الميزانية القصوى للمنتج المطلوب");
      unlockSubmit();
      return;
    }

    // 6 — City
    if (!citySelect.value) {
      e.preventDefault();
      showErrorAfter(cityInput, "الرجاء اختيار المدينة");
      unlockSubmit();
      return;
    }

    // 7 — Terms
    if (!acceptTerms?.checked) {
      e.preventDefault();
      showErrorBelow(termsBox, "الرجاء الموافقة على شروط نشر طلب الشراء قبل الإرسال");
      unlockSubmit();
      return;
    }

    // Passed
    lockSubmit();
    openOverlay(successPopup);

    const redirectUrl = form.getAttribute("data-redirect-url") || "";
    if (redirectUrl) {
      setTimeout(() => { window.location.href = redirectUrl; }, 12000);
    }
  });
});
