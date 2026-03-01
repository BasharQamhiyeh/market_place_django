

/* =========================================================
   ✅ Notifications Data + Render
   ========================================================= */
let notifications = [
  { id: 1, type:"request", status:"pending", title:"طلبك قيد المراجعة", message:"طلب رقم 202 “طلب شراء موبايل سامسونج” قيد المراجعة حالياً.", time:"منذ 10 دقائق", unread:true },
  { id: 2, type:"request", status:"approved", title:"تم قبول طلبك", message:"تم نشر طلب رقم 201 بنجاح وسيظهر للآخرين.", time:"منذ ساعتين", unread:true },
  { id: 3, type:"request", status:"rejected", title:"تم رفض طلبك", message:"طلب رقم 203 مرفوض. السبب: الطلب غير واضح ويحتاج تفاصيل أكثر.", time:"منذ يوم", unread:false },

  { id: 4, type:"ad", status:"pending", title:"إعلانك قيد المراجعة", message:"إعلان رقم 103 “تلفزيون سامسونج 55 بوصة” قيد المراجعة.", time:"منذ 3 ساعات", unread:true },
  { id: 5, type:"ad", status:"approved", title:"تم قبول إعلانك", message:"إعلان رقم 101 “لابتوب HP للبيع” تم قبوله ونشره.", time:"منذ 5 ساعات", unread:false },
  { id: 6, type:"ad", status:"rejected", title:"تم رفض إعلانك", message:"إعلان رقم 104 مرفوض. السبب: الصورة غير واضحة وتخالف معايير الجودة.", time:"منذ يومين", unread:false },
  { id: 7, type:"ad", status:"featured_expired", title:"انتهت مدة تمييز إعلانك", message:"انتهت مدة تمييز الإعلان رقم 101. يمكنك تمييزه مجدداً.", time:"منذ 3 أيام", unread:false },

  { id: 8, type:"wallet", status:"charged", title:"تم شحن النقاط بنجاح", message:"تم إضافة 120 نقطة إلى محفظتك.", time:"منذ 4 أيام", unread:true },
  { id: 9, type:"wallet", status:"used", title:"تم خصم نقاط", message:"تم خصم 30 نقطة مقابل تمييز إعلان رقم 101.", time:"منذ أسبوع", unread:false },
  { id: 10, type:"wallet", status:"reward", title:"مكافأة دعوة صديق", message:"حصلت على +30 نقطة لأن صديقك سجّل عبر رابطك.", time:"منذ أسبوع", unread:false },

// ✅ إشعار وهمي: تمت إضافة إعلانك للمفضلة
  {
    id: 11,
    type: "fav",
    status: "added",
    title: "تم إضافة إعلانك للمفضلة",
    message: "قام أحد المستخدمين بإضافة إعلانك رقم 101 “لابتوب HP للبيع” إلى المفضلة.",
    time: "منذ دقائق",
    unread: true
  },

  { id: 12, type:"system", status:"info", title:"تنبيه من ركن", message:"يرجى تحديث بيانات المتجر لتظهر بشكل احترافي.", time:"منذ أسبوعين", unread:false },
   {
  id: 13,
  type: "store_follow",
  status: "followed",
  title: "تمت متابعة متجرك",
  message: "قام أحد المستخدمين بمتابعة متجرك وسيصله كل جديد من إعلاناتك.",
  time: "منذ دقائق",
  unread: true
},
{
  id: 14,
  type: "store_follow",
  status: "unfollowed",
  title: "تم إلغاء متابعة متجرك",
  message: "قام أحد المستخدمين بإلغاء متابعة متجرك.",
  time: "منذ ساعة",
  unread: true
}

];

