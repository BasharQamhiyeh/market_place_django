

  // إغلاق المودل
  function closeBuyModal() {
    const modal = document.getElementById("buyPointsModal");
    const notice = document.getElementById("buyNotice");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    if (notice) notice.classList.add("hidden");
  }

  // (اختياري) فتح المودل
  function openBuyModal() {
    const modal = document.getElementById("buyPointsModal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  }

  // تعطيل الشراء: فقط إظهار رسالة جميلة
  function buyPointsDisabled(points) {
    const notice = document.getElementById("buyNotice");
    if (!notice) return;

    // إظهار الرسالة مع سكرول بسيط للمكان لو كان المستخدم نازل
    notice.classList.remove("hidden");
    notice.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }



/* =========================================================
   ✅ Wallet / Points
   ========================================================= */
let points = 40;

let transactions = [

  // 🎁 مكافأة تسجيل
  {
    type: "reward",
    text: "مكافأة تسجيل حساب",
    amount: +20,
    date: daysAgo(7)
  },

  // 🎁 مكافأة دعوة
  {
    type: "reward",
    text: "مكافأة دعوة صديق",
    amount: +10,
    date: daysAgo(5)
  },

  // 💳 شراء نقاط
  {
    type: "buy",
    text: "شراء نقاط — باقة 120 نقطة",
    amount: +120,
    date: daysAgo(3)
  },

  // ⭐ تمييز إعلان
  {
    type: "use",
    amount: -30,
    date: daysAgo(2),
    meta: {
      action: "highlight",
      targetType: "ad",
      id: 101,
      title: "لابتوب HP",
      days: 3
    }
  },

  // ⭐ تمييز طلب
  {
    type: "use",
    amount: -60,
    date: daysAgo(1),
    meta: {
      action: "highlight",
      targetType: "request",
      id: 201,
      title: "شراء آيفون",
      days: 7
    }
  },

  // 🔄 إعادة نشر إعلان
  {
    type: "use",
    amount: -20,
    date: daysAgo(0),
    meta: {
      action: "republish",
      targetType: "ad",
      id: 254,
      title: "لابتوب HP"
    }
  }

];

function formatTxText(t){
  if(!t.meta) return t.text || "";

  const m = t.meta;
  const title = m.title ? `«${m.title}»` : "";

  if(m.action === "highlight"){
    return `تمييز ${m.targetType === "ad" ? "إعلان" : "طلب"}
    رقم ${m.id} — ${title} لمدة ${m.days} أيام`;
  }

  if(m.action === "republish"){
    return `إعادة نشر ${m.targetType === "ad" ? "إعلان" : "طلب"}
    رقم ${m.id} — ${title}`;
  }

  return t.text || "";
}



function daysAgo(n){
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function getTxIcon(type, meta){

  /* 🎁 مكافأة */
  if (type === "reward") {
    return `
      <svg class="w-5 h-5 text-red-600" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="8" width="18" height="13" rx="2"
              stroke="currentColor" stroke-width="2"/>
        <path d="M12 8V3M7 5h10"
              stroke="currentColor" stroke-width="2"/>
        <path d="M3 13h18"
              stroke="currentColor" stroke-width="2"/>
      </svg>
    `;
  }

  /* 🔄 إعادة نشر */
  if (meta?.action === "republish") {
    const color =
      meta.targetType === "ad"
        ? "text-orange-600"
        : "text-green-600";

    return `
      <svg class="w-5 h-5 ${color}" viewBox="0 0 24 24" fill="none">
        <path d="M21 12a9 9 0 1 1-3-6.7"
              stroke="currentColor" stroke-width="2"/>
        <path d="M21 3v6h-6"
              stroke="currentColor" stroke-width="2"/>
      </svg>
    `;
  }

  /* 📢 إعلان */
  if (meta?.targetType === "ad") return `
    <svg class="w-5 h-5 text-orange-600" viewBox="0 0 24 24" fill="none">
      <path d="M12 2l3 6 7 1-5 4 1 7-6-3-6 3 1-7-5-4 7-1z"
            stroke="currentColor" stroke-width="2"/>
    </svg>`;

  /* 🛒 طلب */
  if (meta?.targetType === "request") return `
    <svg class="w-5 h-5 text-green-600" viewBox="0 0 24 24" fill="none">
      <path d="M12 2l3 6 7 1-5 4 1 7-6-3-6 3 1-7-5-4 7-1z"
            stroke="currentColor" stroke-width="2"/>
    </svg>`;

  /* 💳 افتراضي (شراء مثلاً) */
  return `
    <svg class="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="none">
      <rect x="3" y="7" width="18" height="10"
            stroke="currentColor" stroke-width="2"/>
    </svg>`;
}



function getTxBadge(type){
  if(type === "buy")
    return `<span class="status-badge pill-blue">شراء</span>`;
  if(type === "reward")
    return `<span class="status-badge pill-green">مكافأة</span>`;
  return `<span class="status-badge pill-red">خصم</span>`;
}


function updateBalance() {
  document.getElementById("pointsBalance").textContent = points;
}


function addTransaction({
  type,        // buy | use | reward
  text,       // نص واضح للعملية
  amount,      // + أو -
  meta = {}    // بيانات إضافية (id، مدة، نوع...)
}) {
  transactions.unshift({
    type,
    text,
    amount,
    meta,
    date: new Date().toISOString().split("T")[0]
  });

  renderTransactions();
}


function renderTransactions() {
  const container = document.getElementById("pointsLog");
  container.innerHTML = "";

  const groups = {};
  transactions.forEach(t => {
    groups[t.date] ??= [];
    groups[t.date].push(t);
  });

  Object.keys(groups)
    .sort((a,b)=> new Date(b)-new Date(a))
    .forEach(date => {

      const title = document.createElement("div");
      title.className = "timeline-date";
      title.innerText =
        date === daysAgo(0) ? "اليوم" :
        date === daysAgo(1) ? "الأمس" :
        date.replace(/-/g,"/");
      container.appendChild(title);

      groups[date].forEach(t => {
        const row = document.createElement("div");
        row.className = "timeline-item items-center gap-3 justify-between";


        row.innerHTML = `
          <div class="flex items-center gap-3">
  ${getTxIcon(t.type, t.meta)}

  <div>
    <div class="flex flex-wrap items-center gap-2">
      <span class="font-semibold text-gray-800">
        ${formatTxText(t)}
      </span>
      ${getTxBadge(t.type)}
    </div>
  </div>
</div>

<div class="font-extrabold text-left
  ${t.amount > 0 ? 'text-green-600' : 'text-red-600'}">
  ${t.amount > 0 ? '+' : ''}${t.amount} نقطة
</div>

        `;
        container.appendChild(row);
      });
    });
}

function buyPoints(amount) {
  points += amount;
  transactions.unshift({
    type: "buy",
    text: `شراء نقاط — باقة ${amount} نقطة`,
    amount: +amount,
    date: new Date().toISOString().split("T")[0]
  });
  updateBalance();
  renderTransactions();
  closeBuyModal();
  openSuccessModal("تم شحن " + amount + " نقطة بنجاح!", "تم شحن النقاط بنجاح");
}

function openBuyModal() {
  const m = document.getElementById('buyPointsModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeBuyModal() {
  const m = document.getElementById('buyPointsModal');
  m.classList.add('hidden'); m.classList.remove('flex');
}

function openInvitePage() {
  document.getElementById('invitePage').classList.remove('hidden');
  generateQR();
}
function closeInvitePage() {
  document.getElementById('invitePage').classList.add('hidden');
}
function generateQR() {
  const link = document.getElementById("refLink").innerText;
  document.getElementById("qrCode").innerHTML = "";
  new QRCode(document.getElementById("qrCode"), {
    text: link, width: 150, height: 150,
    colorDark: "#000000", colorLight: "#ffffff",
    correctLevel: QRCode.CorrectLevel.H
  });
}

function safeCopy(text){
  if(navigator.clipboard && window.isSecureContext){
    return navigator.clipboard.writeText(text);
  }
  const t = document.createElement("textarea");
  t.value = text; t.style.position = "fixed"; t.style.left = "-9999px";
  document.body.appendChild(t); t.focus(); t.select();
  document.execCommand("copy"); t.remove();
  return Promise.resolve();
}

function copyRefLink() {
  const link = document.getElementById('refLink').innerText;
  safeCopy(link);
  openSuccessModal("تم نسخ رابط الدعوة بنجاح!", "تم النسخ");
}

function shareRefLink() {
  const link = document.getElementById("refLink").innerText;
  if (navigator.share) {
    try {
      navigator.share({ title:"دعوة ركن", text:"سجل واحصل على نقاط مجانية!", url:link });
    } catch(e){
      safeCopy(link);
      openSuccessModal("تم نسخ الرابط لأن المشاركة لم تعمل على جهازك.", "تم النسخ");
    }
  } else {
    safeCopy(link);
    openSuccessModal("تم نسخ الرابط — خاصية المشاركة غير مدعومة.", "تم النسخ");
  }
}

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
   ✅ Republish Confirm Modal (before 7 days)
   ========================================================= */
let republishPending = { type: null, id: null };

function openRepublishConfirmModal(type, id, cost){
  republishPending = { type, id };

  document.getElementById("republishPointsBalance").innerText = points;

  const btn = document.getElementById("confirmRepublishBtn");
  btn.onclick = () => confirmRepublishNow(cost);

  const m = document.getElementById("republishConfirmModal");
  m.classList.remove("hidden");
  m.classList.add("flex");
}

function closeRepublishConfirmModal(){
  const m = document.getElementById("republishConfirmModal");
  m.classList.add("hidden");
  m.classList.remove("flex");
  republishPending = { type:null, id:null };
}

function confirmRepublishNow(cost){
  if(points < cost){
    closeRepublishConfirmModal();
    showNoPointsModal();
    return;
  }

  points -= cost;
  updateBalance();

  // سجّل العملية في النقاط
  // هات العنوان الحقيقي
let title = "";
if (republishPending.type === "ad") {
  title = (ads.find(a => a.id === republishPending.id)?.title) || "";
} else {
  title = (requests.find(r => r.id === republishPending.id)?.title) || "";
}

transactions.unshift({
  type: "use",
  amount: -cost,
  date: new Date().toISOString().split("T")[0],
  meta: {
    action: "republish",
    targetType: republishPending.type,  // "ad" أو "request"
    id: republishPending.id,
    title
  }
});


  renderTransactions();

  // نفّذ إعادة النشر فعلياً
  if(republishPending.type === "ad") doRepublishAd(republishPending.id, false);
  if(republishPending.type === "request") doRepublishRequest(republishPending.id, false);

  closeRepublishConfirmModal();

  openSuccessModal(
    `تمت إعادة النشر مقابل ${cost} نقطة ✅`,
    "🔄 تم إعادة النشر"
  );
}



/* =========================================================
   ✅ Global Init
   ========================================================= */
window.addEventListener("load", () => {
  

  

  updateBalance();
  renderTransactions();

 

  
});


