/* static/js/my_account/msgs.js
   Screen-swap: clicking a conversation hides the list and shows the full chat panel.
   Back button returns to the list.
   URL updates: ?tab=msgs&c=ID
   Deep-link on page load opens the correct conversation directly.
*/

let currentChatId = null;
let currentFilter  = "all";
let conversations  = [];
let msgsBooted     = false;

function $(id){ return document.getElementById(id); }

function getCookie(name){
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if(parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

function fmtTime(str){ return str || ""; }

function isMsgsTabActive(){
  return $("tab-msgs")?.classList.contains("active");
}

function getDeepLinkConversationId(){
  const raw = $("msgsBoot")?.dataset?.openConversation || "";
  if(!raw) return null;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? String(n) : null;
}

function updateCounters(){
  const total  = conversations.length;
  const unread = conversations.reduce((sum, c) => sum + (c.unreadCount > 0 ? 1 : 0), 0);
  if($("totalMsgs"))  $("totalMsgs").textContent  = total;
  if($("unreadMsgs")) $("unreadMsgs").textContent = unread;
}

function typeLineHtml(c){
  if(c?.type === "ad")
    return `<span style="color:#c2410c;font-weight:900;">بخصوص إعلان: ${c.title || ""}</span>`;
  if(c?.type === "request")
    return `<span style="color:#16a34a;font-weight:900;">بخصوص طلب: ${c.title || ""}</span>`;
  return `<span style="color:#2563eb;font-weight:900;">تواصل عام مع المتجر</span>`;
}

function getConvLastText(c){ return c?.last?.text  || c?.lastText  || ""; }
function getConvLastTime(c){ return c?.last?.time  || c?.lastTime  || ""; }

/* ─── SCREEN TOGGLE ─────────────────────────────────────────────────────── */

function showChatScreen(){
  const list = $("msgsListUI");
  const panel = $("chatPanel");
  if(list)  list.style.display  = "none";
  if(panel) panel.style.display = "flex";
}

function showListScreen(){
  const list = $("msgsListUI");
  const panel = $("chatPanel");
  if(list)  list.style.display  = "";
  if(panel) panel.style.display = "none";
}

/* ─── CONVERSATION LIST ─────────────────────────────────────────────────── */

function renderConversations(){
  const container  = $("conversationsList");
  const emptyState = $("msgsEmpty");
  if(!container) return;

  const q = ($("chatSearch")?.value || "").trim().toLowerCase();

  const filtered = conversations.filter(c => {
    const matchFilter = currentFilter === "all" || c.type === currentFilter;
    const matchSearch =
      !q ||
      (c.name  || "").toLowerCase().includes(q) ||
      (c.title || "").toLowerCase().includes(q) ||
      (getConvLastText(c)).toLowerCase().includes(q);
    return matchFilter && matchSearch;
  });

  container.innerHTML = "";

  if(!filtered.length){
    container.style.display = "none";
    if(emptyState){ emptyState.classList.remove("hidden"); emptyState.style.display = "flex"; }
    updateCounters();
    return;
  }

  if(emptyState){ emptyState.classList.add("hidden"); emptyState.style.display = "none"; }
  container.style.display = "flex";

  filtered.forEach(c => {
    const badge = (c.unreadCount > 0)
      ? `<span class="chat-item__badge chat-item__badge--unread">${c.unreadCount} جديد</span>`
      : `<span class="chat-item__badge chat-item__badge--read">مقروء</span>`;

    const imgUrl     = (c.img || "").trim();
    const avatarHtml = imgUrl ? `<img class="chat-item__avatar" src="${imgUrl}" alt="">` : "";

    const el = document.createElement("div");
    el.className      = "chat-item";
    el.dataset.chatId = String(c.id);
    el.style.cursor   = "pointer";
    el.innerHTML      = `
      ${avatarHtml}
      <div class="chat-item__body">
        <div class="chat-item__top">
          <div class="chat-item__name">${c.name || "مستخدم"}</div>
          <div class="chat-item__time">${fmtTime(getConvLastTime(c))}</div>
        </div>
        <div class="chat-item__type">${typeLineHtml(c)}</div>
        <div class="chat-item__last">${getConvLastText(c) || "لا يوجد رسائل"}</div>
      </div>
      ${badge}
    `;
    container.appendChild(el);
  });

  updateCounters();
}

async function loadConversations(){
  const res  = await fetch(window.MYMSG_ENDPOINTS.conversations, { credentials:"same-origin" });
  const data = await res.json().catch(() => ({}));
  conversations = data.conversations || [];
  renderConversations();
}

/* ─── CHAT PANEL ─────────────────────────────────────────────────────────── */

function renderChat(messages){
  const area = $("chatArea");
  if(!area) return;

  area.innerHTML = (messages || []).map(m => {
    if(m.from === "them"){
      const avatar     = (m.avatar || "").trim();
      const avatarHtml = avatar ? `<img class="msg-avatar" src="${avatar}" alt="">` : "";
      return `
        <div class="msg-row them">
          ${avatarHtml}
          <div class="msg-bubble">
            <p class="msg-text">${m.text}</p>
            <span class="msg-time">${fmtTime(m.time)}</span>
          </div>
        </div>`;
    }
    return `
      <div class="msg-row me">
        <div class="msg-bubble">
          <p class="msg-text">${m.text}</p>
          <span class="msg-time">${fmtTime(m.time)}</span>
        </div>
      </div>`;
  }).join("");

  area.scrollTop = area.scrollHeight;
}

async function loadMessages(chatId){
  const url = window.MYMSG_ENDPOINTS.messages.replace("__ID__", chatId);
  const res  = await fetch(url, { credentials:"same-origin" });
  const data = await res.json().catch(() => ({}));
  return { res, data };
}

async function openChat(chatId){
  const strId = String(chatId);
  currentChatId = strId;

  // Populate header
  const c = conversations.find(x => String(x.id) === strId) || null;
  if($("chatUserName")) $("chatUserName").textContent = c?.name || "مستخدم";
  if($("chatItemType")) $("chatItemType").innerHTML   = c ? typeLineHtml(c) : "";
  if($("chatUserImg")){
    const img = (c?.img || "").trim();
    if(img) $("chatUserImg").src = img;
    else    $("chatUserImg").removeAttribute("src");
  }

  // Show loading state then switch to chat screen
  const area = $("chatArea");
  if(area) area.innerHTML = `<div class="chat-area__loading">جارٍ التحميل…</div>`;

  showChatScreen();
  window.scrollTo({ top: 0, behavior: "smooth" });
  pushUrl(strId);

  // Load messages
  const { res, data } = await loadMessages(strId);

  if(!res.ok){
    if(area) area.innerHTML = `<div class="chat-area__error">فشل تحميل المحادثة (${res.status})</div>`;
    return;
  }

  const msgs = data.messages || [];
  if(!Array.isArray(msgs) || msgs.length === 0){
    if(area) area.innerHTML = `<div class="chat-area__empty">لا توجد رسائل بعد</div>`;
  } else {
    renderChat(msgs);
  }

  if(c){
    const prevUnread = c.unreadCount || 0;
    c.unreadCount = 0;
    renderConversations();
    if(prevUnread > 0) _decrementNavbarBadge(prevUnread);
  }
}

function _decrementNavbarBadge(decrease){
  const badge = document.querySelector(".msg-badge");
  if(!badge) return;
  const next = Math.max(0, (parseInt(badge.textContent, 10) || 0) - decrease);
  if(next === 0){
    badge.textContent = "";
    badge.classList.add("hidden");
    document.querySelector(".msg-icon")?.classList.remove("filled");
  } else {
    badge.textContent = String(next);
  }
}

function pushUrl(chatId){
  const url = new URL(window.location.href);
  url.searchParams.set("tab", "msgs");
  if(chatId) url.searchParams.set("c", chatId);
  else        url.searchParams.delete("c");
  window.history.replaceState({}, "", url.toString());
}

/* ─── SEND ───────────────────────────────────────────────────────────────── */

async function sendMessage(){
  const input = $("chatInput");
  const body  = (input?.value || "").trim();
  if(!currentChatId || !body) return;

  const url  = window.MYMSG_ENDPOINTS.send.replace("__ID__", currentChatId);
  const csrf = getCookie("csrftoken");

  const res  = await fetch(url, {
    method:"POST",
    credentials:"same-origin",
    headers:{
      "Content-Type":"application/json",
      "X-CSRFToken": csrf || "",
      "X-Requested-With":"XMLHttpRequest",
    },
    body: JSON.stringify({ body })
  });

  const data = await res.json().catch(() => ({}));

  if(!res.ok || !data.ok){
    const area = $("chatArea");
    const msg =
      data.error === "invalid" ? "ممنوع الروابط أو HTML" :
      data.error === "empty"   ? "الرسالة فارغة"         :
                                 "فشل إرسال الرسالة";
    area?.insertAdjacentHTML("beforeend",
      `<div style="padding:12px;text-align:center;color:#ef4444;">${msg}</div>`);
    if(area) area.scrollTop = area.scrollHeight;
    return;
  }

  input.value = "";
  await openChat(currentChatId);   // reload messages
  await loadConversations();       // refresh last-message preview
}

/* ─── RESET (returning to list) ─────────────────────────────────────────── */

function resetMsgsViewToList(){
  currentChatId = null;
  showListScreen();
}

/* ─── FILTERS / SEARCH ──────────────────────────────────────────────────── */

function wireFiltersOnce(){
  const btns = document.querySelectorAll(".chat-filter-btn");
  if(!btns.length) return;

  // Replace to strip old listeners
  btns.forEach(btn => {
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
  });

  document.querySelectorAll(".chat-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chat-filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter || "all";
      renderConversations();
    });
  });
}

