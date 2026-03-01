



/* =========================================================
   ✅ Wallet / Points
   ========================================================= */
let points = 80;
let transactions = [
  { type: 'use',    text: '⭐ تمييز إعلان “لابتوب HP”',     amount: -50 },
  { type: 'reward', text: '🎁 مكافأة دعوة صديق جديد',       amount: +30 },
  { type: 'buy',    text: '💳 شراء نقاط — باقة 100 نقطة',   amount: +100 }
];

function updateBalance() {
  const el = document.getElementById("pointsBalance");
  if (!el) return;
  el.innerHTML = points + ' 🔥';
}


function renderTransactions() {
  const container = document.getElementById("pointsLog");
   if (!container) return;
  container.innerHTML = "";
  if (!transactions.length) return;

  const groups = {};
  transactions.forEach(t => {
    const date = t.date || new Date().toISOString().split("T")[0];
    groups[date] ??= [];
    groups[date].push(t);
  });

  const sortedDates = Object.keys(groups).sort((a, b) => new Date(b) - new Date(a));
  const today = new Date().toISOString().split("T")[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

  sortedDates.forEach(date => {
    const dateLabel = document.createElement("div");
    dateLabel.className = "timeline-date";
    dateLabel.innerText =
      date === today ? "اليوم" :
      date === yesterday ? "الأمس" :
      date.replace(/-/g, "/");
    container.appendChild(dateLabel);

    groups[date].forEach(t => {
      const row = document.createElement("div");
      row.className = "timeline-item";
      row.innerHTML = `
        <span>${t.text}</span>
        <span class="font-bold ${t.amount > 0 ? 'text-green-600' : 'text-red-600'}">
          ${t.amount > 0 ? '+' : ''}${t.amount} نقطة
        </span>`;
      container.appendChild(row);
    });
  });
}

function buyPoints(amount) {
  points += amount;
  transactions.unshift({
    type: "buy",
    text: `💳 شراء نقاط — باقة ${amount} نقطة`,
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


document.getElementById("deleteAdModal").addEventListener("click", e => {
  if (e.target.id === "deleteAdModal") closeDeleteModal();
});

["republishConfirmModal"].forEach(id => {
  const m = document.getElementById(id);
  m.addEventListener("click", e => {
    if (e.target === m) closeRepublishConfirmModal();
  });
});

document.getElementById("highlightModal").addEventListener("click", e => {
  if (e.target.id === "highlightModal") closeHighlightModal();
});


/* =========================================================
   ✅ Ads / Requests Data
   ========================================================= */
let ads = [
  {
    id: 101,
    title: "لابتوب HP للبيع",
    price: 320,
    city: "عمّان",
    date: "2025/02/10",
    views: 124,
	favCount: 7,
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900",
    featured: false,
    featuredExpiresAt: null,
    status: "active",
    category: "ركن الإلكترونيات",
    lastRepublishAt: null
  },
  {
    id: 102,
    title: "طقم كنب",
    price: 550,
    city: "الزرقاء",
    date: "2025/01/19",
    views: 98,
	favCount: 5,
    image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=900",
    featured: false,
    status: "active",
    category: "ركن الأثاث",
    lastRepublishAt: null
  },
  {
    id: 103,
    title: "تلفزيون سامسونج 55 بوصة",
    price: 260,
    city: "إربد",
    date: "2025/01/10",
    views: 0,
    image: "https://images.unsplash.com/photo-1512499617640-c2f999098c21?w=900",
    featured: false,
    status: "pending",
    category: "ركن الأجهزة المنزلية",
    favCount: 0,
    lastRepublishAt: null
  },
  
  {
    id: 104,
    title: "تلفزيون ال جي 32 بوصة",
    price: 160,
    city: "إربد",
    date: "2025/02/10",
    views: 0,
    image: "https://images.unsplash.com/photo-1512499617640-c2f999098c21?w=900",
    featured: false,
    status: "pending",
    category: "ركن الأجهزة المنزلية",
    favCount: 0,
    lastRepublishAt: null
  },
  
  {
    id: 105,
    title: "طقم كورنر 7 قطع",
    price: 800,
    city: "عمان",
    date: "2025/01/19",
    views: 250,
	favCount: 15,
    image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=900",
    featured: false,
    status: "active",
    category: "ركن الأثاث",
    lastRepublishAt: null
  },
  
  {
    id: 106,
    title: "كاميرا كانون احترافية",
    price: 850,
    city: "عمّان",
    date: "2025/01/05",
    views: 0,
    image: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=900",
    featured: false,
    status: "rejected",
    category: "ركن الكاميرات",
    rejectReason: "الصورة غير واضحة وتخالف معايير الجودة",
    favCount: 0,
    lastRepublishAt: null
  }
];


/* =========================================================
   ✅ Helpers
   ========================================================= */
function calcDaysLeft(expireDate) {
  const today = new Date();
  const end = new Date(expireDate);
  today.setHours(0,0,0,0);
  end.setHours(0,0,0,0);
  const diff = end - today;
  const days = Math.ceil(diff / (1000*60*60*24));
  return days > 0 ? days : 0;
}

function updateFeaturedDays() {
  ads.forEach(ad => {
    if (ad.featured && ad.featuredExpiresAt) {
      ad.featuredDays = calcDaysLeft(ad.featuredExpiresAt);
    }
  });
}

// ✅ republish cooldown helpers
function daysBetween(dateStr) {
  if(!dateStr) return 9999;
  const a = new Date(dateStr); a.setHours(0,0,0,0);
  const b = new Date(); b.setHours(0,0,0,0);
  return Math.floor((b - a) / 86400000);
}
function canRepublishWithCost(obj){
  const days = daysBetween(obj.lastRepublishAt);
  if (days >= 7) return { ok:true, cost:0, daysLeft:0 };
  return { ok:false, cost:20, daysLeft:7 - days };
}

/* =========================================================
   ✅ Highlight Modal (Ads + Requests)
   ========================================================= */
let pendingHighlight = { days: null, cost: null };

let highlightTarget = { type: null, id: null };

function openHighlightModal(type, id) {
  highlightTarget = { type, id };

  let title = "";
  if (type === "ad") {
    const ad = ads.find(a => a.id === id);
    title = ad ? ad.title : "";
  } else {
    const req = requests.find(r => r.id === id);
    title = req ? req.title : "";
  }

  highlightTarget.title = title;

  document.getElementById("highlightPointsBalance").innerText = points;
  document.getElementById("highlightModalTitle").innerText =
    type === "ad" ? "⭐ تمييز الإعلان" : "⭐ تمييز الطلب";

  const m = document.getElementById("highlightModal");
  m.classList.remove("hidden");
  m.classList.add("flex");
}


function closeHighlightModal() {
  const m = document.getElementById("highlightModal");
  m.classList.add("hidden");
  m.classList.remove("flex");
}

function selectHighlightPackage(days, cost) {
  if (points < cost) {
    closeHighlightModal();
    showNoPointsModal();
    return;
  }

  pendingHighlight = { days, cost };

 document.getElementById("highlightConfirmText").innerHTML = `
  <div class="text-center space-y-2">
    <div class="font-bold text-gray-800">
      ${highlightTarget.type === "ad" ? "📢 الإعلان:" : "📦 الطلب:"}
    </div>
    <div class="text-orange-600 font-extrabold">
      ${highlightTarget.title}
    </div>
    <div class="text-gray-700 mt-2">
      سيتم خصم <b>${cost}</b> نقطة مقابل تمييز لمدة <b>${days}</b> أيام
    </div>
  </div>
`;


  openHighlightConfirmModal();
}

function openHighlightConfirmModal() {
  const m = document.getElementById("highlightConfirmModal");
  m.classList.remove("hidden");
  m.classList.add("flex");

  document.getElementById("confirmHighlightBtn").onclick = confirmHighlightNow;
}

function closeHighlightConfirmModal() {
  const m = document.getElementById("highlightConfirmModal");
  m.classList.add("hidden");
  m.classList.remove("flex");
  pendingHighlight = { days: null, cost: null };
}

function confirmHighlightNow() {
  const { days, cost } = pendingHighlight;
  if (!days || !cost) return;

  let targetObj = null;
  if (highlightTarget.type === "ad") {
    targetObj = ads.find(a => a.id === highlightTarget.id);
  } else {
    targetObj = requests.find(r => r.id === highlightTarget.id);
  }
  if (!targetObj) return;

  points -= cost;
  updateBalance();

  transactions.unshift({
    type: "use",
    text:
      highlightTarget.type === "ad"
        ? `⭐ تمييز إعلان رقم ${highlightTarget.id} لمدة ${days} يوم`
        : `⭐ تمييز طلب رقم ${highlightTarget.id} لمدة ${days} يوم`,
    amount: -cost,
    date: new Date().toISOString().split("T")[0]
  });
  renderTransactions();

  const expire = new Date();
  expire.setDate(expire.getDate() + days);

  targetObj.featured = true;
  targetObj.featuredExpiresAt = expire.toISOString().split("T")[0];

  if (highlightTarget.type === "ad") generateAds();

  closeHighlightConfirmModal();
  closeHighlightModal();

  openSuccessModal("تم التمييز بنجاح ⭐", "تم التمييز");
}

/* =========================================================
   ✅ Request Highlight Button (Smart)
   ========================================================= */
function getRequestHighlightButton(req) {
  if (req.status !== "active") {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed"><span class="inline-flex items-center gap-1">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
           stroke="currentColor" stroke-width="2"/>
</svg>
</span>تمييز</button>`;
  }

  let daysLeft = 0;
  if (req.featured && req.featuredExpiresAt) {
    daysLeft = calcDaysLeft(req.featuredExpiresAt);
  }

  if (req.featured && daysLeft > 0) {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed">⭐ تمييز</button>`;
  }

  return `
    <button onclick="openHighlightModal('request', ${req.id})"
            class="px-4 py-2 pill-orange text-sm">
      <span class="inline-flex items-center gap-1">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
           stroke="currentColor" stroke-width="2"/>
</svg>
</span> تمييز
    </button>`;
}

function addAd() { openSuccessModal("تم فتح صفحة إضافة إعلان جديد ✅", "➕ إضافة إعلان"); }
function addRequest() { openSuccessModal("تم فتح صفحة إضافة طلب جديد ✅", "➕ إضافة طلب"); }


/* =========================================================
   ✅ Ads UI
   ========================================================= */
function getHighlightButton(ad) {
  if (ad.status !== "active") {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed"><span class="inline-flex items-center gap-1">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
           stroke="currentColor" stroke-width="2"/>
</svg>
</span> تمييز</button>`;
  }

  let daysLeft = 0;
  if (ad.featured && ad.featuredExpiresAt) daysLeft = calcDaysLeft(ad.featuredExpiresAt);

  if (ad.featured && daysLeft > 0) {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed"><span class="inline-flex items-center gap-1">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
           stroke="currentColor" stroke-width="2"/>
</svg>
</span> تمييز</button>`;
  }

  return `
    <button onclick="openHighlightModal('ad', ${ad.id})"
            class="px-4 py-2 pill-orange text-sm">
			
			<span class="inline-flex items-center gap-1">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
           stroke="currentColor" stroke-width="2"/>
</svg>
</span>
تمييز
    </button>`;
}

function generateAdCard(ad) {
  const rowColor =
    ad.status === "active"   ? "bg-white border border-gray-200" :
    ad.status === "pending"  ? "bg-yellow-50 border border-yellow-300" :
    ad.status === "rejected" ? "bg-red-50 border border-red-300" : "";

  const statusLabel =
    ad.status === "active"   ? `<span class="status-badge status-active">
	<span class="inline-flex items-center gap-1">
	<svg class="w-3 h-3 text-green-600" viewBox="0 0 24 24" fill="currentColor">
  <circle cx="12" cy="12" r="10"/>
</svg>
</span>
 مفعّل</span>` :
    ad.status === "pending"  ? `<span class="status-badge status-pending">
	
	<span class="inline-flex items-center gap-1">
	<svg class="w-3 h-3 text-yellow-600" viewBox="0 0 24 24" fill="currentColor">
  <circle cx="12" cy="12" r="10"/>
</svg>
</span>
 قيد المراجعة</span>` :
    ad.status === "rejected" ? `<span class="status-badge status-rejected">
	
	<span class="inline-flex items-center gap-1">
	<svg class="w-3 h-3 text-red-600" viewBox="0 0 24 24" fill="currentColor">
  <circle cx="12" cy="12" r="10"/>
</svg>
</span>
 مرفوض</span>` : "";

  let featureBadge = "";
  if (ad.featured) {
    if (ad.featuredExpiresAt) {
      const daysLeft = calcDaysLeft(ad.featuredExpiresAt);
      if (daysLeft > 0) {
        featureBadge = `<span class="feature-badge flex items-center gap-1">⭐ مميز — متبقّي: ${daysLeft} يوم</span>`;
      } else {
        featureBadge = `<span class="feature-badge">⭐ مميز</span>`;
      }
    } else {
      featureBadge = `<span class="feature-badge">⭐ مميز</span>`;
    }
  }

  let disabledEditDelete = '';
  let disabledRepublishFeature = '';

  if (ad.status === 'pending') {
    disabledEditDelete = 'opacity-40 pointer-events-none';
    disabledRepublishFeature = 'opacity-40 pointer-events-none';
  }
  if (ad.status === 'rejected') {
    disabledRepublishFeature = 'opacity-40 pointer-events-none';
  }

  return `
    <div class="ad-row flex flex-col md:flex-row items-center md:items-center gap-5 p-4 rounded-2xl shadow-sm ${rowColor}">

      <div class="relative w-full md:w-auto flex justify-center">
        <span class="absolute top-2 right-2 bg-white text-orange-600 text-xs px-2 py-1 rounded-lg border-2 border-orange-500 font-bold shadow-sm">
          ${ad.category || "بدون قسم"}
        </span>
        <img src="${ad.image}"
             class="w-full max-w-[420px] mx-auto h-52 sm:h-56 md:w-56 md:h-44 rounded-xl object-cover border">
      </div>

      <div class="flex-1 text-center md:text-right">

        <div class="ad-header flex flex-wrap gap-3 mb-2 justify-center md:justify-start">
          <span class="flex items-center gap-1 text-gray-700 font-bold">
		  
		  <svg class="w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none">
  <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
  <path d="M7 8h10M7 12h10M7 16h6" stroke="currentColor" stroke-width="2"/>
</svg>
رقم الإعلان:

           <span class="text-orange-600">${ad.id}</span>
          </span>
          ${statusLabel}
          ${featureBadge}
        </div>

        <div class="flex flex-col md:flex-row items-center gap-2 md:gap-3 mb-2 justify-center md:justify-start">
          <h3 class="font-bold text-lg text-gray-800">${ad.title}</h3>
		  
          <span class="text-orange-600 font-extrabold text-2xl leading-none">${ad.price} د.أ</span>
        </div>

        <div class="flex flex-wrap gap-4 text-sm text-gray-500 mt-1 mb-2 justify-center md:justify-start">
		<span class="inline-flex items-center gap-1">
  <!-- SVG هنا -->
  <svg class="w-4 h-4 text-orange-500" viewBox="0 0 24 24" fill="none">
  <path d="M12 21s7-7 7-11a7 7 0 1 0-14 0c0 4 7 11 7 11Z"
        stroke="currentColor" stroke-width="2"/>
  <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2"/>
</svg> 
  <span>${ad.city}</span>
</span>

		
          
		  <span class="inline-flex items-center gap-1">
		  <svg class="w-4 h-4 text-orange-500" viewBox="0 0 24 24" fill="none">
  <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
  <path d="M8 2v4M16 2v4M3 10h18" stroke="currentColor" stroke-width="2"/>
</svg>

          <span>${ad.date}</span>
		  </span>
		  
		   <span class="inline-flex items-center gap-1">
		  <svg class="w-4 h-4 text-orange-500" viewBox="0 0 24 24" fill="none">
  <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z"
        stroke="currentColor" stroke-width="2"/>
  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
</svg>

          <span>${ad.views} مشاهدة</span>
		    </span>
		  
		   <span class="inline-flex items-center gap-1">
		  <svg class="w-4 h-4 text-red-500" viewBox="0 0 24 24" fill="none">
  <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z"
        stroke="currentColor" stroke-width="2"/>
</svg>

		  <span>${ad.favCount ?? 0} مفضلة</span>
           </span>
        </div>

        ${ad.status === "rejected" ? `
<p class="text-sm text-red-700 mt-2 flex items-center gap-1 justify-center md:justify-start text-center md:text-right">
  <svg class="w-4 h-4 text-red-600 flex-shrink-0"
       viewBox="0 0 24 24"
       fill="none"
       aria-hidden="true">
    <circle cx="12" cy="12" r="10"
            stroke="currentColor"
            stroke-width="2"/>
    <path d="M12 7v6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"/>
    <circle cx="12" cy="16" r="1"
            fill="currentColor"/>
  </svg>

  <span>
    سبب الرفض:
    <b class="font-semibold">${ad.rejectReason}</b>
  </span>
</p>` : ""}

      </div>

      <div class="flex flex-col gap-2 w-full md:w-auto">
	  
        <button onclick="editAd(${ad.id})" class="px-4 py-2 pill-blue text-sm ${disabledEditDelete}">
		 <span class="inline-flex items-center gap-1">
		<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4 11.5-11.5Z"
        stroke="currentColor" stroke-width="2"/>
</svg>
</span>
تعديل</button>


        <button onclick="deleteAd(${ad.id})" class="px-4 py-2 pill-red text-sm ${disabledEditDelete}">
		 <span class="inline-flex items-center gap-1">
		<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <path d="M3 6h18M8 6v14h8V6M10 10v6M14 10v6"
        stroke="currentColor" stroke-width="2"/>
</svg>
</span>
حذف</button>


        <button onclick="republishAd(${ad.id})" class="px-4 py-2 pill-green text-sm ${disabledRepublishFeature}">
		 <span class="inline-flex items-center gap-1">
		<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
  <path d="M21 12a9 9 0 1 1-3-6.7" stroke="currentColor" stroke-width="2"/>
  <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2"/>
</svg>
</span>
إعادة نشر</button>

                ${getHighlightButton(ad)}
      </div>
    </div>`;
}

function generateAds() {
  const container = document.getElementById("adsList");
  const countEl = document.getElementById("adsCount");
  container.innerHTML = "";
  ads.forEach(ad => container.innerHTML += generateAdCard(ad));
  countEl.textContent = ads.length;
}

function editAd(id) { openSuccessModal("تم فتح صفحة تعديل الإعلان رقم " + id); }

let adToDelete = null;
function deleteAd(id) {
  adToDelete = id;
  document.getElementById("deleteTitle").textContent = "حذف إعلان";
  document.getElementById("deleteSubtitle").textContent = "يرجى اختيار سبب حذف الإعلان";
  document.getElementById("confirmDeleteBtn").textContent = "حذف الإعلان";

  setDeleteReasons("ad");
  openDeleteModal();
}

function doRepublishAd(id, free=true){
  const ad = ads.find(a => a.id === id);
  if (!ad) return;

  const today = new Date();
  const formatted = `${today.getFullYear()}/${String(today.getMonth()+1).padStart(2,"0")}/${String(today.getDate()).padStart(2,"0")}`;
  ad.date = formatted;
  ad.status = "active";
  ad.lastRepublishAt = today.toISOString().split("T")[0];

  generateAds();

  if(free){
    openSuccessModal("تم إعادة نشر الإعلان مجاناً ✅", "🔄 تم إعادة النشر");
  }
}

function republishAd(id) {
  const ad = ads.find(a => a.id === id);
  if (!ad) return;

  const check = canRepublishWithCost(ad);

  // ✅ مجاني بعد 7 أيام
  if(check.ok){
    doRepublishAd(id, true);
    return;
  }

  // ✅ قبل 7 أيام = نعرض مودال تأكيد
  openRepublishConfirmModal("ad", id, check.cost);
}


/* =========================================================
   ✅ Delete Modal (dynamic reasons)
   ========================================================= */
function setDeleteReasons(type){
  const select = document.getElementById("deleteReason");
  select.innerHTML = "";

  let reasons = [];
  if(type === "ad"){
    reasons = [
      { value:"sold_in", label:"تم البيع خلال منصة ركن" },
      { value:"sold_out", label:"تم البيع خارج منصة ركن" },
      { value:"republish", label:"أريد إعادة نشره لاحقاً" },
      { value:"issue", label:"مشكلة في الإعلان" },
      { value:"other", label:"سبب آخر…" }
    ];
  } else {
    reasons = [
      { value:"found", label:"تم العثور على المطلوب" },
      { value:"not_needed", label:"لم أعد بحاجة للطلب" },
      { value:"update", label:"أريد تعديل الطلب ونشره مجدداً" },
      { value:"issue", label:"مشكلة في الطلب" },
      { value:"other", label:"سبب آخر…" }
    ];
  }

  select.innerHTML = `<option value="">— اختر سبب الحذف —</option>` +
    reasons.map(r=>`<option value="${r.value}">${r.label}</option>`).join("");
}

function openDeleteModal(){
  const m = document.getElementById("deleteAdModal");
  m.classList.remove("hidden"); m.classList.add("flex");
}
function closeDeleteModal() {
  const m = document.getElementById("deleteAdModal");
  m.classList.add("hidden"); m.classList.remove("flex");

  document.getElementById("deleteReason").value = "";
  const otherBox = document.getElementById("deleteReasonOther");
  otherBox.classList.add("hidden"); otherBox.value = "";
  document.getElementById("deleteReasonError").classList.add("hidden");

  adToDelete = null;
  requestToDelete = null;
}
const deleteReasonEl = document.getElementById("deleteReason");
if (deleteReasonEl) {
  deleteReasonEl.addEventListener("change", function () {
    document.getElementById("deleteReasonError").classList.add("hidden");

    const otherBox = document.getElementById("deleteReasonOther");
    otherBox.classList.remove("border-red-500");

    if (this.value === "other") otherBox.classList.remove("hidden");
    else { otherBox.classList.add("hidden"); otherBox.value = ""; }
  });
}

function confirmDeleteAd() {
  const reasonSelect = document.getElementById("deleteReason");
  const reason = reasonSelect.value;
  const other  = document.getElementById("deleteReasonOther").value.trim();

  if (!reason) {
    document.getElementById("deleteReasonError").classList.remove("hidden");
    return;
  }

  const finalReason =
    reason === "other" && other.length
      ? other
      : reasonSelect.options[reasonSelect.selectedIndex].text;

  if (adToDelete !== null) {
    ads = ads.filter(a => a.id !== adToDelete);
    generateAds();
    openSuccessModal(`تم حذف الإعلان — السبب: ${finalReason}`, "✔️ تم الحذف");
    adToDelete = null;
  }

  if (requestToDelete !== null) {
    requests = requests.filter(r => r.id !== requestToDelete);
    generateRequests();
    openSuccessModal(`تم حذف الطلب — السبب: ${finalReason}`, "✔️ تم الحذف");
    requestToDelete = null;
  }

  closeDeleteModal();
}


/* =========================================================
   ✅ No Points Modal
   ========================================================= */
function showNoPointsModal() {
  const m = document.getElementById("noPointsModal");
  m.classList.remove("hidden"); m.classList.add("flex");
}
function closeNoPointsModal() {
  const m = document.getElementById("noPointsModal");
  m.classList.add("hidden"); m.classList.remove("flex");
}
function openWalletTab() {
  closeNoPointsModal();
  document.querySelector("[data-tab='wallet']").click();
}


function getNotiBadge(n) {

  const dot = (color) => `
    <svg class="w-3 h-3 ${color}" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="10"/>
    </svg>
  `;

  if (n.status === "pending")
    return `<span class="status-badge status-pending flex items-center gap-1">
      ${dot("text-yellow-500")} قيد المراجعة
    </span>`;

  if (n.status === "approved")
    return `<span class="status-badge status-active flex items-center gap-1">
      ${dot("text-green-500")} مقبول
    </span>`;

  if (n.status === "rejected")
    return `<span class="status-badge status-rejected flex items-center gap-1">
      ${dot("text-red-500")} مرفوض
    </span>`;

  if (n.status === "charged")
    return `<span class="status-badge status-active">شحن</span>`;

  if (n.status === "used")
    return `<span class="status-badge status-rejected">خصم</span>`;

  if (n.status === "reward")
    return `<span class="status-badge status-active">مكافأة</span>`;

  if (n.status === "featured_expired")
    return `<span class="status-badge" style="background:#ffedd5;color:#c2410c;">
      انتهى التمييز
    </span>`;

  if (n.type === "fav")
    return `<span class="status-badge" style="background:#ffedd5;color:#c2410c;">
      مفضلة
    </span>`;
	
	if (n.type === "store_follow" && n.status === "followed") 
  return `
    <span class="status-badge status-active">
      متابعة
    </span>
  `;


if (n.type === "store_follow" && n.status === "unfollowed") {
  return `
    <span class="status-badge"
          style="background:#f3f4f6;color:#6b7280;">
      إلغاء متابعة
    </span>
  `;
}


  return "";
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
  transactions.unshift({
    type: "use",
    text:
      republishPending.type === "ad"
        ? `🔄 إعادة نشر إعلان رقم ${republishPending.id} قبل انتهاء 7 أيام`
        : `🔄 إعادة نشر طلب رقم ${republishPending.id} قبل انتهاء 7 أيام`,
    amount: -cost,
    date: new Date().toISOString().split("T")[0]
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

  

  updateFeaturedDays();
  generateAds();
  

  updateBalance();
  renderTransactions();

  

  setDeleteReasons("ad");
});

