/* static/js/my_account/messages.js
   Fully fixed:
   - Works even if tab HTML is injected later into #tabsViewport
   - Works even if tab buttons are re-rendered
   - Loads conversations ONLY when msgs tab becomes active (or already active on load)
   - Prevents “empty list” when API returns data but container wasn't present yet
*/

let currentChatId = null;
let currentFilter = "all";
let conversations = [];

/* ---------------------------------------------------------
   Helpers
--------------------------------------------------------- */

function getCookie(name){
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if(parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

function fmtTime(str){ return str || ""; }

function $(id){ return document.getElementById(id); }

function isMsgsTabActive(){
  return $("tab-msgs")?.classList.contains("active");
}

/* ---------------------------------------------------------
   Counters + Type line
--------------------------------------------------------- */

function updateCounters(){
  const total = conversations.length;
  const unread = conversations.reduce((sum, c) => sum + (c.unreadCount > 0 ? 1 : 0), 0);

  const totalEl = $("totalMsgs");
  const unreadEl = $("unreadMsgs");
  if(totalEl) totalEl.textContent = total;
  if(unreadEl) unreadEl.textContent = unread;
}

function typeLineHtml(c){
  if(c.type === "ad"){
    return `
      <span style="color:#c2410c; font-weight:900; display:inline-flex; gap:6px; align-items:center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4"
                stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M14 6v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        بخصوص إعلان: ${c.title || ""}
      </span>
    `;
  }
  if(c.type === "request"){
    return `
      <span style="color:#16a34a; font-weight:900; display:inline-flex; gap:6px; align-items:center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
          <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
          <path d="M3 4h2l2.4 12h10.2l2-8H6"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        بخصوص طلب: ${c.title || ""}
      </span>
    `;
  }
  return `
    <span style="color:#2563eb; font-weight:900; display:inline-flex; gap:6px; align-items:center;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M3 9l1-5h16l1 5" stroke="currentColor" stroke-width="2"/>
        <path d="M5 9v10h14V9" stroke="currentColor" stroke-width="2"/>
      </svg>
      تواصل عام مع المتجر
    </span>
  `;
}

/* ---------------------------------------------------------
   Render: Conversations list
--------------------------------------------------------- */

function renderConversations(){
  const container = $("conversationsList");
  if(!container) return;

  const q = ($("chatSearch")?.value || "").trim().toLowerCase();

  const filtered = conversations.filter(c => {
    const matchFilter = currentFilter === "all" || c.type === currentFilter;
    const matchSearch =
      !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.title || "").toLowerCase().includes(q) ||
      (c.lastText || "").toLowerCase().includes(q);

    return matchFilter && matchSearch;
  });

  container.innerHTML = "";

  if(!filtered.length){
    container.innerHTML = `<div style="text-align:center; color:#6b7280; padding:40px 0;">لا توجد محادثات مطابقة 🔍</div>`;
    updateCounters();
    return;
  }

  container.innerHTML = filtered.map(c => {
    const badge = (c.unreadCount > 0)
      ? `<span class="chat-item__badge chat-item__badge--unread">${c.unreadCount} جديد</span>`
      : `<span class="chat-item__badge chat-item__badge--read">مقروء</span>`;

    return `
      <div class="chat-item" data-chat-id="${c.id}">
        <img class="chat-item__avatar" src="${c.img}" alt="">
        <div class="chat-item__body">
          <div class="chat-item__top">
            <div class="chat-item__name">${c.name}</div>
            <div class="chat-item__time">${fmtTime(c.lastTime)}</div>
          </div>
          <div class="chat-item__type">${typeLineHtml(c)}</div>
          <div class="chat-item__last">${c.lastText || "لا توجد رسائل بعد"}</div>
        </div>
        ${badge}
      </div>
    `;
  }).join("");

  // Use event listeners per item (safe, since list is small).
  container.querySelectorAll(".chat-item").forEach(el => {
    el.addEventListener("click", () => openChat(el.dataset.chatId));
  });

  updateCounters();
}

/* ---------------------------------------------------------
   Backend calls
--------------------------------------------------------- */

async function loadConversations(){
  // If tab content was removed from DOM by your tabs system, avoid useless fetch.
  if(!$("conversationsList")) return;

  const res = await fetch(window.MYMSG_ENDPOINTS.conversations, { credentials:"same-origin" });
  const data = await res.json();

  conversations = (data.conversations || []);
  renderConversations();
}

async function loadMessages(chatId){
  const url = window.MYMSG_ENDPOINTS.messages.replace("__ID__", chatId);
  const res = await fetch(url, { credentials:"same-origin" });
  return await res.json();
}

/* ---------------------------------------------------------
   Chat view switching
--------------------------------------------------------- */

function showMsgs(){
  $("tab-chat")?.classList.remove("active");
  $("tab-msgs")?.classList.add("active");

  // When returning, re-render from cached convos (no refetch)
  renderConversations();
}

function showChat(){
  $("tab-msgs")?.classList.remove("active");
  $("tab-chat")?.classList.add("active");
}

/* ---------------------------------------------------------
   Render chat
--------------------------------------------------------- */

function renderChat(messages){
  const area = $("chatArea");
  if(!area) return;

  area.innerHTML = (messages || []).map(m => {
    if(m.from === "them"){
      return `
        <div class="msg-row them">
          <img class="msg-avatar" src="${m.avatar}" alt="">
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
  const c = conversations.find(x => String(x.id) === String(chatId));
  if(!c) return;

  currentChatId = chatId;

  if($("chatUserName")) $("chatUserName").textContent = c.name;
  if($("chatUserImg")) $("chatUserImg").src = c.img;

  const typeEl = $("chatItemType");
  if(typeEl) typeEl.innerHTML = typeLineHtml(c);

  showChat();

  const data = await loadMessages(chatId);
  renderChat(data.messages || []);

  // optimistic mark as read in UI
  c.unreadCount = 0;
  renderConversations();
}

/* ---------------------------------------------------------
   Send message
--------------------------------------------------------- */

async function sendMessage(){
  const input = $("chatInput");
  const text = (input?.value || "").trim();
  if(!text || !currentChatId) return;

  const csrf = getCookie("csrftoken");
  const url = window.MYMSG_ENDPOINTS.send.replace("__ID__", currentChatId);

  const res = await fetch(url, {
    method:"POST",
    credentials:"same-origin",
    headers:{
      "Content-Type":"application/json",
      "X-CSRFToken": csrf || ""
    },
    body: JSON.stringify({ body: text })
  });

  const data = await res.json();
  if(!data.ok) return;

  input.value = "";

  // reload messages + conversations
  await openChat(currentChatId);
  await loadConversations();
}

/* ---------------------------------------------------------
   UI Wiring (robust)
--------------------------------------------------------- */

function wireFiltersOnce(){
  // If filters aren’t in DOM yet, skip.
  const btns = document.querySelectorAll(".chat-filter-btn");
  if(!btns.length) return;

  // Remove old handlers by cloning (simple + safe)
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

/* ---------------------------------------------------------
   Boot / Init logic
   - This is the core fix for "API returns but list empty"
--------------------------------------------------------- */

let msgsBooted = false;

function bootMessagesUI(){
  // DOM must exist
  if(!$("conversationsList")) return false;

  // endpoints must exist
  if(!window.MYMSG_ENDPOINTS?.conversations) return false;

  if(msgsBooted) return true;
  msgsBooted = true;

  // Wire events (safe, elements exist now)
  wireFiltersOnce();

  $("chatSearch")?.addEventListener("input", renderConversations);
  $("chatBackBtn")?.addEventListener("click", showMsgs);
  $("chatSendBtn")?.addEventListener("click", sendMessage);

  $("chatInput")?.addEventListener("keydown", (e) => {
    if(e.key === "Enter"){ e.preventDefault(); sendMessage(); }
  });

  loadConversations();
  return true;
}

// callable from tabs system
window.initMyAccountMessages = function initMyAccountMessages(){
  if(bootMessagesUI()) return;

  // If HTML is injected after click, retry a few frames
  let tries = 0;
  const tick = () => {
    tries++;
    if(bootMessagesUI()) return;
    if(tries < 60) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};

/* ---------------------------------------------------------
   Triggers: when msgs tab is opened/active
--------------------------------------------------------- */

// 1) Delegated click: works even if .tab-btn is re-rendered
document.addEventListener("click", (e) => {
  const btn = e.target.closest('.tab-btn[data-tab="msgs"]');
  if(!btn) return;

  // Wait one frame so your tab system can inject/activate the tab DOM
  requestAnimationFrame(() => {
    window.initMyAccountMessages?.();
  });
});

// 2) If tab already active on load
window.addEventListener("load", () => {
  if(isMsgsTabActive()){
    window.initMyAccountMessages?.();
  }
});

// 3) Optional: if your tabs system toggles active without click (e.g. programmatically)
//    This watches for class changes and boots when #tab-msgs becomes active.
const observer = new MutationObserver(() => {
  if(isMsgsTabActive()){
    window.initMyAccountMessages?.();
  }
});
observer.observe(document.documentElement, { attributes:true, subtree:true, attributeFilter:["class"] });
