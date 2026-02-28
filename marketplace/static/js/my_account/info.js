/* static/js/my_account/info.js
   ✅ Info tab logic for the new mockup HTML (IDs/classes are from your mockup)
   ✅ Includes:
      - profile image preview + remove
      - store logo preview + remove
      - displayed name + note refresh
      - field validation helpers (email/links)
      - chips groups validation (contact/payment/delivery/return)
      - success modal helpers
   ⚠️ NOTE:
      This file ONLY handles the Info tab.
      It does NOT call generateAds/generateRequests/etc.
*/

(function () {
  "use strict";

  /* =========================
     Helpers
  ========================= */

  function $(id) {
    return document.getElementById(id);
  }

  function hasChecked(selector) {
    return document.querySelectorAll(selector + ":checked").length > 0;
  }

  function markBoxError(boxId, errorId) {
    const box = $(boxId);
    const err = $(errorId);
    if (box) box.classList.add("box-error");
    if (err) err.classList.remove("hidden");
    box?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearBoxError(boxId, errorId) {
    const box = $(boxId);
    const err = $(errorId);
    if (box) box.classList.remove("box-error");
    if (err) err.classList.add("hidden");
  }

  function setFieldError(inputId, errorId, hasError, message) {
    const input = $(inputId);
    const error = $(errorId);
    if (!input || !error) return;

    if (hasError) {
      if (message) error.textContent = message;
      error.classList.remove("hidden");
      input.classList.add("border-red-500");
    } else {
      error.classList.add("hidden");
      input.classList.remove("border-red-500");
    }
  }

  function isLettersAndSpaces(value) {
    if (!value) return false;
    return /^[a-zA-Z\u0600-\u06FF\s]+$/.test(value);
  }

  function isValidEmail(value) {
    if (!value) return true;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function isValidURL(value) {
    if (!value) return true;
    return /^(https?:\/\/)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\/.*)?$/i.test(
      value
    );
  }

  function isValidWebsite(value) {
    if (!value) return true;
    return /^(https?:\/\/)?(www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(\/.*)?$/.test(
      value
    );
  }

  function validateLinkField({ inputId, errorId, okId, validator, message }) {
    const input = $(inputId);
    const okIcon = $(okId);
    const value = (input?.value || "").trim();

    if (!input) return true;

    // empty allowed
    if (!value) {
      setFieldError(inputId, errorId, false);
      okIcon?.classList.add("hidden");
      return true;
    }

    if (!validator(value)) {
      setFieldError(inputId, errorId, true, message);
      okIcon?.classList.add("hidden");
      return false;
    }

    setFieldError(inputId, errorId, false);
    okIcon?.classList.remove("hidden");
    return true;
  }

  function filterNameInput(input) {
    input.value = input.value.replace(/[^a-zA-Z\u0600-\u06FF\s]/g, "");
  }

  // openSuccessModal / closeSuccessModal are global (defined in base.js)

  /* =========================
     Displayed name + note
  ========================= */

  function refreshDisplayedName() {
    const storeName = ($("storeName")?.value || "").trim();
    const first = ($("firstName")?.value || "").trim();
    const last = ($("lastName")?.value || "").trim();
    const nick = ($("nickname")?.value || "").trim();

    const displayName = storeName.length
      ? storeName
      : nick.length
      ? nick
      : `${first} ${last}`.trim();

    const fullNameEl = $("fullName");
    if (fullNameEl) fullNameEl.textContent = displayName || "—";

    const noteEl = $("displayNote");
    if (!noteEl) return;

    if (storeName.length) {
      noteEl.textContent =
        "اسم المتجر هو الذي سيظهر للآخرين في الإعلانات والرسائل وكذلك لوجو المتجر.";
    } else {
      noteEl.textContent = "هذا الاسم سيظهر للآخرين في الإعلانات والطلبات والرسائل.";
    }
  }

  /* =========================
     Profile image
  ========================= */

  function refreshProfileInitials() {
    const first = ($("firstName")?.value || "").trim();
    const nick = ($("nickname")?.value || "").trim();

    const initialsSpan = $("profileInitials");
    const imgEl = $("profileImage");
    const removeBtn = $("removeProfileBtn");

    if (!initialsSpan || !imgEl || !removeBtn) return;

    const hasImage = imgEl.dataset.hasImage === "true";

    if (hasImage) {
      initialsSpan.classList.add("hidden");
      imgEl.classList.remove("hidden");
      removeBtn.classList.remove("hidden");
      return;
    }

    let initial = "؟";
    if (nick.length) initial = nick.charAt(0);
    else if (first.length) initial = first.charAt(0);

    initialsSpan.textContent = initial;
    initialsSpan.classList.remove("hidden");
    imgEl.classList.add("hidden");
    removeBtn.classList.add("hidden");
  }

  function removeProfileImage() {
    const imgEl = $("profileImage");
    const initialsSpan = $("profileInitials");
    const removeBtn = $("removeProfileBtn");
    const fileInput = $("profileImgInput");

    if (!imgEl || !initialsSpan || !removeBtn) return;

    imgEl.src = "";
    imgEl.dataset.hasImage = "false";
    imgEl.classList.add("hidden");

    removeBtn.classList.add("hidden");
    initialsSpan.classList.remove("hidden");

    if (fileInput) fileInput.value = "";

    refreshProfileInitials();
    refreshDisplayedName();
  }

  function bindProfileUpload() {
    const input = $("profileImgInput");
    const removeBtn = $("removeProfileBtn");

    input?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const imgEl = $("profileImage");
        if (!imgEl) return;

        imgEl.src = event.target.result;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");

        $("profileInitials")?.classList.add("hidden");
        $("removeProfileBtn")?.classList.remove("hidden");

        refreshDisplayedName();
      };
      reader.readAsDataURL(file);
    });

    removeBtn?.addEventListener("click", removeProfileImage);
  }

  /* =========================
     Store logo
  ========================= */

  function refreshStoreLogoInitial() {
    const storeName = ($("storeName")?.value || "").trim();
    const storeInitialSpan = $("storeLogoInitial");
    const imgEl = $("storeLogoImage");
    const removeBtn = $("removeStoreLogoBtn");

    if (!storeInitialSpan || !imgEl || !removeBtn) return;

    const hasImage = imgEl.dataset.hasImage === "true";

    if (hasImage) {
      storeInitialSpan.classList.add("hidden");
      imgEl.classList.remove("hidden");
      removeBtn.classList.remove("hidden");
      return;
    }

    let initial = "م";
    if (storeName.length) initial = storeName.charAt(0);

    storeInitialSpan.textContent = initial;
    storeInitialSpan.classList.remove("hidden");

    imgEl.classList.add("hidden");
    removeBtn.classList.add("hidden");
  }

  function removeStoreLogo() {
    const imgEl = $("storeLogoImage");
    const removeBtn = $("removeStoreLogoBtn");
    const fileInput = $("storeLogoInput");

    if (!imgEl || !removeBtn) return;

    imgEl.src = "";
    imgEl.dataset.hasImage = "false";
    imgEl.classList.add("hidden");
    removeBtn.classList.add("hidden");

    if (fileInput) fileInput.value = "";

    refreshStoreLogoInitial();
  }

  function bindStoreLogoUpload() {
    const input = $("storeLogoInput");
    const removeBtn = $("removeStoreLogoBtn");

    input?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const imgEl = $("storeLogoImage");
        if (!imgEl) return;

        imgEl.src = event.target.result;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");

        $("storeLogoInitial")?.classList.add("hidden");
        $("removeStoreLogoBtn")?.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    });

    removeBtn?.addEventListener("click", removeStoreLogo);
  }

  /* =========================
     Live input bindings
  ========================= */

  function bindLiveInputs() {
    [
      { input: "firstName", error: "firstNameError", filter: true },
      { input: "lastName", error: "lastNameError", filter: true },
      { input: "storeName", error: "storeNameError" },
      { input: "email", error: "emailError" },
      { input: "storeLocation" },
      { input: "storeDesc" },
      { input: "nickname" },
    ].forEach((cfg) => {
      const el = $(cfg.input);
      if (!el) return;

      el.addEventListener("input", () => {
        if (cfg.filter) filterNameInput(el);
        if (cfg.error) setFieldError(cfg.input, cfg.error, false);
        refreshDisplayedName();
        refreshProfileInitials();
        if (cfg.input === "storeName") refreshStoreLogoInitial();
      });
    });

    // clear group errors when changed
    [
      { box: "contactBox", error: "contactError", selector: "input[name='showMobile']" },
      { box: "paymentBox", error: "paymentError", selector: "#paymentBox input[type='checkbox']" },
      { box: "deliveryBox", error: "deliveryError", selector: "input[name='deliveryTime']" },
      { box: "returnBox", error: "returnError", selector: "input[name='returnPolicy']" },
    ].forEach((cfg) => {
      document.querySelectorAll(cfg.selector).forEach((input) => {
        input.addEventListener("change", () => clearBoxError(cfg.box, cfg.error));
      });
    });

    // hide errors while typing
    [
      { input: "storeSpecialty", error: "storeSpecialtyError" },
      { input: "storeDesc", error: "storeDescError" },
    ].forEach((cfg) => {
      const el = $(cfg.input);
      if (!el) return;
      el.addEventListener("input", () => setFieldError(cfg.input, cfg.error, false));
    });
  }

  /* =========================
     Link validations
  ========================= */

  const linkChecks = [
    {
      inputId: "email",
      errorId: "emailError",
      okId: "emailOk",
      validator: isValidEmail,
      message: "الرجاء إدخال بريد إلكتروني صحيح (مثال: example@mail.com).",
    },
    {
      inputId: "storeWebsite",
      errorId: "storeWebsiteError",
      okId: "storeWebsiteOk",
      validator: isValidWebsite,
      message: "الرجاء إدخال رابط موقع الكتروني صحيح (مثال: https://example.com).",
    },
    {
      inputId: "instagramLink",
      errorId: "instagramError",
      okId: "instagramOk",
      validator: isValidURL,
      message: "الرجاء إدخال رابط انستجرام صحيح (مثال: https://instagram.com/username).",
    },
    {
      inputId: "facebookLink",
      errorId: "facebookError",
      okId: "facebookOk",
      validator: isValidURL,
      message: "الرجاء إدخال رابط فيس بوك صحيح (مثال: https://facebook.com/page).",
    },
  ];

  function bindLinkChecks() {
    linkChecks.forEach((cfg) => {
      const el = $(cfg.inputId);
      if (!el) return;

      el.addEventListener("input", () => validateLinkField(cfg));
    });

    // reset ok/error while typing (before validation)
    [
      { input: "email", error: "emailError", ok: "emailOk" },
      { input: "storeWebsite", error: "storeWebsiteError", ok: "storeWebsiteOk" },
      { input: "instagramLink", error: "instagramError", ok: "instagramOk" },
      { input: "facebookLink", error: "facebookError", ok: "facebookOk" },
    ].forEach((cfg) => {
      const el = $(cfg.input);
      if (!el) return;

      el.addEventListener("input", () => {
        $(cfg.error)?.classList.add("hidden");
        $(cfg.ok)?.classList.add("hidden");
        el.classList.remove("border-red-500");
      });
    });
  }

  /* =========================
     Save (front validation only)
     - Keep your backend POST in your existing implementation
     - This function is exposed for onclick="saveAccountInfo()"
  ========================= */

  window.saveAccountInfo = async function saveAccountInfo() {
      const firstNameEl = document.getElementById("firstName");
      const lastNameEl  = document.getElementById("lastName");
      const emailEl     = document.getElementById("email");

      // store fields may or may not exist (user vs store)
      const storeNameEl = document.getElementById("storeName");
      const specialtyEl = document.getElementById("storeSpecialty");
      const descEl      = document.getElementById("storeDesc");

      const hasStoreSection = !!storeNameEl; // store tab exists in DOM only if store

      /* ======================
         1️⃣ الاسم الأول
      ====================== */
      if (!firstNameEl?.value.trim() || !isLettersAndSpaces(firstNameEl.value)) {
        setFieldError("firstName", "firstNameError", true, "الاسم الأول مطلوب.");
        firstNameEl?.focus();
        return;
      }

      /* ======================
         2️⃣ الاسم الأخير
      ====================== */
      if (!lastNameEl?.value.trim() || !isLettersAndSpaces(lastNameEl.value)) {
        setFieldError("lastName", "lastNameError", true, "الاسم الأخير مطلوب.");
        lastNameEl?.focus();
        return;
      }

      /* ======================
         🔟 الإيميل (اختياري)
      ====================== */
      if (emailEl && !isValidEmail(emailEl.value.trim())) {
        setFieldError("email", "emailError", true,
          "الرجاء إدخال بريد إلكتروني صحيح (مثال: example@mail.com)."
        );
        emailEl.focus();
        return;
      }

      /* ======================
         ✅ Store-only validation (DON’T break users)
      ====================== */
      if (hasStoreSection) {
        /* 3️⃣ اسم المتجر */
        if (!storeNameEl.value.trim()) {
          setFieldError("storeName", "storeNameError", true, "اسم المتجر مطلوب.");
          storeNameEl.focus();
          return;
        }

        /* 4️⃣ تخصص المتجر */
        if (!specialtyEl?.value.trim()) {
          setFieldError("storeSpecialty", "storeSpecialtyError", true, "تخصص المتجر مطلوب.");
          specialtyEl?.focus();
          return;
        }

        /* 5️⃣ وصف المتجر */
        if (!descEl?.value.trim()) {
          setFieldError("storeDesc", "storeDescError", true, "وصف المتجر مطلوب.");
          descEl?.focus();
          return;
        }

        /* 6️⃣ طرق التواصل */
        if (!hasChecked("input[name='showMobile']")) {
          markBoxError("contactBox", "contactError");
          return;
        }

        /* 7️⃣ طرق الدفع */
        if (!hasChecked("#paymentBox input[type='checkbox']")) {
          markBoxError("paymentBox", "paymentError");
          return;
        }

        /* 8️⃣ سياسة التوصيل */
        if (!hasChecked("input[name='deliveryTime']")) {
          markBoxError("deliveryBox", "deliveryError");
          return;
        }

        /* 9️⃣ سياسة الإرجاع */
        if (!hasChecked("input[name='returnPolicy']")) {
          markBoxError("returnBox", "returnError");
          return;
        }

        /* ⓫ الروابط (اختيارية) */
        for (const cfg of linkChecks) {
          // some inputs like instagram/fb exist only for store; still safe
          const input = document.getElementById(cfg.inputId);
          if (!input) continue;

          if (!validateLinkField(cfg)) {
            input.focus();
            return;
          }
        }
      } else {
        // user-only: only validate email via linkChecks if the field exists
        const emailCfg = linkChecks.find(x => x.inputId === "email");
        if (emailCfg && document.getElementById("email")) {
          if (!validateLinkField(emailCfg)) {
            document.getElementById("email")?.focus();
            return;
          }
        }
      }

      // ✅ passed validation -> now send
      await postAccountInfo(hasStoreSection);
    };

    // ✅ Put this OUTSIDE the function (top-level in the same IIFE/module scope)
    let __infoSaving = false;

    async function postAccountInfo(hasStoreSection) {
      // prevent double submit (onclick + addEventListener, double clicks, etc.)
      if (__infoSaving) return;
      __infoSaving = true;

      const root = document.getElementById("myAccountRoot");
      const url = root?.dataset?.saveUrl;
      const csrf = document.querySelector("input[name='csrfmiddlewaretoken']")?.value;

      if (!url) { console.error("❌ data-save-url missing"); __infoSaving = false; return; }
      if (!csrf) { console.error("❌ CSRF missing"); __infoSaving = false; return; }

      const fd = new FormData();

      // user fields
      fd.append("first_name", (document.getElementById("firstName")?.value || "").trim());
      fd.append("last_name",  (document.getElementById("lastName")?.value || "").trim());
      fd.append("username",   (document.getElementById("nickname")?.value || "").trim());
      fd.append("email",      (document.getElementById("email")?.value || "").trim());

      // profile photo
      const profileFile = document.getElementById("profileImgInput")?.files?.[0];
      if (profileFile) {
        fd.append("profile_photo", profileFile);
      } else if (document.getElementById("profileImage")?.dataset.hasImage === "false") {
        fd.append("remove_profile_photo", "1");
      }

      if (hasStoreSection) {
        fd.append("store_name",        (document.getElementById("storeName")?.value || "").trim());
        fd.append("store_specialty",   (document.getElementById("storeSpecialty")?.value || "").trim());
        fd.append("store_address",     (document.getElementById("storeLocation")?.value || "").trim());
        fd.append("store_website",     (document.getElementById("storeWebsite")?.value || "").trim());
        fd.append("store_instagram",   (document.getElementById("instagramLink")?.value || "").trim());
        fd.append("store_facebook",    (document.getElementById("facebookLink")?.value || "").trim());
        fd.append("store_description", (document.getElementById("storeDesc")?.value || "").trim());

        const logoFile = document.getElementById("storeLogoInput")?.files?.[0];
        if (logoFile) {
          fd.append("store_logo", logoFile);
        } else if (document.getElementById("storeLogoImage")?.dataset.hasImage === "false") {
          fd.append("remove_store_logo", "1");
        }

        fd.append(
          "show_mobile",
          document.querySelector("input[name='showMobile']:checked")?.value || ""
        );

        const payments = Array.from(
          document.querySelectorAll("#paymentBox input[type='checkbox']:checked")
        ).map(x => x.value || "on");
        payments.forEach(p => fd.append("payment_methods", p));

        fd.append(
          "delivery_time",
          document.querySelector("input[name='deliveryTime']:checked")?.value || ""
        );
        fd.append(
          "return_policy",
          document.querySelector("input[name='returnPolicy']:checked")?.value || ""
        );
      }

      const btn = document.getElementById("saveBtn");

      // ✅ store original text once (so it never becomes "جاري الحفظ...")
      if (btn && !btn.dataset.originalText) {
        btn.dataset.originalText = (btn.textContent || "").trim() || "حفظ التعديلات";
      }
      const originalText = btn?.dataset.originalText || "حفظ التعديلات";

      try {
        if (btn) {
          btn.disabled = true;
          btn.classList.add("opacity-70", "cursor-not-allowed");
          btn.textContent = "جاري الحفظ...";
        }

        const res = await fetch(url, {
          method: "POST",
          headers: { "X-CSRFToken": csrf },
          body: fd,
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.ok === false) {
          openSuccessModal(data.message || "حدث خطأ أثناء الحفظ.", "❌ لم يتم الحفظ");
          return;
        }

        openSuccessModal("تم حفظ المعلومات بنجاح", "✔️ تم التحديث");
      } catch (e) {
        console.error(e);
        openSuccessModal("تعذر الاتصال بالخادم. حاول مرة أخرى.", "❌ خطأ");
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.classList.remove("opacity-70", "cursor-not-allowed");
          btn.textContent = originalText; // ✅ always restore the real label
        }
        __infoSaving = false;
      }
    }




  /* =========================
     Init
  ========================= */

  window.addEventListener("load", () => {
    // initialize "hasImage" from current DOM state (Django may render src)
    const profileImg = $("profileImage");
    if (profileImg) {
      profileImg.dataset.hasImage =
        profileImg.getAttribute("src") && profileImg.getAttribute("src").trim() ? "true" : "false";
    }

    const storeLogo = $("storeLogoImage");
    if (storeLogo) {
      storeLogo.dataset.hasImage =
        storeLogo.getAttribute("src") && storeLogo.getAttribute("src").trim() ? "true" : "false";
    }

    bindProfileUpload();
    bindStoreLogoUpload();
    bindLiveInputs();
    bindLinkChecks();

    // initial UI
    refreshDisplayedName();
    refreshProfileInitials();
    refreshStoreLogoInitial();

    // save button click (in addition to onclick attribute, safe to keep both)
    $("saveBtn")?.addEventListener("click", window.saveAccountInfo);
  });
})();
