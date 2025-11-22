/* ============================================
   IMAGE PREVIEW + MAIN PHOTO SELECTION
============================================ */
document.addEventListener("change", function (e) {
    const input = document.getElementById("id_images");
    if (!input || e.target !== input) return;

    const preview = document.getElementById("preview");
    const mainInput = document.getElementById("main_photo_index");

    preview.innerHTML = "";
    mainInput.value = "";

    const files = Array.from(input.files || []);

    files.forEach((file, index) => {
        const reader = new FileReader();

        reader.onload = function (ev) {
            const wrapper = document.createElement("div");
            wrapper.className = "upload-preview";

            const img = document.createElement("img");
            img.src = ev.target.result;
            img.dataset.index = index;

            img.onclick = () => {
                document.querySelectorAll(".upload-preview").forEach((p) =>
                    p.classList.remove("main")
                );
                wrapper.classList.add("main");
                mainInput.value = index;
            };

            wrapper.appendChild(img);
            preview.appendChild(wrapper);
        };

        reader.readAsDataURL(file);
    });
});

/* ============================================
   CONDITION SWITCH (NEW / USED)
============================================ */
document.addEventListener("DOMContentLoaded", function () {
    const hidden = document.getElementById("id_condition_hidden");
    const newBtn = document.getElementById("cond_new_btn");
    const usedBtn = document.getElementById("cond_used_btn");

    if (!newBtn || !usedBtn || !hidden) return;

    function activate(btnActive, btnInactive, value) {
        hidden.value = value;

        btnActive.classList.add("active");
        btnActive.classList.remove("inactive");

        btnInactive.classList.add("inactive");
        btnInactive.classList.remove("active");
    }

    newBtn.onclick = () => activate(newBtn, usedBtn, "new");
    usedBtn.onclick = () => activate(usedBtn, newBtn, "used");
});

/* ============================================
   CATEGORY TREE BUILDER
============================================ */
function parseJSON(id) {
    const el = document.getElementById(id);
    if (!el) return [];
    try {
        return JSON.parse(el.textContent.trim() || "[]");
    } catch {
        return [];
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("category-levels");
    if (!container) return;

    const CATEGORY_TREE = parseJSON("category-tree-data");
    const SELECTED_PATH = parseJSON("selected-category-path");

    const finalField = document.getElementById("id_category_final");

    /* Build one level of dropdown */
    function buildLevel(levelIdx, nodes, selectedId) {
        const label = document.createElement("label");
        label.className = "font-semibold";
        label.textContent = levelIdx === 0 ? "القسم الرئيسي" : "القسم الفرعي";

        const select = document.createElement("select");
        select.className = "add-ad-select";
        select.dataset.level = levelIdx;

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "اختر...";
        placeholder.disabled = true;
        if (!selectedId) placeholder.selected = true;
        select.appendChild(placeholder);

        nodes.forEach((node) => {
            const op = document.createElement("option");
            op.value = String(node.id);
            op.textContent = node.name;
            if (selectedId && Number(selectedId) === Number(node.id)) {
                op.selected = true;
            }
            select.appendChild(op);
        });

        const wrapper = document.createElement("div");
        wrapper.appendChild(label);
        wrapper.appendChild(select);

        container.appendChild(wrapper);

        return select;
    }

    /* Build initial top-level */
    let currentNodes = CATEGORY_TREE;
    let levelSelect = buildLevel(0, currentNodes, SELECTED_PATH[0]);

    function getChildren(path) {
        let nodes = CATEGORY_TREE;
        let selected;
        path.forEach((id) => {
            selected = nodes.find((n) => Number(n.id) === Number(id));
            nodes = selected && selected.children ? selected.children : [];
        });
        return nodes;
    }

    function updateFinalValue() {
        let last = "";
        container.querySelectorAll("select").forEach((sel) => {
            if (sel.value) last = sel.value;
        });
        finalField.value = last;
    }

    /* Rebuild deeper levels if editing existing item */
    if (SELECTED_PATH.length) {
        let path = [];
        SELECTED_PATH.forEach((id, idx) => {
            const sel = container.querySelector(`select[data-level="${idx}"]`);
            if (!sel) return;

            sel.value = String(id);
            path.push(id);

            if (idx < SELECTED_PATH.length - 1) {
                const children = getChildren(path);
                buildLevel(idx + 1, children, SELECTED_PATH[idx + 1]);
            }
        });
        updateFinalValue();
    }

    /* Listen for changes */
    container.addEventListener("change", function (e) {
        const sel = e.target;
        if (!(sel instanceof HTMLSelectElement)) return;

        const level = Number(sel.dataset.level);

        /* Remove all deeper levels */
        container.querySelectorAll("select").forEach((other) => {
            if (Number(other.dataset.level) > level) {
                other.parentElement.remove();
            }
        });

        /* Build children */
        if (sel.value) {
            const path = [];
            container.querySelectorAll("select").forEach((s) => {
                if (s.value) path.push(Number(s.value));
            });

            const children = getChildren(path);

            if (children.length) {
                buildLevel(level + 1, children, null);
            }
        }

        updateFinalValue();
    });
});
