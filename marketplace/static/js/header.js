// ===== Dropdowns للهيدر =====
const menus = {
  fav : {btn: document.getElementById('favBtn'),  menu: document.getElementById('favMenu')},
  msg : {btn: document.getElementById('msgBtn'),  menu: document.getElementById('msgMenu')},
  noti: {btn: document.getElementById('notiBtn'), menu: document.getElementById('notiMenu')},
  user: {btn: document.getElementById('userBtn'), menu: document.getElementById('userMenu')}
};

function closeAll(except){
  Object.keys(menus).forEach(k=>{
    if(k!==except){
      menus[k].menu.classList.remove('show');
      menus[k].btn.setAttribute('aria-expanded','false');
    }
  });
}

Object.keys(menus).forEach(key=>{
  const {btn,menu} = menus[key];
  if (!btn || !menu) return;
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains('show');
    closeAll(key);
    if (!isOpen) {
      menu.classList.add('show');
      btn.setAttribute('aria-expanded', 'true');
    } else {
      menu.classList.remove('show');
      btn.setAttribute('aria-expanded', 'false');
    }
  });
});

document.addEventListener('click', (e) => {
    // 👇 do NOT close if clicking inside search
    if (e.target.closest('#searchWrapper')) return;

    closeAll(null);
});

document.addEventListener('keydown',e=>{
  if(e.key==='Escape') closeAll(null);
});

// ===================== LOGIN SCRIPT =====================
const loginBtn    = document.getElementById("loginBtn");
const authButtons = document.getElementById("authButtons");
const userIcons   = document.getElementById("userIcons");
const loginModal  = document.getElementById("loginModal");
const closeLoginX = document.getElementById("closeLoginX");
const loginForm   = document.getElementById("loginForm");

// فتح نافذة تسجيل الدخول
if (loginBtn && loginModal) {
  loginBtn.addEventListener("click", () => {
    loginModal.classList.remove("hidden");
  });
}

// إغلاق النافذة
if (closeLoginX && loginModal) {
  closeLoginX.addEventListener("click", () => {
    loginModal.classList.add("hidden");
  });
}

// تسجيل الدخول (محاكاة)
if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (loginModal) loginModal.classList.add("hidden");
    if (authButtons) authButtons.classList.add("hidden");
    if (userIcons)   userIcons.classList.remove("hidden");
  });
}

// ===== Toggle Buy / Sell =====
document.addEventListener('DOMContentLoaded', () => {
  const sellBtn     = document.getElementById('sellBtn');
  const buyBtn      = document.getElementById('buyBtn');
  const searchInput = document.getElementById('searchInput');
  const searchBtn   = document.getElementById('searchBtn');
  const addAdBtn    = document.getElementById('addAdBtn');
  const intentBox   = document.getElementById('intentBox');

  // لو الهيدر هذا غير موجود في الصفحة، نخرج بهدوء
  if (!sellBtn || !buyBtn || !searchInput || !searchBtn || !addAdBtn || !intentBox) {
    return;
  }

  let isBuy = false;  // default = إعلان

  function refreshSearchUI() {
      const color = isBuy ? '#16a34a' : 'var(--rukn-orange)';

      // نص خانة البحث
      searchInput.placeholder = isBuy
          ? "ابحث عن طلب"
          : "ابحث عن إعلان";

      // أزرار إعلان / طلب
      sellBtn.style.backgroundColor = isBuy ? '#fff' : 'var(--rukn-orange)';
      sellBtn.style.color           = isBuy ? '#6b7280' : '#fff';

      buyBtn.style.backgroundColor  = isBuy ? '#16a34a' : '#fff';
      buyBtn.style.color            = isBuy ? '#fff' : '#6b7280';

      intentBox.style.borderColor   = color;

      // زر أضف إعلانك / أضف طلبك
      addAdBtn.textContent           = isBuy ? "أضف طلبك" : "أضف إعلانك";
      addAdBtn.style.backgroundColor = color;

      // بوردر حقل البحث + زر البحث
      searchInput.style.borderColor   = color;
      searchBtn.style.backgroundColor = color;

      // تفعيل زر البحث فقط عند وجود نص
      const hasText = searchInput.value.trim() !== "";
      searchBtn.disabled = !hasText;
      searchBtn.style.opacity = hasText ? "1" : "0.5";
  }

  sellBtn.addEventListener("click", () => { isBuy = false; refreshSearchUI(); });
  buyBtn.addEventListener("click", () => { isBuy = true;  refreshSearchUI(); });
  searchInput.addEventListener("input", refreshSearchUI);

  // أول تحميل
  refreshSearchUI();

  // لو حبيت تناديها من سكربت ثاني
  window.refreshSearchUI = refreshSearchUI;
});


