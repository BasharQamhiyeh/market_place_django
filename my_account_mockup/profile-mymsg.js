

/* =========================================================
   ✅ Chat
   ========================================================= */
const chatData = {
  c1: [
    { from: 'them', text: 'السلام عليكم، هل الإعلان ما يزال متاح؟', time: '10:45 صباحاً', avatar: 'https://i.pravatar.cc/80' },
    { from: 'me',   text: 'نعم متاح، تفضل أي استفسار؟',             time: '10:46 صباحاً' },
    { from: 'them', text: 'ممكن صور إضافية للابتوب؟',               time: '10:47 صباحاً', avatar: 'https://i.pravatar.cc/80' },
  ],
  c2: [
    { from: 'them', text: 'مرحبا، شفت طلبك بخصوص الموبايل.',       time: '09:10 مساءً', avatar: 'https://i.pravatar.cc/81' },
    { from: 'them', text: 'عندي آيفون مستعمل بحالة ممتازة.',       time: '09:12 مساءً', avatar: 'https://i.pravatar.cc/81' },
    { from: 'me',   text: 'ممتاز، ممكن ترسل التفاصيل والسعر؟',     time: '09:14 مساءً' },
  ],
// 🏪 محادثة عامة مع المتجر
  c_store: [
    {
      from: 'them',
      text: 'مرحباً، حبيت أستفسر عن أوقات عمل المتجر وهل التوصيل متاح لجميع المناطق؟',
      time: '11:05 صباحاً',
      avatar: 'https://i.pravatar.cc/82'
    },
    {
      from: 'me',
      text: 'مرحباً بك 👋 نشكر لك تواصلك معنا. أوقات عمل المتجر من 9:00 صباحاً حتى 9:00 مساءً طوال أيام الأسبوع، وخدمة التوصيل متوفرة لمعظم المناطق ويتم تأكيدها عند إتمام الطلب. يسعدنا خدمتك دائماً 🌸',
      time: '11:07 صباحاً'
    }
  ]
};

let currentChatId = 'c1';

function renderChat(chatId) {
  const area = document.getElementById('chatArea');
  area.innerHTML = '';
  (chatData[chatId] || []).forEach(msg => {
    if (msg.from === 'them') {
      const wrapper = document.createElement('div');
      wrapper.className = 'flex items-start gap-3';
      wrapper.innerHTML = `
        <img src="${msg.avatar || 'https://i.pravatar.cc/80'}" class="w-8 h-8 rounded-full mt-1">
        <div class="p-3 bg-gray-100 rounded-2xl border max-w-[75%]">
          <p class="text-gray-800">${msg.text}</p>
          <span class="text-xs text-gray-500">${msg.time}</span>
        </div>`;
      area.appendChild(wrapper);
    } else {
      const wrapper = document.createElement('div');
      wrapper.className = 'flex justify-end';
      wrapper.innerHTML = `
        <div class="p-3 bg-orange-100 border border-orange-300 rounded-2xl max-w-[75%]">
          <p class="text-gray-800">${msg.text}</p>
          <span class="text-xs text-gray-500 block text-left">${msg.time}</span>
        </div>`;
      area.appendChild(wrapper);
    }
  });
  area.scrollTop = area.scrollHeight;
}

function openMessages() {
  document.getElementById('tab-chat').classList.remove('active');
  document.getElementById('tab-msgs').classList.add('active');
}

function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  chatData[currentChatId] ??= [];
  chatData[currentChatId].push({ from:"me", text, time:"الآن" });

  renderChat(currentChatId);
  renderConversations();
  input.value = '';
}



function markAsRead(id){
  const n = notifications.find(x => x.id === id);
  if (!n) return;
  n.unread = false;
  renderNotifications();
}

/* =========================================================
   ✅ Conversations Data + Render
   ========================================================= */
let conversations = [
  { id:"c1", name:"محمد العلي", type:"ad", title:"لابتوب ديل", img:"https://i.pravatar.cc/80", unreadCount:1 },
  { id:"c2", name:"أحمد خليل", type:"request", title:"طلب شراء موبايل مستعمل", img:"https://i.pravatar.cc/81", unreadCount:0 },
  {
  id: "c_store",
  name: "أحمد خالد",
  type: "store", // 🔥 نوع جديد
  title: "تواصل عام مع المتجر",
  img: "https://i.pravatar.cc/82",
  unreadCount: 1
}

];

let currentFilter = "all";


function updateMessagesCounters() {
  const total = conversations.length;
  const unread = conversations.reduce(
    (sum, c) => sum + (c.unreadCount > 0 ? 1 : 0),
    0
  );

  const totalEl = document.getElementById("totalMsgs");
  const unreadEl = document.getElementById("unreadMsgs");

  if (totalEl) totalEl.innerText = total;
  if (unreadEl) unreadEl.innerText = unread;
}


function getLastMessage(chatId){
  const msgs = chatData[chatId] || [];
  if(!msgs.length) return { text:"لا توجد رسائل بعد", time:"" };
  const last = msgs[msgs.length-1];
  return { text:last.text, time:last.time || "" };
}

