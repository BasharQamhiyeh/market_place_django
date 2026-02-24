(function () {
    function initPreview() {
        document.querySelectorAll('input[type="file"]').forEach(function (input) {
            // avoid attaching twice
            if (input.dataset.previewBound) return;
            input.dataset.previewBound = "true";

            input.addEventListener("change", function () {
                const file = this.files[0];
                if (!file || !file.type.startsWith("image/")) return;

                const reader = new FileReader();
                reader.onload = function (e) {
                    // look for an existing preview img next to this input
                    let preview = input.parentElement.querySelector("img.live-preview");

                    if (!preview) {
                        preview = document.createElement("img");
                        preview.className = "live-preview";
                        preview.style.cssText =
                            "display:block;width:160px;height:160px;object-fit:cover;" +
                            "border-radius:8px;border:1px solid #ddd;margin-top:8px;";
                        input.parentElement.appendChild(preview);
                    }

                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPreview);
    } else {
        initPreview();
    }

    // re-run when nested-admin adds new inline rows
    document.addEventListener("formset:added", initPreview);
})();