// static/js/ai_description.js
// Generates a localised Arabic description based on the ad title and condition.

document.addEventListener("DOMContentLoaded", function () {
  const btn              = document.getElementById("aiBtn");
  if (!btn) return;

  const titleInput       = document.getElementById("id_title");
  const descField        = document.getElementById("id_description");
  const previewContainer = document.getElementById("previewContainer");
  const conditionVal     = document.getElementById("conditionValue");   // new / used toggle
  const imageDropzone    = document.getElementById("imageDropzone");

  /* ── inline error helpers ── */
  function clearErrors() {
    document.querySelectorAll(".ai-field-error").forEach(function (e) { e.remove(); });
    document.querySelectorAll(".ai-error-border").forEach(function (e) { e.classList.remove("ai-error-border"); });
  }
  function showError(field, message) {
    clearErrors();
    field.classList.add("ai-error-border");
    var p = document.createElement("p");
    p.className = "ai-field-error field-error";
    p.textContent = message;
    field.insertAdjacentElement("afterend", p);
    field.scrollIntoView({ behavior: "smooth", block: "center" });
    if (typeof field.focus === "function") field.focus();
  }
  function showErrorBelow(elem, message) {
    clearErrors();
    var p = document.createElement("p");
    p.className = "ai-field-error field-error";
    p.textContent = message;
    elem.insertAdjacentElement("afterend", p);
    elem.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  /* ── category keyword map ── */
  var categories = {
    phones: [
      "iphone", "ايفون", "آيفون", "سامسونج", "هاتف", "جوال", "موبايل",
      "هواوي", "شاومي", "ريدمي", "galaxy", "honor", "نوكيا", "oppo", "vivo"
    ],
    laptops: [
      "laptop", "لاب", "لابتوب", "ماك", "macbook", "حاسوب", "كمبيوتر",
      "pc", "dell", "hp", "lenovo", "asus", "acer", "msi"
    ],
    tablets: [
      "ipad", "ايباد", "آيباد", "تابلت", "tablet", "galaxy tab", "تاب"
    ],
    cars: [
      "سيارة", "سياره", "toyota", "kia", "hyundai", "bmw", "mercedes",
      "ford", "honda", "nissan", "lexus", "mazda", "chevrolet", "جيب", "jeep"
    ],
    bikes: [
      "دراجة", "دراجه", "سيكل", "bicycle", "bike", "سكوتر", "scooter", "دباب"
    ],
    realestate: [
      "شقة", "شقه", "شقق", "شاليه", "فيلا", "villa", "apartment", "أرض",
      "ارض", "مكتب", "محل", "منزل", "بيت", "عقار", "استوديو", "غرفة", "غرف"
    ],
    furniture: [
      "كنبة", "كنب", "طاولة", "طاوله", "كرسي", "سرير", "دولاب", "خزانة",
      "خزانه", "أثاث", "اثاث", "تسريحة", "مكتبة", "رف", "طقم", "سفرة"
    ],
    clothes: [
      "ملابس", "قميص", "بنطال", "فستان", "عباية", "عبايه", "جاكيت",
      "حذاء", "شنطة", "حقيبة", "حقيبه", "تيشيرت", "معطف", "تنورة", "شال"
    ],
    watches: [
      "ساعة", "ساعه", "watch", "rolex", "casio", "seiko", "smart watch", "سمارت"
    ],
    perfumes: [
      "عطر", "عطور", "perfume", "parfum", "عود", "مسك", "بخور"
    ],
    electronics: [
      "شاشة", "شاشه", "تلفزيون", "tv", "سماعة", "سماعه", "بلايستيشن",
      "ps5", "ps4", "xbox", "نينتندو", "router", "راوتر"
    ],
    cameras: [
      "كاميرا", "camera", "canon", "nikon", "sony", "عدسة", "lens", "gopro"
    ],
    homeAppliances: [
      "ثلاجة", "ثلاجه", "غسالة", "غساله", "مكيف", "مكيّف", "فرن",
      "ميكرويف", "مكنسة", "مكنسه", "دفاية", "دفايه", "مروحة", "مروحه"
    ],
    gaming: [
      "لعبة", "لعبه", "ألعاب", "العاب", "gaming", "game", "كرسي قيمنق",
      "قيمنق", "يد تحكم", "controller"
    ],
    sports: [
      "رياضة", "رياضه", "مشاية", "مشايه", "دامبل", "بار", "كرة",
      "دراجة رياضية", "جهاز رياضي", "treadmill", "gym", "fitness"
    ]
  };

  function detectCategory(text) {
    var lower = text.toLowerCase();
    for (var cat in categories) {
      if (categories[cat].some(function (kw) { return lower.includes(kw.toLowerCase()); })) {
        return cat;
      }
    }
    return "general";
  }

  /* ── per-category description templates ── */
  function buildTemplates(title, conditionText) {
    return {
      phones: [
        title + "\nالحالة: " + conditionText + "\n- جهاز مناسب للاستخدام اليومي ويقدم أداءً جيداً في المهام الأساسية.\n- يتميز بسهولة الاستخدام وجودة مناسبة ضمن هذه الفئة.\n- الصور المرفقة توضح حالة الجهاز وتفاصيله بشكل واضح.\nخيار مناسب لمن يبحث عن جهاز عملي بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- هاتف عملي بحالة جيدة ومناسب للتواصل والاستخدام اليومي.\n- يوفر تجربة استخدام مريحة وأداءً موثوقاً.\n- يمكن الاطلاع على التفاصيل الكاملة من خلال الصور.\nفرصة جيدة للحصول على جهاز موثوق بقيمة مناسبة."
      ],
      laptops: [
        title + "\nالحالة: " + conditionText + "\n- جهاز مناسب للعمل أو الدراسة أو الاستخدام اليومي.\n- يتميز بأداء جيد وتصميم عملي يلبي مختلف الاحتياجات.\n- الصور المرفقة توضح حالة الجهاز وتفاصيله بشكل دقيق.\nخيار مناسب لمن يبحث عن جهاز عملي وموثوق.",
        title + "\nالحالة: " + conditionText + "\n- لابتوب عملي بجودة جيدة ويوفر تجربة استخدام مريحة.\n- مناسب للتصفح والأعمال المكتبية والدراسة.\n- الصور توضح التفاصيل والحالة الفعلية بوضوح.\nقيمة جيدة مقابل السعر."
      ],
      tablets: [
        title + "\nالحالة: " + conditionText + "\n- جهاز لوحي عملي ومناسب للتصفح والدراسة والاستخدام اليومي.\n- يتميز بسهولة الحمل والاستخدام مع أداء جيد.\n- الصور المرفقة توضح حالة الجهاز وتفاصيله بشكل واضح.\nخيار مناسب لمن يبحث عن جهاز عملي وخفيف.",
        title + "\nالحالة: " + conditionText + "\n- تابلت بحالة جيدة ومناسب لمختلف الاستخدامات اليومية.\n- يوفر تجربة استخدام مريحة وجودة مناسبة ضمن هذه الفئة.\n- التفاصيل موضحة بوضوح في الصور.\nفرصة مناسبة للحصول على جهاز مفيد بسعر جيد."
      ],
      cars: [
        title + "\nالحالة: " + conditionText + "\n- مركبة عملية ومناسبة للاستخدام اليومي.\n- توفر الراحة والاعتمادية وتلبي احتياجات التنقل بشكل جيد.\n- الصور المرفقة توضح الحالة العامة والتفاصيل بوضوح.\nخيار مناسب لمن يبحث عن وسيلة تنقل موثوقة.",
        title + "\nالحالة: " + conditionText + "\n- سيارة مناسبة للاستخدام الشخصي أو العائلي.\n- تتميز بعملية جيدة وتعد خياراً مناسباً ضمن هذه الفئة.\n- الصور توضح حالة المركبة من الداخل والخارج.\nفرصة جيدة لمن يبحث عن سيارة بسعر مناسب."
      ],
      bikes: [
        title + "\nالحالة: " + conditionText + "\n- دراجة عملية ومناسبة للتنقل أو الاستخدام الترفيهي.\n- تتميز بسهولة الاستخدام وحالة جيدة.\n- الصور المرفقة توضح التفاصيل والشكل العام بوضوح.\nخيار مناسب لمن يبحث عن وسيلة عملية وخفيفة.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب للتنقل اليومي أو الاستخدام الرياضي الخفيف.\n- يوفر تجربة استخدام مريحة وجودة مناسبة.\n- يمكن مراجعة التفاصيل الكاملة من خلال الصور.\nفرصة جيدة للحصول على منتج عملي بسعر مناسب."
      ],
      realestate: [
        title + "\nالحالة: " + conditionText + "\n- عقار مناسب للسكن أو الاستثمار حسب طبيعة الإعلان.\n- يتميز بمساحة واستخدام عملي ضمن هذه الفئة.\n- الصور المرفقة توضح التفاصيل والمواصفات بشكل واضح.\nخيار مناسب لمن يبحث عن فرصة جيدة وموقع عملي.",
        title + "\nالحالة: " + conditionText + "\n- عرض مميز مناسب لمن يبحث عن سكن أو استثمار عقاري.\n- التفاصيل المتوفرة والصور تساعد على تكوين فكرة واضحة عن العقار.\n- يمكن الاطلاع على الحالة والمزايا من خلال الصور.\nفرصة مناسبة ضمن هذه الفئة."
      ],
      furniture: [
        title + "\nالحالة: " + conditionText + "\n- قطعة أثاث عملية ومناسبة للاستخدام المنزلي أو المكتبي.\n- تتميز بتصميم جيد وجودة مناسبة مع استخدام مريح.\n- الصور المرفقة توضح الحالة والتفاصيل بشكل واضح.\nخيار مناسب لمن يبحث عن أثاث عملي بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب لتنظيم المساحة وإضافة استخدام عملي ومريح.\n- يتميز بحالة جيدة وتصميم مناسب لمختلف الاحتياجات.\n- الصور توضح جميع التفاصيل بشكل واضح.\nاختيار موفق لمن يبحث عن الجودة والعملية."
      ],
      clothes: [
        title + "\nالحالة: " + conditionText + "\n- قطعة مميزة بتصميم جميل ومناسبة للاستخدام اليومي.\n- تتميز بمظهر جيد وجودة مناسبة ضمن هذه الفئة.\n- الصور المرفقة توضح التفاصيل والحالة بشكل واضح.\nخيار مناسب لمن يبحث عن منتج أنيق بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج عملي وأنيق يناسب مختلف الاستخدامات.\n- يوفر مظهراً جيداً وراحة في الاستخدام.\n- يمكن مشاهدة الشكل والتفاصيل بوضوح في الصور.\nفرصة جيدة للحصول على قطعة مميزة."
      ],
      watches: [
        title + "\nالحالة: " + conditionText + "\n- ساعة مميزة بتصميم عملي وأنيق.\n- مناسبة للاستخدام اليومي أو الإطلالة الرسمية حسب نوعها.\n- الصور المرفقة توضح الشكل والتفاصيل بوضوح.\nخيار مناسب لمن يبحث عن الأناقة والجودة.",
        title + "\nالحالة: " + conditionText + "\n- منتج يتميز بتصميم جميل وجودة مناسبة ضمن هذه الفئة.\n- مناسب للاستخدام اليومي ويضيف لمسة أنيقة.\n- التفاصيل والحالة موضحة في الصور.\nفرصة جيدة للحصول على ساعة مميزة بسعر مناسب."
      ],
      perfumes: [
        title + "\nالحالة: " + conditionText + "\n- عطر مميز برائحة جذابة ومناسب للاستخدام اليومي أو المناسبات.\n- يتميز بثبات جيد وقيمة مناسبة ضمن هذه الفئة.\n- الصور المرفقة توضح المنتج وتفاصيله بوضوح.\nخيار مناسب لمن يبحث عن عطر مميز بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب لعشاق الروائح المميزة والأنيقة.\n- يتميز بجودة جيدة ويعد خياراً مناسباً للاستخدام الشخصي أو الإهداء.\n- يمكن مراجعة التفاصيل من خلال الصور.\nفرصة مناسبة للحصول على عطر جميل بقيمة جيدة."
      ],
      electronics: [
        title + "\nالحالة: " + conditionText + "\n- منتج إلكتروني عملي يوفر أداءً جيداً واستخداماً مريحاً.\n- مناسب للاستخدام اليومي ويتميز بجودة مناسبة.\n- الصور المرفقة توضح الحالة والتفاصيل بشكل واضح.\nخيار جيد لمن يبحث عن منتج موثوق بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- جهاز عملي بحالة جيدة ومناسب لمختلف الاستخدامات.\n- يتميز بأداء مستقر وتجربة استخدام سهلة.\n- يمكن مشاهدة التفاصيل بوضوح في الصور.\nقيمة ممتازة مقابل السعر."
      ],
      cameras: [
        title + "\nالحالة: " + conditionText + "\n- كاميرا مناسبة للتصوير اليومي أو الاستخدام الاحترافي الخفيف حسب الفئة.\n- تتميز بجودة جيدة وتفاصيل واضحة في الأداء.\n- الصور المرفقة توضح حالة المنتج وملحقاته إن وجدت.\nخيار مناسب لمن يبحث عن كاميرا عملية بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب لعشاق التصوير ويقدم جودة جيدة ضمن هذه الفئة.\n- يتميز بحالة جيدة وسهولة في الاستخدام.\n- يمكن الاطلاع على التفاصيل بوضوح من خلال الصور.\nفرصة جيدة للحصول على كاميرا موثوقة."
      ],
      homeAppliances: [
        title + "\nالحالة: " + conditionText + "\n- جهاز منزلي عملي ومناسب للاستخدام اليومي.\n- يتميز بأداء جيد ويساعد على توفير الراحة في المنزل.\n- الصور المرفقة توضح حالة المنتج وتفاصيله بوضوح.\nخيار مناسب لمن يبحث عن جهاز مفيد بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب للاستخدام المنزلي ويقدم أداءً جيداً.\n- يتميز بجودة مناسبة وسهولة في الاستخدام.\n- التفاصيل موضحة بوضوح في الصور.\nفرصة جيدة للحصول على جهاز عملي وموثوق."
      ],
      gaming: [
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب لعشاق الألعاب ويوفر تجربة استخدام جيدة.\n- يتميز بحالة جيدة وأداء مناسب ضمن هذه الفئة.\n- الصور المرفقة توضح التفاصيل والحالة بشكل واضح.\nخيار مناسب لمن يبحث عن منتج قيمنق بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج عملي ومناسب للاستخدام الترفيهي اليومي.\n- يوفر تجربة جيدة وجودة مناسبة لمحبي الألعاب.\n- يمكن مشاهدة التفاصيل الكاملة في الصور.\nفرصة مناسبة للحصول على منتج مميز."
      ],
      sports: [
        title + "\nالحالة: " + conditionText + "\n- منتج رياضي عملي ومناسب للاستخدام الشخصي أو المنزلي.\n- يتميز بحالة جيدة وجودة مناسبة ضمن هذه الفئة.\n- الصور المرفقة توضح تفاصيل المنتج بشكل واضح.\nخيار مناسب لمن يبحث عن منتج رياضي مفيد بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج مناسب لممارسة الرياضة أو تحسين النشاط اليومي.\n- يتميز بسهولة الاستخدام وقيمة جيدة مقابل السعر.\n- الصور توضح الحالة والتفاصيل بوضوح.\nفرصة جيدة للحصول على منتج عملي ومفيد."
      ],
      general: [
        title + "\nالحالة: " + conditionText + "\n- منتج يتميز بجودة جيدة وأداء موثوق.\n- مناسب للاستخدام اليومي ويوفر تجربة استخدام مريحة.\n- الصور المرفقة توضح تفاصيل المنتج بشكل واضح.\nخيار مناسب لمن يبحث عن جودة بسعر مناسب.",
        title + "\nالحالة: " + conditionText + "\n- منتج عملي بحالة ممتازة ويعمل بكفاءة.\n- مناسب للاستخدام اليومي ويقدم قيمة جيدة مقابل السعر.\n- يمكن مشاهدة تفاصيل المنتج بوضوح في الصور.\nفرصة جيدة للحصول على منتج موثوق."
      ]
    };
  }

  /* ── button click ── */
  btn.addEventListener("click", function () {
    if (!titleInput || !descField) return;

    var title = titleInput.value.trim();
    var previews = previewContainer
      ? previewContainer.querySelectorAll(".upload-preview")
      : [];

    if (!title) {
      showError(titleInput, "الرجاء إدخال عنوان الإعلان قبل توليد الوصف");
      return;
    }
    if (previews.length === 0) {
      var anchor = imageDropzone || previewContainer || titleInput;
      showErrorBelow(anchor, "الرجاء إضافة صور للإعلان قبل توليد الوصف");
      return;
    }

    var conditionText = (conditionVal && conditionVal.value === "used")
      ? "مستعمل بحالة جيدة"
      : "جديد وغير مستخدم";

    var category  = detectCategory(title);
    var templates = buildTemplates(title, conditionText);
    var options   = templates[category] || templates.general;
    var generated = options[Math.floor(Math.random() * options.length)];

    descField.value = generated;
    descField.dispatchEvent(new Event("input", { bubbles: true }));

    // brief highlight so the user notices the field was filled
    descField.classList.add("ring-2", "ring-[var(--rukn-orange)]");
    setTimeout(function () {
      descField.classList.remove("ring-2", "ring-[var(--rukn-orange)]");
    }, 800);

    clearErrors();
  });
});