function renderConversations(){
  const container = document.getElementById("conversationsList");
  if(!container) return;

  const q = (document.getElementById("chatSearch")?.value || "").trim().toLowerCase();

  let filtered = conversations.filter(c=>{
    const matchFilter = currentFilter === "all" || c.type === currentFilter;
    const matchSearch =
      !q ||
      c.name.toLowerCase().includes(q) ||
      (c.title || "").toLowerCase().includes(q);

    return matchFilter && matchSearch;
  });

  container.innerHTML = "";

  if(!filtered.length){
    container.innerHTML = `<div class="text-center text-gray-500 py-12">لا توجد محادثات مطابقة 🔍</div>`;
    return;
  }

  filtered.forEach(c=>{
    const last = getLastMessage(c.id);
  const typeLine =
  c.type === "ad"
    ? `
      <span class="inline-flex items-center gap-1 text-orange-600 font-semibold">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
          <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4"
                stroke="currentColor" stroke-width="2"/>
        </svg>
        بخصوص إعلان: ${c.title || ""}
      </span>
    `
  : c.type === "request"
    ? `
      <span class="inline-flex items-center gap-1 text-green-600 font-semibold">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
          <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
          <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
          <path d="M3 4h2l2.4 12h10.2l2-8H6"
                stroke="currentColor" stroke-width="2"/>
        </svg>
        بخصوص طلب: ${c.title || ""}
      </span>
    `
    : `
      <span class="inline-flex items-center gap-1 text-blue-600 font-semibold">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
          <path d="M3 9l1-5h16l1 5" stroke="currentColor" stroke-width="2"/>
          <path d="M5 9v10h14V9" stroke="currentColor" stroke-width="2"/>
          <path d="M9 19v-6h6v6" stroke="currentColor" stroke-width="2"/>
        </svg>
        تواصل عام مع المتجر
      </span>
    `;



    container.innerHTML += `
      <div onclick="openChatFromList('${c.id}')"
           class="chat-item"
           data-chat-id="${c.id}">
        <img src="${c.img}" class="w-12 h-12 rounded-full border">

        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <p class="font-bold text-gray-800 truncate">${c.name}</p>
            <span class="text-xs text-gray-400 shrink-0">${last.time}</span>
          </div>

          <p class="text-sm text-orange-600 font-semibold truncate mt-0.5">
            ${typeLine}
          </p>

          <p class="chat-lastline mt-1">
            ${last.text}
          </p>
        </div>

        ${c.unreadCount > 0 ? `
          <span class="inline-flex items-center gap-1 px-2 py-1 bg-orange-500 text-white text-[11px] rounded-full">
  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
    <circle cx="12" cy="12" r="10"/>
  </svg>
  ${c.unreadCount} جديد
</span>

        ` : `
         <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-200 text-gray-700 text-[11px] rounded-full">
  <svg class="w-3 h-3 text-green-600" viewBox="0 0 24 24" fill="none">
    <path d="M20 6L9 17l-5-5"
          stroke="currentColor" stroke-width="2"/>
  </svg>
  مقروء
</span>

        `}
      </div>`;
  });
    updateMessagesCounters();

}

function openChatFromList(chatId){
  const c = conversations.find(x=>x.id===chatId);
  if(!c) return;

  currentChatId = chatId;
  document.getElementById('chatUserName').innerText = c.name;
  document.getElementById('chatUserImg').src = c.img;

  const typeEl = document.getElementById('chatItemType');
  typeEl.innerHTML =
  c.type === "ad"
    ? `
      <span class="inline-flex items-center gap-1">
        <svg class="w-4 h-4 text-orange-600" viewBox="0 0 24 24" fill="none">
          <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4"
                stroke="currentColor" stroke-width="2"/>
        </svg>
        بخصوص إعلان:
        <span class="underline">${c.title || ""}</span>
      </span>
    `
  : c.type === "request"
    ? `
      <span class="inline-flex items-center gap-1">
        <svg class="w-4 h-4 text-green-600" viewBox="0 0 24 24" fill="none">
          <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
          <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
          <path d="M3 4h2l2.4 12h10.2l2-8H6"
                stroke="currentColor" stroke-width="2"/>
        </svg>
        بخصوص طلب:
        <span class="underline">${c.title || ""}</span>
      </span>
    `
    : `
      <span class="inline-flex items-center gap-1 text-blue-600 font-semibold">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none">
          <path d="M3 9l1-5h16l1 5" stroke="currentColor" stroke-width="2"/>
          <path d="M5 9v10h14V9" stroke="currentColor" stroke-width="2"/>
        </svg>
        محادثة عامة مع المتجر
      </span>
    `;


  c.unreadCount = 0;
  renderConversations();

  document.getElementById('tab-msgs').classList.remove('active');
  document.getElementById('tab-chat').classList.add('active');
  renderChat(chatId);
}

document.querySelectorAll(".chat-filter-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    document.querySelectorAll(".chat-filter-btn").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    renderConversations();
  });
});

document.getElementById("chatSearch")?.addEventListener("input", renderConversations);



/* =========================================================
   ✅ Global Init
   ========================================================= */
window.addEventListener("load", () => {

   renderConversations();

});


