/* =========================================================
   info.js (UPDATED)
   - Single Save button posts EVERYTHING (user + avatar + store + store logo)
   - Optional URL fields:
       - empty => OK
       - if provided, auto-normalize to https://...
   - Handles backend errors in BOTH shapes + store model field names:
       { ok:false, errors:{ website:[...], instagram:[...], facebook:[...] } }
       { ok:false, field:"store_name", error:"store_name_required" }
========================================================= */

(function () {
  const root = document.getElementById("myAccountRoot");
  if (!root) return;

  const HAS_STORE = root.dataset.hasStore === "1";
  const SAVE_URL = root.dataset.saveUrl || "";

  const $ = (id) => document.getElementById(id);

  /* --------------------------
     Cookies / CSRF
  -------------------------- */
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }
  function csrfToken() {
    return getCookie("csrftoken");
  }

  /* --------------------------
     UI helpers
  -------------------------- */
  function toast(msg) {
    alert(msg);
  }

  function setFieldError(inputId, errorId, hasError, message) {
    const input = $(inputId);
    const error = $(errorId);
    if (!error) return;

    error.textContent = message || "";
    error.classList.toggle("hidden", !hasError);

    if (input) {
      input.classList.toggle("border-red-500", !!hasError);
    }
  }

  function clearErrors() {
    setFieldError("firstName", "firstNameError", false, "");
    setFieldError("lastName", "lastNameError", false, "");
    setFieldError("email", "emailError", false, "");

    if (HAS_STORE) {
      setFieldError("storeName", "storeNameError", false, "");
      setFieldError("storeWebsite", "storeWebsiteError", false, "");
      // NOTE: you don't have instagram/facebook error <p> in HTML.
      // If you add them later, add them here too.
    }
  }

  function safeTrim(id) {
    return (($(id)?.value) || "").trim();
  }

  /* --------------------------
     URL normalization (IMPORTANT)
     - Optional fields:
       "" => ""
       "www.site.com" => "https://www.site.com"
       "site.com"     => "https://site.com"
       "http://..." or "https://..." keep
  -------------------------- */
  function normalizeUrl(value) {
    const v = (value || "").trim();
    if (!v) return "";
    if (/^https?:\/\//i.test(v)) return v;
    return "https://" + v;
  }

  /* --------------------------
     Live display name + note
  -------------------------- */
  function refreshDisplayedName() {
    const first = safeTrim("firstName");
    const last = safeTrim("lastName");
    const nick = safeTrim("nickname");
    const storeName = HAS_STORE ? safeTrim("storeName") : "";

    const fullNameEl = $("fullName");
    const noteEl = $("displayNote");
    if (!fullNameEl || !noteEl) return;

    const displayName =
      (HAS_STORE && storeName) ? storeName :
      (nick ? nick : `${first} ${last}`.trim());

    fullNameEl.textContent = displayName || "—";
    noteEl.textContent = (HAS_STORE && storeName)
      ? "اسم المتجر هو الذي سيظهر للآخرين في الإعلانات والرسائل و كذلك لوجو المتجر ."
      : "هذا الاسم سيظهر للآخرين في الإعلانات والطلبات والرسائل.";
  }

  /* --------------------------
     Avatar initials + preview/remove
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
    const initial = (nick || first || "؟").charAt(0);

    initialsSpan.textContent = initial;
    initialsSpan.classList.remove("hidden");
    removeBtn.classList.remove("show");
    imgEl.classList.add("hidden");
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

    removeBtn.addEventListener("click", () => {
      imgEl.src = "";
      imgEl.dataset.hasImage = "false"; // backend removes on save
      imgEl.classList.add("hidden");
      input.value = "";
      refreshProfileInitials();
      refreshDisplayedName();
    });
  }

  /* --------------------------
     Store logo initials + preview/remove (store only)
  -------------------------- */
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
    initialEl.textContent = (storeName || "م").charAt(0);
    initialEl.classList.remove("hidden");
    removeBtn.classList.remove("show");
    imgEl.classList.add("hidden");
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
        refreshDisplayedName();
      };
      reader.readAsDataURL(file);
    });

    removeBtn.addEventListener("click", () => {
      imgEl.src = "";
      imgEl.dataset.hasImage = "false"; // backend removes on save
      imgEl.classList.add("hidden");
      input.value = "";
      refreshStoreLogoInitial();
      refreshDisplayedName();
    });
  }

  /* --------------------------
     Validation
     - Optional URL fields: validate only if not empty (after normalize)
  -------------------------- */
  function isLettersAndSpaces(v) {
    return /^[a-zA-Z\u0600-\u06FF\s]+$/.test(v || "");
  }
  function isValidEmail(v) {
    return !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }
  function looksLikeUrl(v) {
    // after normalization, must be http(s)://domain...
    return /^https?:\/\/[^\s/$.?#].[^\s]*$/i.test(v || "");
  }

  function validate() {
    clearErrors();

    const first = safeTrim("firstName");
    const last = safeTrim("lastName");
    const email = safeTrim("email");

    if (!first || !isLettersAndSpaces(first)) {
      setFieldError("firstName", "firstNameError", true, "الاسم الأول مطلوب.");
      return false;
    }
    if (!last || !isLettersAndSpaces(last)) {
      setFieldError("lastName", "lastNameError", true, "الاسم الأخير مطلوب.");
      return false;
    }
    if (!isValidEmail(email)) {
      setFieldError("email", "emailError", true, "الرجاء إدخال بريد إلكتروني صحيح.");
      return false;
    }

    if (HAS_STORE) {
      const storeName = safeTrim("storeName");
      if (!storeName) {
        setFieldError("storeName", "storeNameError", true, "اسم المتجر مطلوب.");
        return false;
      }

      // optional URLs (only validate if user typed something)
      const website = normalizeUrl(safeTrim("storeWebsite"));
      if (website && !looksLikeUrl(website)) {
        setFieldError("storeWebsite", "storeWebsiteError", true, "الرجاء إدخال رابط صحيح (https://...).");
        return false;
      }

      // instagram/facebook are optional too; we validate softly via toast (no inline error elements)
      const insta = normalizeUrl(safeTrim("storeInstagram"));
      if (insta && !looksLikeUrl(insta)) {
        toast("رابط انستغرام غير صالح. استخدم مثال: https://instagram.com/...");
        return false;
      }

      const fb = normalizeUrl(safeTrim("storeFacebook"));
      if (fb && !looksLikeUrl(fb)) {
        toast("رابط فيسبوك غير صالح. استخدم مثال: https://facebook.com/...");
        return false;
      }
    }

    return true;
  }

  /* --------------------------
     Backend error mapping
     - Supports:
       errors.store_website OR errors.website
       errors.instagram OR errors.store_instagram
       errors.facebook  OR errors.store_facebook
  -------------------------- */
  function applyBackendErrors(payload) {
    const errors = payload?.errors || null;

    // Manual shape: {field, error}
    if (!errors && payload?.field) {
      if (payload.field === "first_name") setFieldError("firstName", "firstNameError", true, "الاسم الأول مطلوب.");
      if (payload.field === "last_name") setFieldError("lastName", "lastNameError", true, "الاسم الأخير مطلوب.");
      if (payload.field === "store_name") setFieldError("storeName", "storeNameError", true, "اسم المتجر مطلوب.");
      return;
    }

    if (!errors) return;

    // user
    if (errors.first_name?.[0]) setFieldError("firstName", "firstNameError", true, errors.first_name[0]);
    if (errors.last_name?.[0]) setFieldError("lastName", "lastNameError", true, errors.last_name[0]);
    if (errors.email?.[0]) setFieldError("email", "emailError", true, errors.email[0]);
    if (errors.username?.[0]) toast(errors.username[0]);

    if (!HAS_STORE) return;

    // store required
    if (errors.store_name?.[0]) setFieldError("storeName", "storeNameError", true, errors.store_name[0]);

    // website can come as store_website OR website (model field name)
    const websiteErr = (errors.store_website?.[0] || errors.website?.[0] || "");
    if (websiteErr) setFieldError("storeWebsite", "storeWebsiteError", true, websiteErr);

    // instagram/facebook: you don't have inline error blocks -> toast
    const instaErr = (errors.store_instagram?.[0] || errors.instagram?.[0] || "");
    if (instaErr) toast(instaErr);

    const fbErr = (errors.store_facebook?.[0] || errors.facebook?.[0] || "");
    if (fbErr) toast(fbErr);
  }

  /* --------------------------
     Save: one POST with everything
  -------------------------- */
  async function save() {
    if (!SAVE_URL) {
      toast("❌ data-save-url غير موجود.");
      return;
    }
    if (!validate()) return;

    const fd = new FormData();

    // user fields
    fd.append("first_name", safeTrim("firstName"));
    fd.append("last_name", safeTrim("lastName"));
    fd.append("username", safeTrim("nickname"));
    fd.append("email", safeTrim("email"));

    // avatar file
    const profileFile = $("profileImgInput")?.files?.[0];
    if (profileFile) fd.append("profile_photo", profileFile);

    // avatar remove flag
    const profileImg = $("profileImage");
    if (profileImg && profileImg.dataset.hasImage === "false") {
      fd.append("remove_profile_photo", "1");
    }

    // store fields
    if (HAS_STORE) {
      fd.append("store_name", safeTrim("storeName"));
      fd.append("store_address", safeTrim("storeLocation"));
      fd.append("store_city_id", safeTrim("storeCity"));

      // OPTIONAL URL fields: normalize before sending
      fd.append("store_website", normalizeUrl(safeTrim("storeWebsite")));
      fd.append("store_instagram", normalizeUrl(safeTrim("storeInstagram")));
      fd.append("store_facebook", normalizeUrl(safeTrim("storeFacebook")));

      fd.append("store_desc", ($("storeDesc")?.value || "").trim());

      const storeLogoFile = $("storeLogoInput")?.files?.[0];
      if (storeLogoFile) fd.append("store_logo", storeLogoFile);

      const storeLogoImg = $("storeLogoImage");
      if (storeLogoImg && storeLogoImg.dataset.hasImage === "false") {
        fd.append("remove_store_logo", "1");
      }
    }

    const saveBtn = $("saveBtn");
    const oldText = saveBtn?.textContent;
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "⏳ جاري الحفظ...";
    }

    try {
      const res = await fetch(SAVE_URL, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
        body: fd,
      });

      let data = null;
      const ct = res.headers.get("content-type") || "";

      if (ct.includes("application/json")) {
        data = await res.json();
      } else {
        const text = await res.text();
        console.error("Non-JSON response:", text);
        data = { ok: res.ok, message: text };
      }

      if (!res.ok || !data?.ok) {
        console.error("Save failed:", { status: res.status, data });
        applyBackendErrors(data);
        toast(data?.message || "❌ حصل خطأ أثناء الحفظ.");
        return;
      }

      // Update avatar URL from backend
      if (data.profile_photo_url && $("profileImage")) {
        const imgEl = $("profileImage");
        imgEl.src = data.profile_photo_url;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
        $("removeProfileBtn")?.classList.add("show");
        $("profileInitials")?.classList.add("hidden");
      }

      // Update store logo URL from backend
      if (HAS_STORE && data.store_logo_url && $("storeLogoImage")) {
        const imgEl = $("storeLogoImage");
        imgEl.src = data.store_logo_url;
        imgEl.dataset.hasImage = "true";
        imgEl.classList.remove("hidden");
        $("removeStoreLogoBtn")?.classList.add("show");
        $("storeLogoInitial")?.classList.add("hidden");
      }

      refreshDisplayedName();
      refreshProfileInitials();
      refreshStoreLogoInitial();

      toast(data.message || "✅ تم حفظ معلومات الحساب بنجاح!");
    } catch (e) {
      console.error(e);
      toast("❌ تعذّر الاتصال بالسيرفر.");
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = oldText || "💾 حفظ التعديلات";
      }
    }
  }

  /* --------------------------
     Bind inputs
  -------------------------- */
  function bindInputs() {
    ["firstName", "lastName", "nickname", "email"].forEach((id) => {
      $(id)?.addEventListener("input", () => {
        refreshDisplayedName();
        refreshProfileInitials();
      });
    });

    if (HAS_STORE) {
      ["storeName", "storeLocation", "storeCity", "storeWebsite", "storeInstagram", "storeFacebook", "storeDesc"].forEach((id) => {
        $(id)?.addEventListener("input", () => {
          refreshDisplayedName();
          refreshStoreLogoInitial();
        });
      });
    }
  }

  function init() {
    const pImg = $("profileImage");
    if (pImg && !pImg.dataset.hasImage) pImg.dataset.hasImage = pImg.src ? "true" : "false";

    if (HAS_STORE) {
      const sImg = $("storeLogoImage");
      if (sImg && !sImg.dataset.hasImage) sImg.dataset.hasImage = sImg.src ? "true" : "false";
    }

    bindProfileUpload();
    bindStoreLogoUpload();
    bindInputs();

    $("saveBtn")?.addEventListener("click", save);

    refreshDisplayedName();
    refreshProfileInitials();
    refreshStoreLogoInitial();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
