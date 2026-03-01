let pendingRemoveFavId = null;
let pendingFavBtn = null;


/* =========================================================
   ✅ Favorites
   ========================================================= */
let favoritesAds = [
    { id: 1, title: "تويوتا كورولا 2018", city: "عمّان", timeLabel: "منذ 3 س", hoursAgo: 3, price: 1000, priceLabel: "1000 د.أ", seller: "محمد علي", sellerType: "individual", condition: "used", featured: true, hasImage: true, category: "cars", categoryLabel: "🚗 ركن السيارات", avatar: "https://randomuser.me/api/portraits/men/32.jpg", img: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop" },
            { id: 2, title: "لابتوب لمحترفين مستعمل بحالة ممتازة جداً", city: "إربد", timeLabel: "منذ يوم", hoursAgo: 24, price: 3355, priceLabel: "3,355 د.أ", seller: "سارة الكيلاني", sellerType: "individual", condition: "used", featured: false, hasImage: true, category: "electronics", categoryLabel: "💻 ركن الإلكترونيات", avatar: "https://randomuser.me/api/portraits/women/44.jpg", img: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1200&auto=format&fit=crop" },
            { id: 3, title: "كرسي مودرن أنيق لغرفة المعيشة", city: "الزرقاء", timeLabel: "منذ يومين", hoursAgo: 48, price: 80, priceLabel: "80 د.أ", seller: "أحمد الزعبي", sellerType: "individual", condition: "used", featured: false, hasImage: true, category: "furniture", categoryLabel: "🪑 ركن الأثاث", avatar: "https://randomuser.me/api/portraits/men/18.jpg", img: "https://images.unsplash.com/photo-1493666438817-866a91353ca9?q=80&w=1200&auto=format&fit=crop" },
            { id: 4, title: "ثلاجة بحالة ممتازة 16 قدم", city: "عمّان", timeLabel: "منذ 4 أيام", hoursAgo: 96, price: 220, priceLabel: "220 د.أ", seller: "ليلى منصور", sellerType: "store", condition: "used", featured: false, hasImage: true, category: "appliances", categoryLabel: "🧊 ركن الأجهزة المنزلية", avatar: "https://randomuser.me/api/portraits/women/55.jpg", img: "https://images.unsplash.com/photo-1582582494702-6a8a0aa98b58?q=80&w=1200&auto=format&fit=crop" },
            { id: 5, title: "هاتف آيفون 13 برو 256GB", city: "إربد", timeLabel: "منذ 5 ساعات", hoursAgo: 5, price: 600, priceLabel: "600 د.أ", seller: "رامي الخطيب", sellerType: "store", condition: "used", featured: true, hasImage: true, category: "electronics", categoryLabel: "💻 ركن الإلكترونيات", avatar: "https://randomuser.me/api/portraits/men/47.jpg", img: "https://images.unsplash.com/photo-1631443058022-84a3e1fd35c9?q=80&w=1200&auto=format&fit=crop" },
            { id: 6, title: "كنبة فخمة رمادية زاوية L", city: "السلط", timeLabel: "منذ 8 ساعات", hoursAgo: 8, price: 250, priceLabel: "250 د.أ", seller: "نورا الحياري", sellerType: "individual", condition: "used", featured: false, hasImage: true, category: "furniture", categoryLabel: "🪑 ركن الأثاث", avatar: "https://randomuser.me/api/portraits/women/68.jpg", img: "https://images.unsplash.com/photo-1615874959474-d609969a20ed?q=80&w=1200&auto=format&fit=crop" },
            { id: 7, title: "ساعة ذكية جديدة بضمان", city: "عمّان", timeLabel: "منذ 6 ساعات", hoursAgo: 6, price: 70, priceLabel: "70 د.أ", seller: "حسن عواد", sellerType: "store", condition: "new", featured: true, hasImage: true, category: "electronics", categoryLabel: "💻 ركن الإلكترونيات", avatar: "https://randomuser.me/api/portraits/men/7.jpg", img: "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop" },
           
];


function generateFavCard(ad) {
  return `
    <article class="ad-card group flex flex-col overflow-hidden bg-white border border-orange-100 rounded-2xl hover:shadow-lg transition hover:border-orange-200 cursor-pointer"
                   onclick="window.location.href='#'">
            <div class="relative">
              <div class="aspect-[4/3] overflow-hidden">
                <img src="${ad.img}" alt="${ad.title}" class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
              </div>

              <button type="button"
        class="ad-fav-btn absolute bottom-3 left-3 w-9 h-9 rounded-full bg-white/95 flex items-center justify-center shadow-sm text-orange-500 transition"
        onclick="event.stopPropagation(); toggleFav(this, ${ad.id})">

                <svg class="w-5 h-5" viewBox="0 0 24 24">
                  <path class="heart-outline hidden"
                        d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"
                        fill="none" stroke="currentColor" stroke-width="2"
                        stroke-linecap="round" stroke-linejoin="round"/>
                  <path class="heart-filled"
                        d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"
                        fill="currentColor"/>
                </svg>
              </button>

              <span class="absolute top-3 right-3 bg-white text-gray-800 text-[11px] px-3 py-1 rounded-full shadow-sm border border-orange-200">
                ${ad.categoryLabel}
              </span>

              ${ad.featured ? `<span class="absolute top-2 left-2 bg-[var(--rukn-orange)] text-white text-[10px] font-bold px-2 py-1 rounded-full shadow">مميز</span>` : ""}
            </div>

            <div class="relative isolate">
              <div class="absolute inset-0 pointer-events-none z-10">
                <div class="absolute inset-0 bg-orange-100/0 group-hover:bg-orange-100/70 transition-all duration-200"></div>

                <div class="absolute top-1/2 -translate-y-1/2 left-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition duration-200">
                  <div class="flex flex-col text-[11px] font-extrabold text-[var(--rukn-orange)] leading-tight text-center">
                    <span>عرض</span><span>الإعلان</span>
                  </div>
                  <span class="ad-hint-arrow text-gray-300 group-hover:text-[var(--rukn-orange)]">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none"
                         viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
                         class="w-5 h-5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="m18.75 4.5-7.5 7.5 7.5 7.5m-6-15L5.25 12l7.5 7.5" />
                    </svg>
                  </span>
                </div>
              </div>

              <div class="relative flex-1 flex flex-col pt-2 p-4 gap-2">
                <h3 class="relative z-50 backdrop-blur py-1 rounded-lg font-bold text-sm text-gray-900 line-clamp-2 min-h-[48px] transition group-hover:text-[var(--rukn-orange)]">
                  ${ad.title}
                </h3>

                <div class="flex items-center gap-4 text-[11px] sm:text-xs text-[var(--muted)] mt-3">
                  <span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5 text-orange-500" viewBox="0 0 20 20" fill="none">
                      <path d="M10 18s6-5.05 6-10a6 6 0 1 0-12 0c0 4.95 6 10 6 10z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
                      <circle cx="10" cy="8" r="2.3" stroke="currentColor" stroke-width="1.6" />
                    </svg>
                    <span>${ad.city}</span>
                  </span>

                  <span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5 text-orange-500" viewBox="0 0 20 20" fill="none">
                      <rect x="3" y="4" width="14" height="13" rx="2" stroke="currentColor" stroke-width="1.6"/>
                      <path d="M7 2v4M13 2v4M4 8h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
                    </svg>
                    <span>${ad.timeLabel}</span>
                  </span>
                </div>
              </div>

              <div class="relative flex items-center justify-between p-4 bg-white border-t-2 border-orange-200">
                <div class="flex items-center gap-2">
                  <img src="${ad.avatar}" class="w-7 h-7 rounded-full border border-gray-200 object-cover" alt="${ad.seller}" />
                  <span class="text-xs sm:text-sm font-semibold text-gray-900">${ad.seller}</span>
                </div>

                <span class="px-4 py-1.5 rounded-xl bg-[var(--rukn-orange)] text-white text-xs sm:text-sm font-bold shadow-sm">
                  ${ad.priceLabel}
                </span>
              </div>
            </div>
          </article>`;
        }

function toggleFav(btn, adId) {
  // لا تغيّر القلب هنا أبداً
  pendingRemoveFavId = adId;
  pendingFavBtn = btn;

  const modal = document.getElementById("confirmFavModal");
  if (!modal) {
    console.error("confirmFavModal not found in HTML");
    return;
  }

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}


function closeFavModal() {
  pendingRemoveFavId = null;
  pendingFavBtn = null;

  const modal = document.getElementById("confirmFavModal");
  if (!modal) return;

  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

function confirmRemoveFav() {
  if (pendingRemoveFavId === null || !pendingFavBtn) return;

  // ✅ خزّن الـ id قبل الإغلاق (مهم)
  const idToRemove = pendingRemoveFavId;

  // ✅ اغلق المودال فورًا
  closeFavModal();

  // ✅ احذف الإعلان وحدث العدد والقائمة
  removeFromFav(idToRemove);
}



function renderFavorites() {
  const container = document.getElementById("favList");
  const countEl = document.getElementById("favCount");
  if (!container || !countEl) return;

  container.innerHTML = "";
  favoritesAds.forEach(ad => { container.innerHTML += generateFavCard(ad); });
  countEl.textContent = favoritesAds.length;

  if (!favoritesAds.length) {
    container.innerHTML = `<div class="col-span-full text-center text-gray-500 py-10 flex flex-col items-center gap-2">
  <svg class="w-10 h-10 text-gray-300" viewBox="0 0 24 24" fill="none">
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1
             a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21
             l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z"
          stroke="currentColor" stroke-width="2"/>
  </svg>
  <span>لا يوجد إعلانات في المفضلة حالياً</span>
</div>
`;
  }
}

function removeFromFav(id) {
  favoritesAds = favoritesAds.filter(ad => ad.id !== id);
  renderFavorites();
  openSuccessModal(
  "تم حذف الإعلان من المفضلة بنجاح",
  "تم الحذف من المفضلة"
);

}


/* =========================================================
   ✅ Global Init
   ========================================================= */
window.addEventListener("load", () => {

  
  renderFavorites();
 
});


