/* =========================================================
   Tabs logic (desktop + mobile)
========================================================= */
(function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const tabs = document.querySelectorAll(".tab-content");

  function openTab(key) {
    buttons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === key);
    });

    tabs.forEach(tab => {
      tab.classList.toggle("active", tab.id === "tab-" + key);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => openTab(btn.dataset.tab));
  });

  const hash = window.location.hash.replace("#", "");
  if (hash && document.getElementById("tab-" + hash)) openTab(hash);
})();


/* =========================================================
   my_account.js (UPDATED)
   - Supports normal user vs store account
========================================================= */
(function () {
  const $ = (id) => document.getElementById(id);

  const HAS_STORE = document.documentElement.dataset.hasStore === "1";

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function csrfToken() {
    return getCookie("csrftoken");
  }

  function showToast(message) {
    alert(message);
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

  function isValidWebsite(value) {
    if (!value) return true;
    return /^(https?:\/\/)?(www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(\/.*)?$/.test(value);
  }

  function safeTrim(id) {
    const el = $(id);
    return (el?.value || "").trim();
  }

  function filterNameInput(el) {
    el.value = el.value.replace(/[^a-zA-Z\u0600-\u06FF\s]/g, "");
  }

  /* --------------------------
     Live displayed name + note
  -------------------------- */
  function refreshDisplayedName() {
    const first = safeTrim("firstName");
    const last  = safeTrim("lastName");
    const nick  = safeTrim("nickname");
    const storeName = HAS_STORE ? safeTrim("storeName") : "";

    const fullNameEl = $("fullName");
    const noteEl = $("displayNote");
    if (!fullNameEl || !noteEl) return;

    const displayName =
      (HAS_STORE && storeName.length)
        ? storeName
        : (nick.length ? nick : `${first} ${last}`.trim());

    fullNameEl.textContent = displayName || "—";

    if (HAS_STORE && storeName.length) {
      noteEl.textContent = "اسم المتجر هو الذي سيظهر للآخرين في الإعلانات والرسائل و كذلك لوجو المتجر .";
    } else {
      noteEl.textContent = "هذا الاسم سيظهر للآخرين في الإعلانات والطلبات والرسائل.";
    }
  }

  /* --------------------------
     Initials logic
  -------------------------- */
  function refreshProfileInitials() {
    const initialsSpan = $("profileInitials");
    const imgEl = $("profileImage");
    const removeBtn = $("removeProfileBtn");
    if (!initialsSpan || !imgEl || !removeBtn) return;

    const hasImage = imgEl.dataset.hasImage === "true";
    if (hasImage) {
      initialsSpan.classList.add("hidden");
      removeBtn.classList.add("show");
      imgEl.classList.remove("hidden");
      return;
    }

    const nick = safeTrim("nickname");
    const first = safeTrim("firstName");

    let initial = "؟";
    if (nick.length) initial = nick.charAt(0);
    else if (first.length) initial = first.charAt(0);

    initialsSpan.textContent = initial;
    initialsSpan.classList.remove("hidden");
    removeBtn.classList.remove("show");
    imgEl.classList.add("hidden");
  }

  function refreshStoreLogoInitial() {
    if (!HAS_STORE) return;

    const initialEl = $("storeLogoInitial");
    const imgEl = $("storeLogoImage");
    const removeBtn = $("removeStoreLogoBtn");
    if (!initialEl || !imgEl || !removeBtn) return;

    const hasImage = imgEl.dataset.hasImage === "true";
    if (hasImage) {
      initialEl.classList.add("hidden");
      removeBtn.classList.add("show");
      imgEl.classList.remove("hidden");
      return;
    }

    const storeName = safeTrim("storeName");
    let initial = "م";
    if (storeName.length) initial = storeName.charAt(0);

    initialEl.textContent = initial;
    initialEl.classList.remove("hidden");
    removeBtn.classList.remove("show");
    imgEl.classList.add("hidden");
  }

  /* --------------------------
     Profile image: preview/remove
  -------------------------- */
  function removeProfileImage() {
    const imgEl = $("profileImage");
    const input = $("profileImgInput");
    if (!imgEl || !input) return;

    imgEl.src = "";
    imgEl.dataset.hasImage = "false";
    imgEl.classList.add("hidden");
    input.value = "";

    refreshProfileInitials();
    refreshDisplayedName();
  }

  function bindProfileUpload() {
    const input = $("profileImgInput");
    const imgEl = $("profileImage");
    const removeBtn = $("removeProfileBtn");
    if (!input || !imgEl || !removeBtn) return;

    input.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (ev) => {
        imgEl.src = ev.target.result;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
        removeBtn.classList.add("show");
        refreshProfileInitials();
        refreshDisplayedName();
      };
      reader.readAsDataURL(file);
    });

    removeBtn.addEventListener("click", removeProfileImage);
  }

  /* --------------------------
     Store logo: preview/remove
  -------------------------- */
  function removeStoreLogo() {
    if (!HAS_STORE) return;

    const imgEl = $("storeLogoImage");
    const input = $("storeLogoInput");
    if (!imgEl || !input) return;

    imgEl.src = "";
    imgEl.dataset.hasImage = "false";
    imgEl.classList.add("hidden");
    input.value = "";

    refreshStoreLogoInitial();
    refreshDisplayedName();
  }

  function bindStoreLogoUpload() {
    if (!HAS_STORE) return;

    const input = $("storeLogoInput");
    const imgEl = $("storeLogoImage");
    const removeBtn = $("removeStoreLogoBtn");
    if (!input || !imgEl || !removeBtn) return;

    input.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (ev) => {
        imgEl.src = ev.target.result;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
        removeBtn.classList.add("show");
        refreshStoreLogoInitial();
      };
      reader.readAsDataURL(file);
    });

    removeBtn.addEventListener("click", removeStoreLogo);
  }

  /* --------------------------
     Validation + Save
  -------------------------- */
  function validateAccountForm() {
    const first = safeTrim("firstName");
    const last = safeTrim("lastName");
    const email = safeTrim("email");

    // store fields (optional, only if HAS_STORE)
    const storeName = HAS_STORE ? safeTrim("storeName") : "";
    const website = HAS_STORE ? safeTrim("storeWebsite") : "";

    if (!first || !isLettersAndSpaces(first)) {
      setFieldError("firstName", "firstNameError", true, "الاسم الأول مطلوب.");
      $("firstName")?.focus();
      return false;
    }
    setFieldError("firstName", "firstNameError", false);

    if (!last || !isLettersAndSpaces(last)) {
      setFieldError("lastName", "lastNameError", true, "الاسم الأخير مطلوب.");
      $("lastName")?.focus();
      return false;
    }
    setFieldError("lastName", "lastNameError", false);

    if (HAS_STORE) {
      if (!storeName) {
        setFieldError("storeName", "storeNameError", true, "اسم المتجر مطلوب.");
        $("storeName")?.focus();
        return false;
      }
      setFieldError("storeName", "storeNameError", false);

      if (!isValidWebsite(website)) {
        setFieldError("storeWebsite", "storeWebsiteError", true, "الرجاء إدخال رابط صحيح (مثال: https://example.com).");
        $("storeWebsite")?.focus();
        return false;
      }
      setFieldError("storeWebsite", "storeWebsiteError", false);
    }

    if (!isValidEmail(email)) {
      setFieldError("email", "emailError", true, "الرجاء إدخال بريد إلكتروني صحيح.");
      $("email")?.focus();
      return false;
    }
    setFieldError("email", "emailError", false);

    return true;
  }

  async function saveAccountInfo() {
    if (!validateAccountForm()) return;

    refreshDisplayedName();
    refreshProfileInitials();
    if (HAS_STORE) refreshStoreLogoInitial();

    const form = $("accountForm");
    const saveBtn = $("saveBtn");

    const saveUrl =
      form?.dataset.saveUrl ||
      saveBtn?.dataset.saveUrl ||
      saveBtn?.dataset.url ||
      "";

    if (!saveUrl) {
      console.error("Missing save URL. Add data-save-url on #saveBtn or #accountForm.");
      showToast("❌ لم يتم إعداد رابط الحفظ بعد (data-save-url).");
      return;
    }

    const fd = new FormData();

    // user fields
    fd.append("first_name", safeTrim("firstName"));
    fd.append("last_name", safeTrim("lastName"));
    fd.append("username", safeTrim("nickname"));
    fd.append("email", safeTrim("email"));

    // profile file
    const profileFile = $("profileImgInput")?.files?.[0];
    if (profileFile) fd.append("profile_photo", profileFile);

    const profileImg = $("profileImage");
    if (profileImg && profileImg.dataset.hasImage === "false") {
      fd.append("remove_profile_photo", "1");
    }

    // store fields ONLY if HAS_STORE
    if (HAS_STORE) {
      fd.append("store_name", safeTrim("storeName"));
      fd.append("store_address", safeTrim("storeLocation"));
      fd.append("store_city_id", safeTrim("storeCity"));
      fd.append("store_website", safeTrim("storeWebsite"));
      fd.append("store_instagram", safeTrim("storeInstagram"));
      fd.append("store_facebook", safeTrim("storeFacebook"));
      fd.append("store_description", (form?.querySelector("#storeDesc")?.value || "").trim());

      const storeLogoFile = $("storeLogoInput")?.files?.[0];
      if (storeLogoFile) fd.append("store_logo", storeLogoFile);

      const storeLogoImg = $("storeLogoImage");
      if (storeLogoImg && storeLogoImg.dataset.hasImage === "false") {
        fd.append("remove_store_logo", "1");
      }
    }

    const oldText = saveBtn?.textContent;
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "⏳ جاري الحفظ...";
    }

    try {
      const res = await fetch(saveUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
        body: fd,
      });

      let data = null;
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) data = await res.json();
      else data = { ok: res.ok };

      if (!res.ok || !data?.ok) {
          // Reset all visible field errors first
          setFieldError("firstName", "firstNameError", false);
          setFieldError("lastName", "lastNameError", false);
          setFieldError("email", "emailError", false);

          if (HAS_STORE) {
            setFieldError("storeName", "storeNameError", false);
            setFieldError("storeWebsite", "storeWebsiteError", false);
          }

          // Map backend errors -> UI
          if (data?.errors) {
            console.error("Save errors:", data.errors);

            // email
            if (data.errors.email?.length) {
              setFieldError("email", "emailError", true, data.errors.email[0]);
              $("email")?.focus();
            }

            // optional mappings if your backend uses these keys:
            if (data.errors.first_name?.length) {
              setFieldError("firstName", "firstNameError", true, data.errors.first_name[0]);
            }
            if (data.errors.last_name?.length) {
              setFieldError("lastName", "lastNameError", true, data.errors.last_name[0]);
            }

            if (HAS_STORE) {
              if (data.errors.store_name?.length) {
                setFieldError("storeName", "storeNameError", true, data.errors.store_name[0]);
              }
              if (data.errors.store_website?.length) {
                setFieldError("storeWebsite", "storeWebsiteError", true, data.errors.store_website[0]);
              }
            }

            // show generic message too (optional)
            showToast(data.message || "❌ يرجى تصحيح الأخطاء.");
          } else {
            showToast(data?.message || "❌ حصل خطأ أثناء حفظ المعلومات.");
          }
          return;
        }


      if (data.profile_photo_url && $("profileImage")) {
        const imgEl = $("profileImage");
        imgEl.src = data.profile_photo_url;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
      }

      if (HAS_STORE && data.store_logo_url && $("storeLogoImage")) {
        const imgEl = $("storeLogoImage");
        imgEl.src = data.store_logo_url;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
      }

      showToast(data?.message || "✅ تم حفظ معلومات الحساب بنجاح!");
    } catch (e) {
      console.error(e);
      showToast("❌ تعذّر الاتصال بالسيرفر. حاول مرة أخرى.");
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = oldText || "💾 حفظ التعديلات";
      }
    }
  }

  /* --------------------------
     Bind live events
  -------------------------- */
  function bindLiveInputs() {
    const configs = [
      { id: "firstName", error: "firstNameError", filter: true },
      { id: "lastName", error: "lastNameError", filter: true },
      { id: "nickname" },
      { id: "email", error: "emailError" },

      ...(HAS_STORE ? [
        { id: "storeName", error: "storeNameError" },
        { id: "storeWebsite", error: "storeWebsiteError" },
        { id: "storeLocation" },
        { id: "storeCity" },
        { id: "storeInstagram" },
        { id: "storeFacebook" },
        { id: "storeDesc" },
      ] : []),
    ];

    configs.forEach((cfg) => {
      const el = $(cfg.id);
      if (!el) return;

      el.addEventListener("input", () => {
        if (cfg.filter) filterNameInput(el);
        if (cfg.error) setFieldError(cfg.id, cfg.error, false);

        refreshDisplayedName();
        refreshProfileInitials();
        if (HAS_STORE && cfg.id === "storeName") refreshStoreLogoInitial();
      });
    });
  }

  function init() {
    const pImg = $("profileImage");
    if (pImg && !pImg.dataset.hasImage) {
      pImg.dataset.hasImage = pImg.src ? "true" : "false";
    }

    const sImg = $("storeLogoImage");
    if (HAS_STORE && sImg && !sImg.dataset.hasImage) {
      sImg.dataset.hasImage = sImg.src ? "true" : "false";
    }

    bindProfileUpload();
    if (HAS_STORE) bindStoreLogoUpload();
    bindLiveInputs();

    $("saveBtn")?.addEventListener("click", saveAccountInfo);

    refreshDisplayedName();
    refreshProfileInitials();
    if (HAS_STORE) refreshStoreLogoInitial();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
