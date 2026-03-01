

function hasChecked(selector){
  return document.querySelectorAll(selector + ":checked").length > 0;
}

function showGroupError(errorId, show){
  const el = document.getElementById(errorId);
  if(!el) return;
  el.classList.toggle("hidden", !show);
}

function markBoxError(boxId, errorId) {
  const box = document.getElementById(boxId);
  if (!box) return;

  box.classList.add("box-error");
  document.getElementById(errorId)?.classList.remove("hidden");

  box.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearBoxError(boxId, errorId) {
  const box = document.getElementById(boxId);
  if (!box) return;

  box.classList.remove("box-error");
  document.getElementById(errorId)?.classList.add("hidden");
}


/* =========================================================
   ✅ Tabs (works for desktop + mobile tabs)
   ========================================================= */
(function initTabs(){
  const btns = document.querySelectorAll('.tab-btn');
  const tabs = document.querySelectorAll('.tab-content');

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      tabs.forEach(tab => tab.classList.remove('active'));
      const target = document.getElementById('tab-' + btn.dataset.tab);
      if (target) target.classList.add('active');

    });
  });
})();

(function controlSaveButtonVisibility(){
  const saveBtn = document.getElementById("saveBtn");
  if (!saveBtn) return;

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const isInfoTab = btn.dataset.tab === "info";
      saveBtn.style.display = isInfoTab ? "inline-flex" : "none";
    });
  });

  // الحالة الافتراضية عند التحميل
  saveBtn.style.display = "inline-flex";
})();





/* =========================================================
   ✅ Success Modal
   ========================================================= */
