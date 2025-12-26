// ===== Icons (same as mockup behavior) =====
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

function attachToggle(inputId, btnId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(btnId);
  if (!input || !btn) return;

  btn.innerHTML = EYE_OPEN_ICON;
  btn.addEventListener("click", () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    btn.innerHTML = isHidden ? EYE_CLOSED_ICON : EYE_OPEN_ICON;
  });
}

function csrfTokenFromPage() {
  const el = document.querySelector("input[name=csrfmiddlewaretoken]");
  return el ? el.value : "";
}

function setErr(el, html) {
  if (!el) return;
  el.innerHTML = html || "";
}

document.addEventListener("DOMContentLoaded", () => {
  attachToggle("pass1", "togglePass1");
  attachToggle("pass2", "togglePass2");

  const mobileForm = document.getElementById("mobileForm");
  const mobile = document.getElementById("mobile");
  const mobileErr = document.getElementById("mobileErr");

  const verifyPopup = document.getElementById("verifyPopup");
  const verifyCodeInput = document.getElementById("verifyCodeInput");
  const verifyCodeErr = document.getElementById("verifyCodeErr");
  const checkVerifyCode = document.getElementById("checkVerifyCode");
  const closeVerify = document.getElementById("closeVerify");

  const otpSuccessPopup = document.getElementById("otpSuccessPopup");

  const signupForm = document.getElementById("signupForm");
  const verifiedMobile = document.getElementById("verifiedMobile");

  const termsLink = document.getElementById("termsLink");
  const privacyLink = document.getElementById("privacyLink");
  const termsPopup = document.getElementById("termsPopup");
  const privacyPopup = document.getElementById("privacyPopup");
  const closeTerms = document.getElementById("closeTerms");
  const closePrivacy = document.getElementById("closePrivacy");

  const btnPersonal = document.getElementById("btnPersonal");
  const btnStore = document.getElementById("btnStore");
  const storeBox = document.getElementById("storeBox");
  const conditionValue = document.getElementById("conditionValue");

  // ✅ NEW: restore step after page reload (server-side render with errors)
  // Template must set:
  // window.SIGNUP_RESTORE_STEP = "details" (or "")
  // window.SIGNUP_VERIFIED_PHONE = "07xxxxxxxx" (or "")
  if (window.SIGNUP_RESTORE_STEP === "details") {
    mobileForm?.classList.add("hidden");
    signupForm?.classList.remove("hidden");

    if (verifiedMobile && window.SIGNUP_VERIFIED_PHONE) {
      verifiedMobile.value = window.SIGNUP_VERIFIED_PHONE;
    }

    // Also restore account type UI if backend rendered it into the hidden input
    if (conditionValue?.value === "store") {
      btnStore?.classList.add("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      btnPersonal?.classList.remove("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      storeBox?.classList.remove("hidden");
    } else {
      btnPersonal?.classList.add("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      btnStore?.classList.remove("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      storeBox?.classList.add("hidden");
    }
  }

  function openVerifyPopup() {
    verifyCodeInput.value = "";
    setErr(verifyCodeErr, "");
    verifyPopup.classList.remove("hidden");
    setTimeout(() => verifyCodeInput.focus(), 50);
  }
  function closeVerifyPopup() {
    verifyPopup.classList.add("hidden");
  }

  closeVerify?.addEventListener("click", (e) => {
    e.preventDefault();
    closeVerifyPopup();
  });

  // close popups on backdrop click
  verifyPopup?.addEventListener("click", (e) => { if (e.target === verifyPopup) closeVerifyPopup(); });
  termsPopup?.addEventListener("click", (e) => { if (e.target === termsPopup) termsPopup.classList.add("hidden"); });
  privacyPopup?.addEventListener("click", (e) => { if (e.target === privacyPopup) privacyPopup.classList.add("hidden"); });

  // open terms/privacy
  termsLink?.addEventListener("click", (e) => { e.preventDefault(); termsPopup?.classList.remove("hidden"); });
  privacyLink?.addEventListener("click", (e) => { e.preventDefault(); privacyPopup?.classList.remove("hidden"); });
  closeTerms?.addEventListener("click", () => termsPopup?.classList.add("hidden"));
  closePrivacy?.addEventListener("click", () => privacyPopup?.classList.add("hidden"));

  // account type toggle UI (UI only)
  function setAccountType(type) {
    if (!btnPersonal || !btnStore || !conditionValue) return;
    if (type === "store") {
      btnStore.classList.add("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      btnPersonal.classList.remove("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      storeBox?.classList.remove("hidden");
      conditionValue.value = "store";
    } else {
      btnPersonal.classList.add("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      btnStore.classList.remove("toggle-active", "bg-[var(--rukn-orange)]", "text-white");
      storeBox?.classList.add("hidden");
      conditionValue.value = "personal";
    }
  }
  btnPersonal?.addEventListener("click", () => setAccountType("personal"));
  btnStore?.addEventListener("click", () => setAccountType("store"));

  // STEP 1: send OTP
  mobileForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    setErr(mobileErr, "");

    const val = (mobile.value || "").trim();

    if (!/^07\d{8}$/.test(val)) {
      setErr(mobileErr, `<p class="field-error">⚠️ رقم الهاتف يجب أن يبدأ بـ 07 ويتكون من 10 أرقام</p>`);
      return;
    }

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
        setErr(mobileErr, `<p class="field-error">هذا الرقم مسجَّل لدينا بالفعل.</p>`);
      } else {
        setErr(mobileErr, `<p class="field-error">⚠️ ${data.error || "حدث خطأ"}</p>`);
      }
      return;
    }

    openVerifyPopup();
  });

  // STEP 2: verify OTP (popup)
  checkVerifyCode?.addEventListener("click", async (e) => {
    e.preventDefault();
    setErr(verifyCodeErr, "");

    const code = (verifyCodeInput.value || "").trim();

    if (!/^\d{4}$/.test(code)) {
      setErr(verifyCodeErr, `<p class="field-error">⚠️ أدخل رمز مكوّن من 4 أرقام</p>`);
      return;
    }

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
      setErr(verifyCodeErr, `<p class="field-error">${data.error || "⚠️ الرمز غير صحيح"}</p>`);
      return;
    }

    verifiedMobile.value = data.phone || "";
    closeVerifyPopup();

    otpSuccessPopup.classList.remove("hidden");
    setTimeout(() => {
      otpSuccessPopup.classList.add("hidden");
      mobileForm.classList.add("hidden");
      signupForm.classList.remove("hidden");
    }, 2000);
  });

  // STEP 3: basic client validation like mockup (only terms required)
  signupForm?.addEventListener("submit", (e) => {
    const acceptTerms = document.getElementById("acceptTerms");
    const acceptTermsErr = document.getElementById("acceptTermsErr");
    setErr(acceptTermsErr, "");

    if (acceptTerms && !acceptTerms.checked) {
      e.preventDefault();
      setErr(acceptTermsErr, `<p class="field-error">⚠️ يجب الموافقة على الشروط والأحكام</p>`);
    }
  });
});
