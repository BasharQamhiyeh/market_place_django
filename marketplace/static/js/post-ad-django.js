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

  function showErrorBelow(elem, message) {
    clearErrors();
    const p = document.createElement("p");
    p.className = "field-error js-error";
    p.textContent = "⚠️ " + message;
    elem.insertAdjacentElement("afterend", p);
    elem.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // ===== Elements =====
  const form = document.getElementById("addAdForm");

  const titleInput = document.getElementById("adTitle");

  const imageDropzone = document.getElementById("imageDropzone");
  const imageInput = document.getElementById("imageInput");
  const previewContainer = document.getElementById("previewContainer");
  const mainPhotoIndexInput = document.getElementById("main_photo_index");

  const levelsRoot = document.getElementById("category-levels");
  const categoryIdInput = document.getElementById("categoryIdInput");
  const attributeFields = document.getElementById("attribute-fields");

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

  // ===== Images (real input sync + main selection) =====
  let filesState = [];

  function syncInputFiles() {
    const dt = new DataTransfer();
    filesState.forEach(f => dt.items.add(f));
    imageInput.files = dt.files;
  }

  function setMainIndex(idxOrNull) {
    if (idxOrNull === null || idxOrNull === undefined) {
      mainPhotoIndexInput.value = "";
    } else {
      mainPhotoIndexInput.value = String(idxOrNull);
    }
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
        renderPreviews();
      });

      div.appendChild(img);
      div.appendChild(btn);
      previewContainer.appendChild(div);
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

      // ✅ keep the real input (this is what Django submits)
      syncInputFiles();
      renderPreviews();

      // ❌ DO NOT clear imageInput.value here
      // imageInput.value = "";
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

  // ===== City dropdown (mockup behavior) =====
  function openCity() {
    cityList.classList.remove("hidden");
    citySearch.focus();
  }
  function closeCity() {
    cityList.classList.add("hidden");
  }

  cityInput?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    openCity();
  });

  citySearch?.addEventListener("click", (e) => e.stopPropagation());

  citySearch?.addEventListener("input", () => {
    const val = (citySearch.value || "").toLowerCase();
    const items = cityList.querySelectorAll("#cityOptions li");
    items.forEach(li => {
      li.style.display = li.textContent.toLowerCase().includes(val) ? "block" : "none";
    });
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

  // ===== Categories hierarchical (parent -> sub -> sub) EXACT behavior =====
    const categoryTree = safeJsonFromScript("category-tree-data") || [];
    const selectedPath = safeJsonFromScript("selected-category-path") || [];

    // (optional hint line) if you added: <p id="categoryDynamicHint" ...></p>
    const categoryDynamicHint = document.getElementById("categoryDynamicHint");

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

    function setHint(text) {
      if (!categoryDynamicHint) return;
      const t = (text || "").trim();
      if (!t) {
        categoryDynamicHint.textContent = "";
        categoryDynamicHint.classList.add("hidden");
        return;
      }
      categoryDynamicHint.textContent = t;
      categoryDynamicHint.classList.remove("hidden");
    }



    function closeAllCategoryPanels(exceptPanel = null) {
      levelsRoot.querySelectorAll(".cat-panel").forEach(p => {
        if (exceptPanel && p === exceptPanel) return;
        p.classList.add("hidden");
      });
    }

    function createSearchableLevel(levelIndex, nodes, labelText) {
      const wrap = document.createElement("div");
      wrap.className = "space-y-1";
      wrap.dataset.levelWrap = String(levelIndex);

      const lbl = document.createElement("label");
      lbl.className = "label";
      lbl.textContent = (labelText || "").trim() || (levelIndex === 0 ? "القسم" : "القسم الفرعي");

      // input that opens panel
      const input = document.createElement("input");
      input.type = "text";
      input.readOnly = true;
      input.className = "input-field cursor-pointer text-sm";
      input.placeholder = levelIndex === 0 ? "اختر القسم الرئيسي" : (labelText ? `اختر ${labelText}` : "اختر القسم الفرعي");
      input.dataset.level = String(levelIndex);

      // dropdown panel
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

      // render list items
      const liNodes = nodes.map(n => {
        const li = document.createElement("li");
        li.className = "p-2 hover:bg-orange-50 cursor-pointer";
        li.textContent = nodeName(n);
        li.dataset.id = nodeId(n) || "";
        li.dataset.hasChildren = nodeChildren(n).length ? "1" : "0";
        ul.appendChild(li);
        return { li, node: n };
      });

      function openPanel() {
        closeAllCategoryPanels(panel);
        panel.classList.remove("hidden");
        search.value = "";
        // show all
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

      liNodes.forEach(({ li, node }) => {
        li.addEventListener("click", async (e) => {
          e.preventDefault();
          e.stopPropagation();

          // select
          input.value = nodeName(node);
          closePanel();

          // remove deeper levels
          Array.from(levelsRoot.querySelectorAll("[data-level-wrap]"))
            .filter(w => Number(w.dataset.levelWrap) > levelIndex)
            .forEach(w => w.remove());

          const children = nodeChildren(node);

          if (children.length) {
            categoryIdInput.value = "";
            const nextLabel = nodeChildLabel(node) || "القسم الفرعي";
            setHint(nodeChildLabel(node)); // optional hint line like mockup
            createSearchableLevel(levelIndex + 1, children, nextLabel);
            return;
          }

          // leaf
          setHint("");
          categoryIdInput.value = nodeId(node) || "";
          if (categoryIdInput.value) await loadAttributesForCategory(categoryIdInput.value);
        });
      });

      // ESC closes
      input.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closePanel();
      });
      search.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closePanel();
      });

      panel.appendChild(searchBoxWrap);
      panel.appendChild(ul);

      wrap.appendChild(lbl);
      wrap.appendChild(input);
      wrap.appendChild(panel);
      levelsRoot.appendChild(wrap);

      return { wrap, input, panel };
    }

    if (levelsRoot && Array.isArray(categoryTree)) {
      levelsRoot.innerHTML = "";
      setHint("");
      createSearchableLevel(0, categoryTree, "القسم");

      // outside click closes panels
      document.addEventListener("click", () => closeAllCategoryPanels(), { capture: true });

      // preselect path if provided (best-effort)
      if (Array.isArray(selectedPath) && selectedPath.length) {
        const pathIds = selectedPath.map(x => (typeof x === "object" ? String(x.id ?? x.pk ?? x.value ?? "") : String(x)));
        let currentNodes = categoryTree;

        for (let level = 0; level < pathIds.length; level++) {
          const id = pathIds[level];

          // find wrap for this level
          const wrap = levelsRoot.querySelector(`[data-level-wrap="${level}"]`);
          if (!wrap) break;

          const input = wrap.querySelector(`input[data-level="${level}"]`);
          const li = wrap.querySelector(`li[data-id="${id}"]`);
          if (!input || !li) break;

          // simulate click selection on li
          li.click();

          // update currentNodes for next loop
          const chosen = currentNodes.find(n => nodeId(n) === id);
          if (!chosen) break;
          currentNodes = nodeChildren(chosen);
        }
      }
    }


