/* static/js/my_account/msgs.js
   - Uses your EXISTING views.py APIs:
     conversations: api_my_conversations
     messages: api_conversation_messages
     send: api_conversation_send  (expects JSON key "body")
   - No avatar fallback requests (avoid 404)
   - No duplicate showChat()
   - Delegated click always works
   ✅ When returning to msgs tab, show list (not last opened chat)
   ✅ Shows proper empty state with icon
*/

let currentChatId = null;
let currentFilter = "all";
let conversations = [];
let msgsBooted = false;

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
  const total = conversations.length;
  const unread = conversations.reduce((sum, c) => sum + (c.unreadCount > 0 ? 1 : 0), 0);
  if($("totalMsgs")) $("totalMsgs").textContent = total;
  if($("unreadMsgs")) $("unreadMsgs").textContent = unread;
}

function typeLineHtml(c){
  if(c?.type === "ad"){
    return `<span style="color:#c2410c; font-weight:900;">بخصوص إعلان: ${c.title || ""}</span>`;
  }
  if(c?.type === "request"){
    return `<span style="color:#16a34a; font-weight:900;">بخصوص طلب: ${c.title || ""}</span>`;
  }
  return `<span style="color:#2563eb; font-weight:900;">تواصل عام مع المتجر</span>`;
}

function getConvLastText(c){ return (c?.last?.text || c?.lastText || ""); }
function getConvLastTime(c){ return (c?.last?.time || c?.lastTime || ""); }

function renderConversations(){
  const container = $("conversationsList");
  const emptyState = $("msgsEmpty");

  if(!container) return;

  const q = ($("chatSearch")?.value || "").trim().toLowerCase();

  const filtered = conversations.filter(c => {
    const matchFilter = currentFilter === "all" || c.type === currentFilter;
    const matchSearch =
      !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.title || "").toLowerCase().includes(q) ||
      (getConvLastText(c) || "").toLowerCase().includes(q);
    return matchFilter && matchSearch;
  });

  container.innerHTML = "";

  if(!filtered.length){
    // Show empty state, hide list
    if(container) container.style.display = "none";
    if(emptyState){
      emptyState.classList.remove("hidden");
      emptyState.style.display = "flex";
    }
    updateCounters();
    return;
  }

  // Hide empty state, show list
  if(emptyState){
    emptyState.classList.add("hidden");
    emptyState.style.display = "none";
  }
  if(container) container.style.display = "flex";

  container.innerHTML = filtered.map(c => {
    const badge = (c.unreadCount > 0)
      ? `<span class="chat-item__badge chat-item__badge--unread">${c.unreadCount} جديد</span>`
      : `<span class="chat-item__badge chat-item__badge--read">مقروء</span>`;

    const imgUrl = (c.img || "").trim();
    const avatarHtml = imgUrl ? `<img class="chat-item__avatar" src="${imgUrl}" alt="">` : "";

    return `
      <div class="chat-item" data-chat-id="${c.id}" style="cursor:pointer;">
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
      </div>
    `;
  }).join("");

  updateCounters();
}

async function loadConversations(){
  const res = await fetch(window.MYMSG_ENDPOINTS.conversations, { credentials:"same-origin" });
  const data = await res.json().catch(() => ({}));
  conversations = (data.conversations || []);
  renderConversations();
}

async function loadMessages(chatId){
  const url = window.MYMSG_ENDPOINTS.messages.replace("__ID__", chatId);

  console.log("[msgs] loading messages:", url);
  const res = await fetch(url, { credentials:"same-origin" });
  console.log("[msgs] messages status:", res.status);

  const data = await res.json().catch(() => ({}));
  console.log("[msgs] messages payload keys:", Object.keys(data || {}));

  return { res, data };
}

function showMsgs(){
  const panel = $("chatPanel");
  const list = $("conversationsList");
  if(panel){
    panel.hidden = true;
    panel.setAttribute("hidden", "hidden");
    panel.style.display = "none";
  }
  if(list) list.style.display = "block";
}

function showChat(){
  const panel = $("chatPanel");
  const list = $("conversationsList");
  const emptyState = $("msgsEmpty");

  if(list) list.style.display = "none";
  if(emptyState){
    emptyState.classList.add("hidden");
    emptyState.style.display = "none";
  }
  if(panel){
    panel.hidden = false;
    panel.removeAttribute("hidden");
    panel.style.display = "block";
  }
}

/* ✅ NEW: reset UI when user comes back to msgs tab */
function resetMsgsViewToList(){
  currentChatId = null;

  // clear header UI (optional but avoids showing stale name/type)
  if($("chatUserName")) $("chatUserName").textContent = "";
  if($("chatItemType")) $("chatItemType").innerHTML = "";
  if($("chatUserImg")) $("chatUserImg").removeAttribute("src");

  showMsgs();
}

