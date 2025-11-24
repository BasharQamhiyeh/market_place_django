// static/js/category_selector.js
// Multi-level Arabic category selector with search

(function () {

  function createLevelBlock(level, labelText) {
    const wrapper = document.createElement("div");
    wrapper.className = "category-level-block relative";

    const label = document.createElement("label");
    label.className = "block font-semibold mb-2";
    label.textContent = labelText || "القسم";

    const inputWrapper = document.createElement("div");
    inputWrapper.className = "relative";

    const input = document.createElement("input");
    input.type = "text";
    input.readOnly = true;
    input.className =
      "w-full border-2 border-[var(--rukn-orange)] rounded-xl py-2.5 px-3 pr-10 cursor-pointer";
    input.dataset.level = String(level);
    input.placeholder = level === 0 ? "اختر القسم الرئيسي" : "اختر القسم الفرعي";

    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("fill", "none");
    icon.setAttribute("stroke", "currentColor");
    icon.classList.add(
      "w-5",
      "h-5",
      "absolute",
      "left-3",
      "top-1/2",
      "-translate-y-1/2",
      "text-gray-400",
      "pointer-events-none"
    );
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("d", "M19 9l-7 7-7-7");
    icon.appendChild(path);

    inputWrapper.appendChild(input);
    inputWrapper.appendChild(icon);

    const dropdown = document.createElement("div");
    dropdown.className =
      "category-dropdown absolute z-40 mt-2 w-full bg-white border border-orange-200 rounded-xl shadow-lg";

    const searchWrapper = document.createElement("div");
    searchWrapper.className = "p-2 border-b border-orange-100";

    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "🔍 بحث...";
    searchInput.className =
      "w-full border border-gray-200 rounded-lg py-1.5 px-3 text-sm";

    searchWrapper.appendChild(searchInput);

    const list = document.createElement("ul");
    list.className = "max-h-52 overflow-y-auto text-sm";
    list.dataset.level = String(level);

    dropdown.appendChild(searchWrapper);
    dropdown.appendChild(list);

    wrapper.appendChild(label);
    wrapper.appendChild(inputWrapper);
    wrapper.appendChild(dropdown);

    return { wrapper, input, dropdown, list, searchInput };
  }

  function initCategorySelector(opts) {
    const container = opts.container;
    const tree = Array.isArray(opts.tree) ? opts.tree : [];
    const selectedPath = Array.isArray(opts.selectedPath) ? opts.selectedPath : [];
    const hiddenInput = opts.hiddenInput;

    if (!container || !hiddenInput) return;

    container.innerHTML = "";

    const state = {
      levels: [],
      path: selectedPath.slice()
    };

    function closeAllDropdowns() {
      container.querySelectorAll(".category-level-block").forEach(b => {
        b.classList.remove("open");
      });
    }

    function findNode(nodes, id) {
      id = String(id);
      return nodes.find(n => String(n.id) === id) || null;
    }

    function rebuildHiddenInput() {
      const last = state.levels[state.levels.length - 1];
      const oldVal = hiddenInput.value;
      let newVal = "";

      if (last && last.selectedNode && (!last.selectedNode.children || last.selectedNode.children.length === 0)) {
        newVal = String(last.selectedNode.id);
      }

      if (oldVal !== newVal) {
        hiddenInput.value = newVal;
        const ev = new Event("change", { bubbles: true });
        hiddenInput.dispatchEvent(ev);
      }
    }

    function clearLevelsFrom(index) {
      while (state.levels.length > index) {
        const lvl = state.levels.pop();
        if (lvl.block && lvl.block.parentNode === container) {
          container.removeChild(lvl.block);
        }
      }
    }

    function buildLevel(levelIndex, nodes, preselectId) {
      if (!nodes || !nodes.length) return;

      const block = createLevelBlock(
        levelIndex,
        levelIndex === 0 ? "القسم" : "القسم الفرعي"
      );
      const { wrapper, input, dropdown, list, searchInput } = block;

      // Populate list
      list.innerHTML = "";
      nodes.forEach(node => {
        const li = document.createElement("li");
        li.className = "p-2 hover:bg-orange-50 cursor-pointer";
        li.dataset.id = String(node.id);
        li.textContent = node.name_ar || node.name || "";
        list.appendChild(li);
      });

      // Clicking input toggles dropdown
      input.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = wrapper.classList.contains("open");
        closeAllDropdowns();
        if (!isOpen) {
          wrapper.classList.add("open");
          searchInput.focus();
        }
      });

      // Search inside dropdown
      searchInput.addEventListener("input", (e) => {
        const val = e.target.value.toLowerCase();
        Array.from(list.children).forEach(li => {
          const text = li.textContent.toLowerCase();
          li.style.display = text.includes(val) ? "block" : "none";
        });
      });

      // Selecting an item
      list.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        const li = e.target.closest("li");
        if (!li) return;
        const node = findNode(nodes, li.dataset.id);
        if (!node) return;

        input.value = li.textContent.trim();

        // Close dropdown properly
        wrapper.classList.remove("open");

        // Remove deeper levels
        clearLevelsFrom(levelIndex + 1);

        // Save selection
        state.levels[levelIndex] = {
          block: wrapper,
          input,
          nodes,
          selectedNode: node
        };

        // Build next level if children exist
        if (node.children && node.children.length > 0) {
          buildLevel(levelIndex + 1, node.children, null);
        }

        rebuildHiddenInput();
      });

      container.appendChild(wrapper);

      state.levels[levelIndex] = {
        block: wrapper,
        input,
        nodes,
        selectedNode: null
      };

      // Preselect path (edit / invalid POST)
      if (preselectId != null) {
        const node = findNode(nodes, preselectId);
        if (node) {
          input.value = node.name_ar || node.name || "";
          state.levels[levelIndex].selectedNode = node;

          if (node.children && node.children.length > 0) {
            const nextId = state.path[levelIndex + 1];
            buildLevel(levelIndex + 1, node.children, nextId);
          }
          rebuildHiddenInput();
        }
      }
    }

    // Initial render
    buildLevel(0, tree, state.path[0]);

    // Global click closes dropdowns
    document.addEventListener("click", (e) => {
      if (!container.contains(e.target)) {
        closeAllDropdowns();
      }
    });
  }

  window.initCategorySelector = initCategorySelector;

})();
