document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("searchInput");
    const box = document.getElementById("searchSuggestionsBox");

    if (!input || !box) return;

    let controller = null;
    let hideTimer = null;

    function showBox() {
        clearTimeout(hideTimer);
        box.classList.remove("hidden");
    }

    function hideBox() {
        hideTimer = setTimeout(() => {
            box.classList.add("hidden");
        }, 200); // delay prevents instant disappearance
    }

    // 🚫 IMPORTANT FIX:
    // This file must NEVER touch the placeholder.
    // It was overriding main.js.
    // We enforce the placeholder from main.js only.
    // -------------------------------------------------
    // Remove ANY potential placeholder changes:
    // (Your file does NOT contain such lines, but we lock it safely)
    input.setAttribute("data-lock-placeholder", "1");
    // -------------------------------------------------

    input.addEventListener("input", async function () {
        const q = this.value.trim();

        if (q.length < 2) {
            box.classList.add("hidden");
            box.innerHTML = "";
            return;
        }

        if (controller) controller.abort();
        controller = new AbortController();

        try {
            const res = await fetch(`/ar/search/suggestions/?q=${encodeURIComponent(q)}`, {
                signal: controller.signal,
            });

            const data = await res.json();
            const results = data.results;

            if (!results.length) {
                box.classList.add("hidden");
                box.innerHTML = "";
                return;
            }

            box.innerHTML = results
                .map(item => {
                    if (item.type === "category") {
                        return `
                        <div class="px-4 py-2 cursor-pointer hover:bg-gray-100"
                             onclick="window.location='/ar/items/?categories=${item.category_id}'">
                            ${item.emoji} ${item.name}
                            <span class="text-gray-400 text-xs">${item.parent || ""}</span>
                        </div>`;
                    }

                    if (item.type === "item") {
                        return `
                        <div class="px-4 py-2 cursor-pointer hover:bg-gray-100 flex items-center gap-3"
                             onclick="window.location='/ar/item/${item.id}'">
                            <img src="${item.photo_url || ""}"
                                 class="w-10 h-10 rounded-lg object-cover bg-gray-200" />
                            <div>
                                <div class="font-semibold">${item.name}</div>
                                <div class="text-xs text-gray-500">${item.category || ""}</div>
                            </div>
                        </div>`;
                    }
                })
                .join("");

            showBox();
        } catch (err) {
            console.warn("Suggestion aborted or failed:", err);
        }
    });

    box.addEventListener("mouseenter", showBox);
    box.addEventListener("mouseleave", hideBox);
    input.addEventListener("focus", showBox);
    input.addEventListener("blur", hideBox);

    document.addEventListener("click", function (e) {
        if (!box.contains(e.target) && e.target !== input) {
            hideBox();
        }
    });
});
