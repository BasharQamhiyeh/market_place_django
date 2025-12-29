/* ===== Icons ===== */
const EYE_OPEN_ICON = `
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5"
     fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274
    4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
</svg>
`;

const EYE_CLOSED_ICON = `
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5"
     fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
  <path stroke-linecap="round" stroke-linejoin="round" d="M10.584 10.587A3 3 0 0113.413 13.41" />
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M6.697 6.7C4.98 8.018 3.74 10.012 3 12c1.274 4.057 5.065 7 9.542 7
       1.53 0 2.984-.288 4.293-.812" />
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M17.31 17.31C19.022 15.989 20.262 13.994 21 12c-.993-3.164-3.49-5.675-6.57-6.62" />
</svg>
`;

function attachToggle(input, btn) {
  if (!input || !btn) return;
  btn.innerHTML = EYE_OPEN_ICON;
  btn.onclick = () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    btn.innerHTML = isHidden ? EYE_CLOSED_ICON : EYE_OPEN_ICON;
  };
}

function csrfTokenFromPage() {
  const el = document.querySelector("input[name=csrfmiddlewaretoken]");
  return el ? el.value : "";
}

/* ===== Mockup error helpers ===== */
function setFieldError(input, msg, holder) {
  if (input) input.classList.add("input-error");
  if (holder) holder.innerHTML = `<p class="field-error">⚠️ ${msg}</p>`;

  if (input) {
    setTimeout(() => {
      input.scrollIntoView({ behavior: "smooth", block: "center" });
      input.focus();
    }, 50);
  }
  return false;
}

function clearErrors() {
  document.querySelectorAll(".input-error").forEach((e) => e.classList.remove("input-error"));
  // IMPORTANT: remove only errors we injected (field-error class)
  document.querySelectorAll(".field-error").forEach((e) => e.remove());

  // clear holders (like mockup)
  [
    "mobileErr",
    "verifyCodeErr",
    "firstNameErr",
    "lastNameErr",
    "storeNameErr",
    "storeLogoErr",
    "pass1Err",
    "pass2Err",
    "acceptTermsErr",
  ].forEach((id) => {
    const h = document.getElementById(id);
    if (h) h.innerHTML = "";
  });
}

function removeFieldError(field) {
  if (!field) return;
  field.classList.remove("input-error");
  const holder = document.getElementById(field.id + "Err");
  if (holder) holder.innerHTML = "";
}

function validatePhone(num) {
  return /^07\d{8}$/.test(num);
}

function digitsOnlyKeydown(e) {
  const allowedKeys = ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab"];
  if ((e.key >= "0" && e.key <= "9") || allowedKeys.includes(e.key)) return;
  e.preventDefault();
}