function getNotiIcon(n) {

  // 🛒 طلب
  if (n.type === "request") return `
    <svg class="w-6 h-6 text-green-600" viewBox="0 0 24 24" fill="none">
      <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
      <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
      <path d="M3 4h2l2.4 12h10.2l2-8H6"
            stroke="currentColor" stroke-width="2"/>
    </svg>
  `;

  // 📢 إعلان
  if (n.type === "ad") return `
    <svg class="w-6 h-6 text-orange-600" viewBox="0 0 24 24" fill="none">
      <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4a1 1 0 0 0-1 1Z"
            stroke="currentColor" stroke-width="2"/>
      <path d="M14 6v12"
            stroke="currentColor" stroke-width="2"/>
    </svg>
  `;

  // 💰 محفظة
  if (n.type === "wallet") return `
    <svg class="w-6 h-6 text-yellow-600" viewBox="0 0 24 24" fill="none">
      <rect x="2" y="6" width="20" height="14" rx="2"
            stroke="currentColor" stroke-width="2"/>
      <path d="M16 12h4"
            stroke="currentColor" stroke-width="2"/>
    </svg>
  `;

  // ⭐ مفضلة
  if (n.type === "fav") return `
    <svg class="w-6 h-6 text-red-500" viewBox="0 0 24 24" fill="none">
      <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
               stroke="currentColor" stroke-width="2"/>
    </svg>
  `;

// 🏬 متابعة متجر
if (n.type === "store_follow") 
  return `
    <svg class="w-6 h-6 ${n.status === "followed" ? "text-green-600" : "text-gray-500"}"
         viewBox="0 0 24 24"
         fill="none"
         stroke="currentColor"
         stroke-width="2"
         stroke-linecap="round"
         stroke-linejoin="round">
      <path d="M3 9l1-5h16l1 5"/>
      <path d="M5 9v10h14V9"/>
      <path d="M9 19v-6h6v6"/>
      ${
        n.status === "followed"
          ? `<path d="M16 3l2 2 4-4"/>`
          : `<path d="M18 6l4 4M22 6l-4 4"/>`
      }
    </svg>
  `;


  // 🔔 افتراضي
  return `
    <svg class="w-6 h-6 text-gray-500" viewBox="0 0 24 24" fill="none">
      <path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 7h18s-3 0-3-7Z"
            stroke="currentColor" stroke-width="2"/>
    </svg>
  `;
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



function renderNotifications() {
  const container = document.getElementById("notiList");
  const totalEl = document.getElementById("notiTotal");
  const unreadEl = document.getElementById("notiUnread");

  // ✅ صححنا التحقق هنا
  if (!container || !totalEl || !unreadEl) return;

  container.innerHTML = "";

  const total = notifications.length;
  const unread = notifications.filter(n => n.unread).length;

  totalEl.textContent = total;
  unreadEl.textContent = unread;

  // ✨ (اختياري) اخفِ شارة غير المقروء إذا صار 0
  unreadEl.parentElement.style.display = unread === 0 ? "none" : "flex";

  if (!notifications.length) {
    container.innerHTML = `<div class="text-center text-gray-500 py-10">لا يوجد إشعارات حالياً</div>`;
    return;
  }

  notifications.forEach(n => {
    container.innerHTML += `
      <div class="flex items-start gap-3 p-4 border rounded-xl hover:bg-gray-50 transition relative ${n.unread ? "bg-orange-50/40" : ""}">
        ${n.unread ? `<span class="w-3 h-3 bg-orange-500 rounded-full absolute top-3 left-3"></span>` : ""}
        <span>${getNotiIcon(n)}</span>
        <div class="flex-1 space-y-1">
          <div class="flex items-center gap-2 flex-wrap">
            <p class="font-bold text-gray-800">${n.title}</p>
            ${getNotiBadge(n)}
          </div>
          <p class="text-sm text-gray-700">${n.message}</p>
          <p class="text-xs text-gray-500">${n.time}</p>
        </div>
        ${n.unread ? `
          <button onclick="markAsRead(${n.id})"
                  class="text-xs px-3 py-1 rounded-xl border bg-white hover:bg-orange-50 text-gray-700 shrink-0">
            <span class="inline-flex items-center gap-1">
              <svg class="w-4 h-4 text-green-600" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17l-5-5"
                      stroke="currentColor" stroke-width="2"
                      stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              مقروء
            </span>
          </button>
        ` : `
          <span class="text-xs px-3 py-1 rounded-xl border bg-gray-100 text-gray-500 shrink-0">
            مقروء
          </span>
        `}
      </div>`;
  });
}

function markAsRead(id) {
  const noti = notifications.find(n => n.id === id);
  if (!noti) return;

  noti.unread = false;

  renderNotifications();
}

/* =========================================================
   ✅ Global Init
   ========================================================= */
window.addEventListener("load", () => {

  
  renderNotifications();
 
});



