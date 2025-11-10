document.addEventListener("DOMContentLoaded", function() {
  const input = document.getElementById("id_icon");
  if (!input) return;

  // Create preview span
  const preview = document.createElement("span");
  preview.style.marginLeft = "10px";
  preview.style.fontSize = "22px";
  preview.style.verticalAlign = "middle";
  input.parentNode.appendChild(preview);

  function updatePreview() {
    preview.className = input.value;
  }

  input.addEventListener("input", updatePreview);
  updatePreview();
});