function openSuccessModal(message, title = "تم التنفيذ بنجاح") {
  document.getElementById("successMsg").innerText = message;
  document.getElementById("successTitle").innerText = title;
  const modal = document.getElementById("successModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}
function closeSuccessModal() {
  const modal = document.getElementById("successModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

/* =========================================================
   ✅ Account Info (Profile + Validation)
   ========================================================= */
function setFieldError(inputId, errorId, hasError, message) {
  const input = document.getElementById(inputId);
  const error = document.getElementById(errorId);
  if (hasError) {
    if (message) error.textContent = message;
    error.classList.remove("hidden");
    input.classList.add("border-red-500");
  } else {
    error.classList.add("hidden");
    input.classList.remove("border-red-500");
  }
}


function validateLinkField({ inputId, errorId, okId, validator, message }) {
  const input = document.getElementById(inputId);
  const okIcon = document.getElementById(okId);

  const value = (input?.value || "").trim();

  // فاضي = مسموح
  if (!value) {
    setFieldError(inputId, errorId, false);
    okIcon?.classList.add("hidden");
    return true;
  }

  // تحقق
  if (!validator(value)) {
    setFieldError(inputId, errorId, true, message);
    okIcon?.classList.add("hidden");
    return false;
  }

  setFieldError(inputId, errorId, false);
  okIcon?.classList.remove("hidden");
  return true;
}


function validateURLField(inputId, errorId, okId) {
  const input = document.getElementById(inputId);
  const okIcon = document.getElementById(okId);

  if (!input.value.trim()) {
    setFieldError(inputId, errorId, false);
    okIcon?.classList.add("hidden");
    return true;
  }

  if (!isValidURL(input.value.trim())) {
    setFieldError(inputId, errorId, true);
    okIcon?.classList.add("hidden");
    return false;
  }

  setFieldError(inputId, errorId, false);
  okIcon?.classList.remove("hidden");
  return true;
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



function refreshDisplayedName() {
  const storeName = document.getElementById("storeName").value.trim();
  const first     = document.getElementById("firstName").value.trim();
  const last      = document.getElementById("lastName").value.trim();
  const nick      = document.getElementById("nickname").value.trim();

  // الاسم المعروض
  const displayName =
    storeName.length
      ? storeName
      : (nick.length ? nick : `${first} ${last}`.trim());

  document.getElementById("fullName").textContent = displayName;

  // ✅ النص التوضيحي (المكان الصحيح لكودك)
  const noteEl = document.getElementById("displayNote");

  if (storeName.length) {
    noteEl.textContent = "اسم المتجر هو الذي سيظهر للآخرين في الإعلانات والرسائل و كذلك لوجو المتجر .";
  } else {
    noteEl.textContent = "هذا الاسم سيظهر للآخرين في الإعلانات والطلبات والرسائل.";
  }
}



function refreshProfileInitials() {
  const first = document.getElementById("firstName").value.trim();
  const nick  = document.getElementById("nickname").value.trim();
  const initialsSpan = document.getElementById("profileInitials");
  const imgEl = document.getElementById("profileImage");
  const removeBtn = document.getElementById("removeProfileBtn");
  const hasImage = imgEl.dataset.hasImage === "true";

  if (hasImage) {
    initialsSpan.classList.add("hidden");
    removeBtn.classList.add("show");
    return;
  }

  let initial = "؟";
  if (nick.length) initial = nick.charAt(0);
  else if (first.length) initial = first.charAt(0);

  initialsSpan.textContent = initial;
  initialsSpan.classList.remove("hidden");
  removeBtn.classList.remove("show");
  imgEl.classList.add("hidden");
}

function removeProfileImage() {
  const imgEl = document.getElementById('profileImage');
  const initialsSpan = document.getElementById('profileInitials');
  const removeBtn = document.getElementById('removeProfileBtn');
  const fileInput = document.getElementById('profileImgInput');

  imgEl.src = '';
  imgEl.dataset.hasImage = 'false';
  imgEl.classList.add('hidden');
  removeBtn.classList.remove('show');
  initialsSpan.classList.remove('hidden');
  fileInput.value = '';

  refreshProfileInitials();
  refreshDisplayedName();
}

document.getElementById('profileImgInput').addEventListener('change', function (e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (event) {
    const imgEl = document.getElementById('profileImage');
    const initialsSpan = document.getElementById('profileInitials');
    const removeBtn = document.getElementById('removeProfileBtn');

    imgEl.src = event.target.result;
    imgEl.dataset.hasImage = 'true';
    imgEl.classList.remove('hidden');

    initialsSpan.classList.add('hidden');
    removeBtn.classList.add('show');

    refreshDisplayedName();
  };
  reader.readAsDataURL(file);
});
document.getElementById("removeProfileBtn").onclick = removeProfileImage;

// Store logo
function refreshStoreLogoInitial() {
  const storeName = document.getElementById("storeName").value.trim();
  const storeInitialSpan = document.getElementById("storeLogoInitial");
  const imgEl = document.getElementById("storeLogoImage");
  const removeBtn = document.getElementById("removeStoreLogoBtn");
  const hasImage = imgEl.dataset.hasImage === "true";

  if (hasImage) {
    storeInitialSpan.classList.add("hidden");
    removeBtn.classList.add("show");
    return;
  }

  let initial = "م";
  if (storeName.length > 0) initial = storeName.charAt(0);
  storeInitialSpan.textContent = initial;
  storeInitialSpan.classList.remove("hidden");
  removeBtn.classList.remove("show");
  imgEl.classList.add("hidden");
}

function removeStoreLogo() {
  const imgEl = document.getElementById("storeLogoImage");
  const removeBtn = document.getElementById("removeStoreLogoBtn");
   const fileInput = document.getElementById("storeLogoInput");
  
  
  imgEl.src = "";
  imgEl.dataset.hasImage = "false";
  imgEl.classList.add('hidden');
  removeBtn.classList.remove("show");
  fileInput.value = "";
  refreshStoreLogoInitial();
}

document.getElementById("storeLogoInput").addEventListener("change", function (e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function (event) {
    const imgEl = document.getElementById("storeLogoImage");
    const initialEl = document.getElementById("storeLogoInitial");
    const removeBtn = document.getElementById("removeStoreLogoBtn");

    imgEl.src = event.target.result;
    imgEl.dataset.hasImage = "true";
    imgEl.classList.remove("hidden");
    initialEl.classList.add("hidden");
    removeBtn.classList.add("show");
  };
  reader.readAsDataURL(file);
});
document.getElementById("removeStoreLogoBtn").onclick = removeStoreLogo;

function filterNameInput(input) {
  input.value = input.value.replace(/[^a-zA-Z\u0600-\u06FF\s]/g, "");
}

[
  { input: "firstName", error: "firstNameError", filter: true },
  { input: "lastName", error: "lastNameError", filter: true },
  { input: "storeName", error: "storeNameError" },
  { input: "email", error: "emailError" },
  
  { input: "storeLocation" },
  { input: "storeDesc" },
  { input: "nickname" }
].forEach(cfg => {
  const el = document.getElementById(cfg.input);
  if (!el) return;
  el.addEventListener("input", () => {
    if (cfg.filter) filterNameInput(el);
    if (cfg.error) setFieldError(cfg.input, cfg.error, false);
    refreshDisplayedName();
    refreshProfileInitials();
    if (cfg.input === "storeName") refreshStoreLogoInitial();
  });
});

[
  { box: "contactBox", error: "contactError", selector: "input[name='showMobile']" },
  { box: "paymentBox",   error: "paymentError",   selector: "#paymentBox input[type='checkbox']" },
  { box: "deliveryBox",  error: "deliveryError",  selector: "input[name='deliveryTime']" },
  { box: "returnBox",    error: "returnError",    selector: "input[name='returnPolicy']" }
].forEach(cfg => {
  document.querySelectorAll(cfg.selector).forEach(input => {
    input.addEventListener("change", () => {
      clearBoxError(cfg.box, cfg.error);
    });
  });
});

// ✅ إخفاء الخطأ مباشرة عند الكتابة
[
  { input: "storeSpecialty", error: "storeSpecialtyError" },
  { input: "storeDesc",      error: "storeDescError" }
].forEach(cfg => {
  const el = document.getElementById(cfg.input);
  if (!el) return;

  el.addEventListener("input", () => {
    setFieldError(cfg.input, cfg.error, false);
  });
});

const linkChecks = [

   // ✅ الإيميل (نفس الآلية)
  {
    inputId: "email",
    errorId: "emailError",
    okId: "emailOk",   // ✔️ نفس الـ ID في HTML
    validator: isValidEmail,
    message: "الرجاء إدخال بريد إلكتروني صحيح (مثال: example@mail.com)."
  },


    // 1️⃣ الموقع الإلكتروني
    {
      inputId: "storeWebsite",
      errorId: "storeWebsiteError",
      okId: "storeWebsiteOk",
      validator: isValidWebsite,
      message: "الرجاء إدخال رابط موقع الكتروني صحيح (مثال: https://example.com)."
    },

    // 2️⃣ إنستجرام
    {
      inputId: "instagramLink",
      errorId: "instagramError",
      okId: "instagramOk",
      validator: isValidURL,
      message: "الرجاء إدخال رابط انستجرام صحيح (مثال: https://instagram.com/username)."
    },

    // 3️⃣ فيسبوك
    {
      inputId: "facebookLink",
      errorId: "facebookError",
      okId: "facebookOk",
      validator: isValidURL,
      message: "الرجاء إدخال رابط فيس بوك صحيح (مثال: https://facebook.com/page)."
    }
  ];
  
  linkChecks.forEach(cfg => {
  const el = document.getElementById(cfg.inputId);
  if (!el) return;

  el.addEventListener("input", () => validateLinkField(cfg));
});

  
  [
  { input: "email",  error: "emailError", ok: "emailOk" },
  { input: "storeWebsite",  error: "storeWebsiteError", ok: "storeWebsiteOk" },
  { input: "instagramLink", error: "instagramError",    ok: "instagramOk" },
  { input: "facebookLink",  error: "facebookError",     ok: "facebookOk" }
].forEach(cfg => {
  const el = document.getElementById(cfg.input);
  if (!el) return;

  el.addEventListener("input", () => {
    // 🔹 إخفاء رسالة الخطأ
    document.getElementById(cfg.error)?.classList.add("hidden");

    // 🔹 إخفاء علامة الصح (لأننا لم نتحقق بعد)
    document.getElementById(cfg.ok)?.classList.add("hidden");

    // 🔹 إزالة أي ستايل خطأ
    el.classList.remove("border-red-500");
  });
});


function saveAccountInfo() {

  const firstNameEl = document.getElementById("firstName");
  const lastNameEl  = document.getElementById("lastName");
  const storeNameEl = document.getElementById("storeName");
  const specialtyEl = document.getElementById("storeSpecialty");
  const descEl      = document.getElementById("storeDesc");
  const emailEl     = document.getElementById("email");

  /* ======================
     1️⃣ الاسم الأول
  ====================== */
  if (!firstNameEl.value.trim() || !isLettersAndSpaces(firstNameEl.value)) {
    setFieldError("firstName", "firstNameError", true, "الاسم الأول مطلوب.");
    firstNameEl.focus();
    return;
  }

  /* ======================
     2️⃣ الاسم الأخير
  ====================== */
  if (!lastNameEl.value.trim() || !isLettersAndSpaces(lastNameEl.value)) {
    setFieldError("lastName", "lastNameError", true, "الاسم الأخير مطلوب.");
    lastNameEl.focus();
    return;
  }

  /* ======================
     3️⃣ اسم المتجر
  ====================== */
  if (!storeNameEl.value.trim()) {
    setFieldError("storeName", "storeNameError", true, "اسم المتجر مطلوب.");
    storeNameEl.focus();
    return;
  }

  /* ======================
     4️⃣ تخصص المتجر
  ====================== */
  if (!specialtyEl.value.trim()) {
    setFieldError("storeSpecialty", "storeSpecialtyError", true);
    specialtyEl.focus();
    return;
  }

  /* ======================
     5️⃣ وصف المتجر
  ====================== */
  if (!descEl.value.trim()) {
    setFieldError("storeDesc", "storeDescError", true);
    descEl.focus();
    return;
  }

  /* ======================
     6️⃣ طرق التواصل
  ====================== */
  if (!hasChecked("input[name='showMobile']")) {
  markBoxError("contactBox", "contactError");
  return;
}


  /* ======================
     7️⃣ طرق الدفع
  ====================== */
  if (!hasChecked("#paymentBox input[type='checkbox']")) {
    markBoxError("paymentBox", "paymentError");
    return;
  }

  /* ======================
     8️⃣ سياسة التوصيل
  ====================== */
  if (!hasChecked("input[name='deliveryTime']")) {
    markBoxError("deliveryBox", "deliveryError");
    return;
  }

  /* ======================
     9️⃣ سياسة الإرجاع
  ====================== */
  if (!hasChecked("input[name='returnPolicy']")) {
    markBoxError("returnBox", "returnError");
    return;
  }

  /* ======================
     🔟 الإيميل (اختياري)
  ====================== */
  if (!isValidEmail(emailEl.value.trim())) {
    setFieldError("email", "emailError", true, "الرجاء إدخال بريد إلكتروني صحيح (مثال: example@mail.com).");
    emailEl.focus();
    return;
  }

  /* ======================
     ⓫ الروابط (اختيارية)
  ====================== */
  for (const cfg of linkChecks) {
    if (!validateLinkField(cfg)) {
      document.getElementById(cfg.inputId)?.focus();
      return;
    }
  }

  /* ======================
     ✅ نجاح
  ====================== */
  refreshDisplayedName();
  refreshProfileInitials();
  refreshStoreLogoInitial();

  openSuccessModal("تم حفظ معلومات الحساب بنجاح!", "✔️ تم التحديث");
}




/* =========================================================
   ✅ Global Init
   ========================================================= */
window.addEventListener("load", () => {

  const profileImg = document.getElementById("profileImage");
  const storeLogo  = document.getElementById("storeLogoImage");

  if (profileImg) profileImg.dataset.hasImage = "false";
  if (storeLogo)  storeLogo.dataset.hasImage  = "false";

  const saveBtn = document.getElementById("saveBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", saveAccountInfo);
  } else {
    console.error("❌ saveBtn not found in DOM");
  }

  // hide X by default
  document.getElementById("removeProfileBtn")?.classList.remove("show");
  document.getElementById("removeStoreLogoBtn")?.classList.remove("show");

  refreshDisplayedName();
  refreshProfileInitials();
  refreshStoreLogoInitial();

  updateFeaturedDays();
  generateAds();
  generateRequests();

  updateBalance();
  renderTransactions();

  renderFavorites();
  renderNotifications();
  renderConversations();

  setDeleteReasons("ad");
});



function isValidURL(value){
  if (!value) return true;

  return /^(https?:\/\/)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\/.*)?$/i.test(value);
}



