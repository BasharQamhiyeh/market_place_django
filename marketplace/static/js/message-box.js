/* =========================
   Message form (AJAX - no redirect)
========================= */

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

(function initMessageForm() {
  const form = document.getElementById("messageForm");
  const text = document.getElementById("messageText");
  const err = document.getElementById("messageError");

  if (!form || !text) return;

  form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const body = text.value.trim();
      console.log(text);

    if (!body) {
    console.log("Here_Body");
      err?.classList.remove("hidden");
      text.classList.add("border-red-500");
      return;
    }

    err?.classList.add("hidden");
    text.classList.remove("border-red-500");

    try {
    console.log("Here2");
      const res = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: new FormData(form),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.ok) {
        if (data.error === "invalid") {
          showRuknAlert("❌ ممنوع الروابط أو HTML داخل الرسالة");
          return;
        }
        if (data.error === "self_message") {
          showRuknAlert("❌ لا يمكنك مراسلة نفسك");
          return;
        }
        if (data.error === "empty") {
          showRuknAlert("⚠️ اكتب رسالتك أولاً");
          return;
        }
        showRuknAlert("❌ لم يتم إرسال الرسالة");
        return;
      }

      // ✅ success: stay on page + toast
      showRuknAlert("✔ تم إرسال رسالتك للمعلن");
      text.value = "";

      // close accordion if exists
      document.getElementById("messageBox")?.classList.add("hidden");
      document.getElementById("messageChevron")?.classList.remove("rotate-180");

    } catch (err) {
      console.error(err);
      showRuknAlert("❌ حدث خطأ غير متوقع");
    }
  });
})();