function renderChat(messages){
  const area = $("chatArea");
  if(!area) return;

  area.innerHTML = (messages || []).map(m => {
    if(m.from === "them"){
      const avatar = (m.avatar || "").trim();
      const avatarHtml = avatar ? `<img class="msg-avatar" src="${avatar}" alt="">` : "";
      return `
        <div class="msg-row them">
          ${avatarHtml}
          <div class="msg-bubble">
            <p class="msg-text">${m.text}</p>
            <span class="msg-time">${fmtTime(m.time)}</span>
          </div>
        </div>
      `;
    }
    return `
      <div class="msg-row me">
        <div class="msg-bubble">
          <p class="msg-text">${m.text}</p>
          <span class="msg-time">${fmtTime(m.time)}</span>
        </div>
      </div>
    `;
  }).join("");

  area.scrollTop = area.scrollHeight;
}

async function openChat(chatId){
  currentChatId = String(chatId);

  const c = conversations.find(x => String(x.id) === String(chatId)) || null;
  if($("chatUserName")) $("chatUserName").textContent = c?.name || "مستخدم";
  if($("chatItemType")) $("chatItemType").innerHTML = c ? typeLineHtml(c) : "";

  if($("chatUserImg")){
    const img = (c?.img || "").trim();
    if(img) $("chatUserImg").src = img;
    else $("chatUserImg").removeAttribute("src");
  }

  showChat();

  const { res, data } = await loadMessages(chatId);

  if(!res.ok){
    const area = $("chatArea");
    if(area){
      area.innerHTML = `<div style="padding:24px;text-align:center;color:#ef4444;">فشل تحميل المحادثة (${res.status})</div>`;
    }
    return;
  }

  const msgs = data.messages || [];
  if(!Array.isArray(msgs) || msgs.length === 0){
    const area = $("chatArea");
    if(area){
      area.innerHTML = `<div style="padding:24px;text-align:center;color:#6b7280;">لا توجد رسائل بعد</div>`;
    }
  } else {
    renderChat(msgs);
  }

  if(c){
    c.unreadCount = 0;
    renderConversations();
  }

  const url = new URL(window.location.href);
  url.searchParams.set("tab", "msgs");
  url.searchParams.set("c", String(chatId));
  window.history.replaceState({}, "", url.toString());
}

async function sendMessage(){
  const input = $("chatInput");
  const body = (input?.value || "").trim();
  if(!currentChatId || !body) return;

  const url = window.MYMSG_ENDPOINTS.send.replace("__ID__", currentChatId);
  const csrf = getCookie("csrftoken");

  console.log("[msgs] sending:", url);

  const res = await fetch(url, {
    method:"POST",
    credentials:"same-origin",
    headers:{
      "Content-Type":"application/json",
      "X-CSRFToken": csrf || "",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify({ body })
  });

  const data = await res.json().catch(() => ({}));
  console.log("[msgs] send status:", res.status, data);

  if(!res.ok || !data.ok){
    const area = $("chatArea");
    const msg =
      data.error === "invalid" ? "ممنوع الروابط أو HTML" :
      data.error === "empty" ? "الرسالة فارغة" :
      "فشل إرسال الرسالة";
    if(area){
      area.insertAdjacentHTML("beforeend", `<div style="padding:12px;text-align:center;color:#ef4444;">${msg}</div>`);
      area.scrollTop = area.scrollHeight;
    }
    return;
  }

  input.value = "";
  await openChat(currentChatId);
  await loadConversations();
}

function wireFiltersOnce(){
  const btns = document.querySelectorAll(".chat-filter-btn");
  if(!btns.length) return;

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

function bootMessagesUI(){
  if(!$("conversationsList")) return false;
  if(!window.MYMSG_ENDPOINTS?.conversations) return false;

  // ✅ If already booted, don't rewire handlers,
  // but DO reset view when returning to msgs tab (unless deep-link exists)
  if(msgsBooted){
    const deepId = getDeepLinkConversationId();
    if(deepId) openChat(deepId);
    else resetMsgsViewToList();
    return true;
  }

  msgsBooted = true;

  wireFiltersOnce();

  $("chatSearch")?.addEventListener("input", renderConversations);
  $("chatBackBtn")?.addEventListener("click", () => {
    resetMsgsViewToList();
    // NOTE: we do NOT change URL params here; tabs.js already clears them on leaving msgs
  });
  $("chatSendBtn")?.addEventListener("click", sendMessage);

  $("chatInput")?.addEventListener("keydown", (e) => {
    if(e.key === "Enter"){ e.preventDefault(); sendMessage(); }
  });

  loadConversations().then(() => {
    const deepId = getDeepLinkConversationId();
    if(deepId) openChat(deepId);
    else resetMsgsViewToList();
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

// tab open trigger
document.addEventListener("click", (e) => {
  const btn = e.target.closest('.tab-btn[data-tab="msgs"]');
  if(!btn) return;
  requestAnimationFrame(() => window.initMyAccountMessages?.());
});

// delegated click on conversation
document.addEventListener("click", (e) => {
  const item = e.target.closest("#tab-msgs .chat-item");
  if(!item) return;

  const chatId = item.dataset.chatId;
  if(!chatId) return;

  console.log("[msgs] clicked conversation:", chatId);
  openChat(chatId);
}, true);

window.addEventListener("load", () => {
  const params = new URLSearchParams(window.location.search);
  if(params.get("tab") === "msgs"){
    document.querySelector('.tab-btn[data-tab="msgs"]')?.click();
  }
  if(isMsgsTabActive()){
    window.initMyAccountMessages?.();
  }
});