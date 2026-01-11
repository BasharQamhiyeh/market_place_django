function calcDaysLeft(expireDateStr) {
  if (!expireDateStr) return 0;
  const today = new Date(); today.setHours(0,0,0,0);
  const end = new Date(expireDateStr.replaceAll("/", "-")); end.setHours(0,0,0,0);
  const diff = end - today;
  const days = Math.ceil(diff / 86400000);
  return days > 0 ? days : 0;
}

function getRequestHighlightButton(req) {
  if (req.status !== "active") {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed">⭐ تمييز</button>`;
  }
  const daysLeft = req.featuredExpiresAt ? calcDaysLeft(req.featuredExpiresAt) : 0;
  if (req.featured && daysLeft > 0) {
    return `<button class="px-4 py-2 pill-orange text-sm opacity-40 cursor-not-allowed">⭐ تمييز</button>`;
  }
  return `<button class="px-4 py-2 pill-orange text-sm" onclick="openHighlightModal?.('request', ${req.id})">⭐ تمييز</button>`;
}

function generateRequestCard(req) {
  const rowColor =
    req.status === "active"   ? "bg-white border border-gray-200" :
    req.status === "pending"  ? "bg-yellow-50 border border-yellow-300" :
    req.status === "rejected" ? "bg-red-50 border border-red-300" : "bg-white border border-gray-200";

  const statusLabel =
    req.status === "active"   ? `<span class="status-badge status-active">🟢 مفعّل</span>` :
    req.status === "pending"  ? `<span class="status-badge status-pending">🟡 قيد المراجعة</span>` :
    req.status === "rejected" ? `<span class="status-badge status-rejected">🔴 مرفوض</span>` : "";

  let featureBadge = "";
  if (req.featured) {
    const daysLeft = req.featuredExpiresAt ? calcDaysLeft(req.featuredExpiresAt) : 0;
    featureBadge = daysLeft > 0
      ? `<span class="feature-badge flex items-center gap-1">⭐ مميز — متبقّي: ${daysLeft} يوم</span>`
      : `<span class="feature-badge">⭐ مميز</span>`;
  }

  const disableAll = (req.status === "pending") ? "opacity-40 pointer-events-none" : "";
  const disableRepublish = (req.status !== "active") ? "opacity-40 pointer-events-none" : "";

  return `
    <div class="request-row flex flex-col md:flex-row items-start md:items-center gap-5 p-4 rounded-2xl shadow-sm ${rowColor}">
      <div class="flex-1 min-w-0">
        <div class="flex flex-wrap items-center gap-2 mb-2">
          <span class="px-2 py-1 rounded-lg bg-gray-100 border text-xs text-gray-600 font-bold">
            ${req.category || "ركن الطلبات"}
          </span>
          ${featureBadge}
        </div>

        <div class="flex flex-wrap items-center gap-3 mb-2">
          <span class="flex items-center gap-1 text-gray-700 font-bold">
            🆔 رقم الطلب: <span class="text-orange-600">${req.id}</span>
          </span>
          ${statusLabel}
        </div>

        <div class="flex flex-wrap items-center gap-3 mb-2">
          <h3 class="font-bold text-lg text-gray-800">${req.title || ""}</h3>
          <span class="text-orange-600 font-extrabold text-xl leading-none">
            💰 الميزانية: ${req.budget ?? 0} د.أ
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 mt-1 mb-2">
          <span>📍 ${req.city || "—"}</span>
          <span>📅 ${req.date || "—"}</span>
          <span>🔎 الحالة المطلوبة: ${req.condition || "—"}</span>
          <span>👁️ ${req.views ?? 0} مشاهدة</span>
        </div>

        ${req.status === "rejected" && req.rejectReason
          ? `<p class="text-sm text-red-700 mt-2">❗ سبب الرفض: <b>${req.rejectReason}</b></p>`
          : ""
        }
      </div>

      <div class="flex flex-col gap-2 w-full md:w-auto">
        <a href="${req.editUrl || '#'}" class="px-4 py-2 pill-blue text-sm ${disableAll} text-center">✏️ تعديل</a>
        <button type="button" class="px-4 py-2 pill-red text-sm ${disableAll}" onclick="myAccountDeleteRequest?.(${req.id})">❌ حذف</button>
        <button type="button" class="px-4 py-2 pill-green text-sm ${disableRepublish}" onclick="myAccountRepublishRequest?.(${req.id})">🔄 إعادة نشر</button>
        ${getRequestHighlightButton(req)}
      </div>
    </div>`;
}

function renderMyRequests() {
  const container = document.getElementById("requestsList");
  const countEl = document.getElementById("requestsCount");
  if (!container || !countEl) return;

  const requests = JSON.parse(document.getElementById("myRequestsData")?.textContent || "[]");
  container.innerHTML = "";
  requests.forEach(r => { container.innerHTML += generateRequestCard(r); });
  countEl.textContent = requests.length;

  if (!requests.length) {
    container.innerHTML = `<div class="text-center text-gray-500 py-10">لا يوجد طلبات حالياً</div>`;
  }
}

window.addEventListener("load", renderMyRequests);