async function loadAttributesForCategory(categoryId) {
  const tpl = attributeFields?.getAttribute("data-url-template");
  if (!tpl || !categoryId) return;

  const url = tpl.replace(/0\/?$/, `${categoryId}/`);

  try {
    const resp = await fetch(url, { credentials: "same-origin" });
    if (!resp.ok) return;

    attributeFields.innerHTML = await resp.text();

    // ✅ after replacing the partial, toggle "Other" for anything already selected
    initAttributeOtherLogic(attributeFields);
  } catch {}
}

    function initAttributeOtherLogic(root) {
      const scope = root || document;
      const attrsRoot = scope.querySelector("#attrsRoot");
      if (!attrsRoot) return;

      // 1) RADIO / CHECKBOX: show/hide the other-wrapper
      function syncBlock(block) {
        const otherWrap = block.querySelector(".other-wrapper");
        if (!otherWrap) return;

        const name = block.dataset.fieldName;
        if (!name) return;

        const inputs = Array.from(block.querySelectorAll(`input[name="${CSS.escape(name)}"]`));

        // ✅ if there are no inputs, it might be a <select> (dropdown) — ignore here
        if (!inputs.length) return;

        const show = inputs.some(i => i.checked && i.value === "__other__");
        otherWrap.style.display = show ? "block" : "none";
      }

      attrsRoot.querySelectorAll(".attr-block").forEach(syncBlock);

      // ✅ delegate change listener ONCE per load to handle clicks after render
      // (avoid stacking listeners)
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

// ✅ ADD THIS ONE LINE once, RIGHT AFTER the function definitions above,
// so "Other" works on initial GET render too (not only after category fetch):
initAttributeOtherLogic(attributeFields);

  // ===== Close dropdowns on outside click =====
  document.addEventListener("click", () => {
    closeCity();
  });

  // ===== AI =====
  aiBtn?.addEventListener("click", () => {
    const title = (titleInput?.value || "").trim();
    if (!title) {
      showErrorAfter(titleInput, "الرجاء إدخال عنوان الإعلان قبل توليد الوصف");
      return;
    }
    if (!filesState.length) {
      showErrorBelow(imageDropzone, "الرجاء إضافة صور للإعلان قبل توليد الوصف");
      return;
    }

    const condTxt = conditionVal?.value === "used" ? "مستعمل بحالة جيدة" : "جديد وغير مستخدم";
    descField.value =
      `📦 ${title}\n` +
      `• الحالة: ${condTxt}\n` +
      `• المنتج بحالة ممتازة ومرفق صور واضحة.\n` +
      `✅ تواصل للشراء أو الاستفسار.`;
  });

  // ===== Submit validation (keep normal submit to Django) =====
  form?.addEventListener("submit", (e) => {
    clearErrors();

    if (!titleInput.value.trim()) {
      e.preventDefault();
      showErrorAfter(titleInput, "الرجاء إدخال عنوان الإعلان");
      return;
    }

    if (!filesState.length) {
      e.preventDefault();
      showErrorBelow(imageDropzone, "الرجاء إضافة صور للإعلان");
      return;
    }

    if (mainPhotoIndexInput.value === "") {
      e.preventDefault();
      showErrorBelow(previewContainer, "الرجاء اختيار صورة رئيسية");
      return;
    }

    if (!categoryIdInput.value) {
      e.preventDefault();
      showErrorBelow(levelsRoot, "الرجاء اختيار القسم حتى آخر مستوى");
      return;
    }

    if (!descField.value.trim()) {
      e.preventDefault();
      showErrorAfter(descField, "الرجاء كتابة وصف للمنتج");
      return;
    }

    if (!priceInput.value) {
      e.preventDefault();
      showErrorAfter(priceInput, "الرجاء إدخال السعر");
      return;
    }

    if (!citySelect.value) {
      e.preventDefault();
      showErrorAfter(cityInput, "الرجاء اختيار المدينة");
      return;
    }

    if (!acceptTerms.checked) {
      e.preventDefault();
      showErrorBelow(termsBox, "الرجاء الموافقة على الشروط قبل النشر");
      return;
    }
  });
});