/* ─── BOOT ───────────────────────────────────────────────────────────────── */

function bootMessagesUI(){
  if(!$("conversationsList"))                return false;
  if(!window.MYMSG_ENDPOINTS?.conversations) return false;

  if(msgsBooted){
    // Returning to the tab: always go back to list view
    resetMsgsViewToList();
    pushUrl(null);
    return true;
  }

  msgsBooted = true;
  wireFiltersOnce();

  $("chatSearch")?.addEventListener("input", renderConversations);

  // Back button: return to the conversations list
  $("chatBackBtn")?.addEventListener("click", () => {
    resetMsgsViewToList();
    pushUrl(null);
  });

  $("chatSendBtn")?.addEventListener("click", sendMessage);
  $("chatInput")?.addEventListener("keydown", e => {
    if(e.key === "Enter"){ e.preventDefault(); sendMessage(); }
  });

  loadConversations().then(() => {
    const deepId = getDeepLinkConversationId();
    if(deepId) openChat(deepId);
    else       resetMsgsViewToList();
  });

  return true;
}

window.initMyAccountMessages = function(){
  if(bootMessagesUI()) return;
  let tries = 0;
  const tick = () => {
    tries++;
    if(bootMessagesUI()) return;
    if(tries < 60) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};

/* ─── GLOBAL LISTENERS ──────────────────────────────────────────────────── */

// Tab open
document.addEventListener("click", e => {
  const btn = e.target.closest('.tab-btn[data-tab="msgs"]');
  if(!btn) return;
  requestAnimationFrame(() => window.initMyAccountMessages?.());
});

// Delegated click on conversation item
document.addEventListener("click", e => {
  const item = e.target.closest("#conversationsList .chat-item");
  if(!item) return;
  const chatId = item.dataset.chatId;
  if(chatId) openChat(chatId);
}, true);

// Page-load deep-link
window.addEventListener("load", () => {
  const params = new URLSearchParams(window.location.search);
  if(params.get("tab") === "msgs"){
    document.querySelector('.tab-btn[data-tab="msgs"]')?.click();
  }
  if(isMsgsTabActive()) window.initMyAccountMessages?.();
});
