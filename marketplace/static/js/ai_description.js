// static/js/ai_description.js
// Simple reusable "generate description" helper for listing forms

document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("aiBtn");
  if (!btn) return;

  const titleInput = document.getElementById("id_title");
  const descField = document.getElementById("id_description");
  const previewContainer = document.getElementById("previewContainer");

  btn.addEventListener("click", function () {
    if (!titleInput || !descField) return;

    const title = (titleInput.value || "").trim();
    const imagesCount = previewContainer
      ? previewContainer.querySelectorAll(".upload-preview").length
      : 0;

    if (!title) {
      alert("⚠️ الرجاء إدخال عنوان الإعلان أولاً قبل توليد الوصف.");
      return;
    }

    if (imagesCount === 0) {
      if (!confirm("لم تقم بإضافة صور. هل تريد توليد الوصف بدون صور؟")) {
        return;
      }
    }

    const base = `📦 ${title} — منتج بحالة ممتازة، مناسب للاستخدام اليومي ويتميز بسعر منافس. `;
    const withPhotos = imagesCount > 0
      ? `تم إرفاق ${imagesCount} صورة توضح حالة المنتج من عدة زوايا لزيادة وضوح التفاصيل للمشتري. `
      : "";
    const extra =
      "يرجى قراءة الوصف جيداً والتواصل في حال وجود أي استفسار إضافي عن المواصفات أو طريقة التسليم.";

    descField.value = base + withPhotos + extra;

    // small highlight effect
    descField.classList.add("ring-2", "ring-[var(--rukn-orange)]");
    setTimeout(() => {
      descField.classList.remove("ring-2", "ring-[var(--rukn-orange)]");
    }, 800);
  });
});