document.addEventListener("DOMContentLoaded", () => {
  /* ===== Grab elements (same as mockup) ===== */
  const firstName = document.getElementById("firstName");
  const lastName = document.getElementById("lastName");
  const firstNameErr = document.getElementById("firstNameErr");
  const lastNameErr = document.getElementById("lastNameErr");

  const btnPersonal = document.getElementById("btnPersonal");
  const btnStore = document.getElementById("btnStore");
  const conditionVal = document.getElementById("conditionValue");

  const storeBox = document.getElementById("storeBox");
  const storeName = document.getElementById("storeName");
  const storeNameErr = document.getElementById("storeNameErr");

  const storeLogo = document.getElementById("storeLogo");
  const storeLogoErr = document.getElementById("storeLogoErr");
  const logoPreview = document.getElementById("logoPreview");
  const logoPlaceholder = document.getElementById("logoPlaceholder");
  const removeLogo = document.getElementById("removeLogo");

  const mobileForm = document.getElementById("mobileForm");
  const mobile = document.getElementById("mobile");
  const mobileErr = document.getElementById("mobileErr");

  const signupForm = document.getElementById("signupForm");
  const verifiedMobileInput = document.getElementById("verifiedMobile");

  const pass1 = document.getElementById("pass1");
  const pass1Err = document.getElementById("pass1Err");
  const pass2 = document.getElementById("pass2");
  const pass2Err = document.getElementById("pass2Err");

  const togglePass1 = document.getElementById("togglePass1");
  const togglePass2 = document.getElementById("togglePass2");

  const verifyPopup = document.getElementById("verifyPopup");
  const verifyCodeInput = document.getElementById("verifyCodeInput");
  const verifyCodeErr = document.getElementById("verifyCodeErr");
  const checkVerifyCode = document.getElementById("checkVerifyCode");
  const closeVerify = document.getElementById("closeVerify");

  const otpSuccessPopup = document.getElementById("otpSuccessPopup");

  const termsLink = document.getElementById("termsLink");
  const privacyLink = document.getElementById("privacyLink");
  const termsPopup = document.getElementById("termsPopup");
  const privacyPopup = document.getElementById("privacyPopup");
  const closeTerms = document.getElementById("closeTerms");
  const closePrivacy = document.getElementById("closePrivacy");
  const acceptTerms = document.getElementById("acceptTerms");
  const acceptTermsErr = document.getElementById("acceptTermsErr");

  /* Flags */
  let pendingMobile = "";

  /* ===== toggles ===== */
  attachToggle(pass1, togglePass1);
  attachToggle(pass2, togglePass2);

  /* ===== restore step ===== */
  if (window.SIGNUP_RESTORE_STEP === "details") {
    mobileForm?.classList.add("hidden");
    signupForm?.classList.remove("hidden");

    if (verifiedMobileInput && window.SIGNUP_VERIFIED_PHONE) {
      verifiedMobileInput.value = window.SIGNUP_VERIFIED_PHONE;
    }
  }

  /* ===== terms/privacy ===== */
  termsLink && (termsLink.onclick = (e) => { e.preventDefault(); termsPopup.classList.remove("hidden"); });
  privacyLink && (privacyLink.onclick = (e) => { e.preventDefault(); privacyPopup.classList.remove("hidden"); });
  closeTerms && (closeTerms.onclick = () => termsPopup.classList.add("hidden"));
  closePrivacy && (closePrivacy.onclick = () => privacyPopup.classList.add("hidden"));

  document.addEventListener("click", (e) => {
    if (e.target === termsPopup) termsPopup.classList.add("hidden");
    if (e.target === privacyPopup) privacyPopup.classList.add("hidden");
    if (e.target === verifyPopup) verifyPopup.classList.add("hidden");
  });

  /* ===== account type toggle ===== */
  btnPersonal && (btnPersonal.onclick = () => {
    conditionVal.value = "personal";
    btnPersonal.classList.add("toggle-active");
    btnPersonal.style.background = "var(--rukn-orange)";
    btnPersonal.style.color = "white";

    btnStore.classList.remove("toggle-active");
    btnStore.style.background = "white";
    btnStore.style.color = "var(--muted)";

    storeBox.classList.add("hidden");
  });

  btnStore && (btnStore.onclick = () => {
    conditionVal.value = "store";
    btnStore.classList.add("toggle-active");
    btnStore.style.background = "var(--rukn-orange)";
    btnStore.style.color = "white";

    btnPersonal.classList.remove("toggle-active");
    btnPersonal.style.background = "white";
    btnPersonal.style.color = "var(--muted)";

    storeBox.classList.remove("hidden");
  });

  /* ===== store logo preview (mockup) ===== */
  storeLogo && storeLogo.addEventListener("change", () => {
    const file = storeLogo.files && storeLogo.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      logoPreview.src = url;
      logoPreview.classList.remove("hidden");
      logoPlaceholder.classList.add("hidden");
      removeLogo.classList.remove("hidden");
    }
  });

  removeLogo && (removeLogo.onclick = () => {
    storeLogo.value = "";
    logoPreview.src = "";
    logoPreview.classList.add("hidden");
    logoPlaceholder.classList.remove("hidden");
    removeLogo.classList.add("hidden");
  });

  /* ===== remove error on input/change ===== */
  document.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => removeFieldError(field));
    field.addEventListener("change", () => removeFieldError(field));
  });

  /* ===== digits only mobile + verify ===== */
  mobile && mobile.addEventListener("keydown", digitsOnlyKeydown);
  mobile && mobile.addEventListener("input", () => { mobile.value = mobile.value.replace(/\D/g, ""); });

  verifyCodeInput && verifyCodeInput.addEventListener("keydown", digitsOnlyKeydown);
  verifyCodeInput && verifyCodeInput.addEventListener("input", () => { verifyCodeInput.value = verifyCodeInput.value.replace(/\D/g, ""); });

  function openVerifyPopup() {
    verifyCodeInput.value = "";
    verifyCodeErr.innerHTML = "";
    verifyCodeInput.classList.remove("input-error");
    verifyPopup.classList.remove("hidden");
    setTimeout(() => verifyCodeInput.focus(), 50);
  }

  /* =========================================================
     STEP 1: OTP SEND (IMPORTANT: use onsubmit, not addEventListener)
     Also STOP any other submit handlers.
  ========================================================= */
  if (mobileForm) {
    mobileForm.onsubmit = async (e) => {
      e.preventDefault();
      e.stopImmediatePropagation(); // <<< THIS is the key
      clearErrors();

      const val = (mobile.value || "").trim();

      if (!val) return setFieldError(mobile, "رقم الموبايل إجباري", mobileErr);
      if (!validatePhone(val)) return setFieldError(mobile, "الرقم يجب أن يبدأ بـ07 ويتكون من 10 أرقام", mobileErr);

      const fd = new FormData();
      fd.append("phone", val);
      fd.append("csrfmiddlewaretoken", csrfTokenFromPage());

      const res = await fetch(window.SIGNUP_SEND_OTP_URL, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.duplicated) {
          mobile.classList.remove("input-error");
          mobileErr.innerHTML = `
            <div class="field-error">
              هذا الرقم مسجَّل لدينا بالفعل.
            </div>
          `;
          const resetLinkBtn = document.getElementById("resetLink");
          if (resetLinkBtn) {
            resetLinkBtn.onclick = () => {
              window.location.href = "/reset-password?mobile=" + encodeURIComponent(val);
            };
          }
          return false;
        }
        return setFieldError(mobile, data.error || "حدث خطأ", mobileErr);
      }

      pendingMobile = val;
      openVerifyPopup();
    };
  }

  /* ===== STEP 2: OTP VERIFY ===== */
  if (checkVerifyCode) {
    checkVerifyCode.onclick = async () => {
      clearErrors();

      const code = (verifyCodeInput.value || "").trim();
      if (!code) return setFieldError(verifyCodeInput, "أدخل رمز التحقق", verifyCodeErr);
      if (!/^\d{4}$/.test(code)) return setFieldError(verifyCodeInput, "أدخل رمز مكوّن من 4 أرقام", verifyCodeErr);

      const fd = new FormData();
      fd.append("code", code);
      fd.append("csrfmiddlewaretoken", csrfTokenFromPage());

      const res = await fetch(window.SIGNUP_VERIFY_OTP_URL, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        verifyCodeInput.value = "";
        return setFieldError(verifyCodeInput, data.error || "❌ رمز التحقق غير صحيح", verifyCodeErr);
      }

      verifiedMobileInput.value = data.phone || pendingMobile || "";
      verifyPopup.classList.add("hidden");

      otpSuccessPopup.classList.remove("hidden");
      setTimeout(() => {
        otpSuccessPopup.classList.add("hidden");
        mobileForm.classList.add("hidden");
        signupForm.classList.remove("hidden");
      }, 2000);
    };
  }

  closeVerify && (closeVerify.onclick = () => verifyPopup.classList.add("hidden"));

  /* =========================================================
     STEP 3: SIGNUP VALIDATION (EXACT mockup: one field at a time)
     IMPORTANT: use onsubmit + stopImmediatePropagation
  ========================================================= */
  if (signupForm) {
    signupForm.noValidate = true; // disable browser native validation bubbles

    signupForm.onsubmit = (e) => {
      e.preventDefault();
      e.stopImmediatePropagation(); // <<< THIS prevents any other listeners from submitting
      clearErrors();

      // 1) first name
      if (!firstName.value.trim()) return setFieldError(firstName, "الاسم الأول إجباري", firstNameErr);

      // 2) last name
      if (!lastName.value.trim()) return setFieldError(lastName, "الاسم الأخير إجباري", lastNameErr);

      // 3) store name if store (Arabic)
      if (conditionVal.value === "store") {
        if (!storeName.value.trim()) return setFieldError(storeName, "اسم المتجر إجباري", storeNameErr);
      }

      // 4) password rules
      const pwd = pass1.value.trim();
      if (!pwd) return setFieldError(pass1, "كلمة المرور مطلوبة", pass1Err);
      if (pwd.length < 8) return setFieldError(pass1, "كلمة المرور يجب أن تكون 8 أحرف على الأقل", pass1Err);
      if (!/[A-Za-z]/.test(pwd) || !/\d/.test(pwd))
        return setFieldError(pass1, "كلمة المرور يجب أن تحتوي على أحرف وأرقام معاً", pass1Err);

      // 5) confirm password (REQUIRED)
      const pwd2 = pass2.value.trim();
      if (!pwd2) return setFieldError(pass2, "تأكيد كلمة المرور مطلوب", pass2Err);
      if (pwd !== pwd2) return setFieldError(pass2, "كلمتا المرور غير متطابقتين", pass2Err);

      // 6) terms
      if (!acceptTerms.checked)
        return setFieldError(acceptTerms, "يجب الموافقة على الشروط والأحكام قبل إنشاء الحساب", acceptTermsErr);

      // ✅ valid => submit ONLY ONCE (and bypass this handler)
      signupForm.onsubmit = null;
      signupForm.submit();
    };
  }
});
