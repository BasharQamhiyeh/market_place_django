document.addEventListener("DOMContentLoaded", async function () {
  const iconInput = document.getElementById("id_icon");
  const colorInput = document.getElementById("id_color");
  if (!iconInput) return;

  // Create preview element
  const preview = document.createElement("span");
  preview.style.fontSize = "30px";
  preview.style.marginLeft = "10px";
  preview.style.verticalAlign = "middle";
  preview.textContent = iconInput.value || "🙂";
  iconInput.parentNode.appendChild(preview);

  // Create the button
  const pickerBtn = document.createElement("button");
  pickerBtn.type = "button";
  pickerBtn.textContent = "🧩 Choose Emoji";
  pickerBtn.classList.add("button");
  pickerBtn.style.marginLeft = "10px";
  iconInput.parentNode.appendChild(pickerBtn);

  try {
    // ✅ Import emoji picker properly (as ES module)
    const module = await import("https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@4.6.2/+esm");
    const EmojiButton = module.EmojiButton || module.default;

    const picker = new EmojiButton({ theme: "auto", position: "bottom-start" });

    // When an emoji is picked
    picker.on("emoji", (selection) => {
      // ✅ Ensure we always save the emoji string, not an object
      const emoji = typeof selection === "string" ? selection : selection.emoji || "";
      iconInput.value = emoji;
      preview.textContent = emoji;
      preview.style.color = colorInput?.value || "#000";
    });

    pickerBtn.addEventListener("click", () => picker.togglePicker(pickerBtn));

  } catch (error) {
    console.error("Emoji picker failed to load:", error);
    alert("Emoji picker not supported in this browser. Paste emoji manually 🙂");
  }

  // Live preview when typing manually
  iconInput.addEventListener("input", () => {
    preview.textContent = iconInput.value || "🙂";
    preview.style.color = colorInput?.value || "#000";
  });

  // Update preview color
  colorInput?.addEventListener("input", () => {
    preview.style.color = colorInput.value;
  });
});
