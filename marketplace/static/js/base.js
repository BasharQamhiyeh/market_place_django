(() => {
  "use strict";

  // Read context safely
  function readRuknContext() {
    const node = document.getElementById("rukn-context");
    if (!node) return { isAuthenticated: false, userId: null, username: "" };
    try { return JSON.parse(node.textContent || "{}"); }
    catch { return { isAuthenticated: false, userId: null, username: "" }; }
  }

  window.RUKN = window.RUKN || readRuknContext();

  // Helpers
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const ui = {
    topbar: $(".topbar"),
    categoriesRow: $("#categoriesRow"),

    guestActions: $("#guestActions"),
    authButtonsMobile: $("#authButtonsMobile"),
    userActionsDropdowns: $("#userActionsDropdowns"),
    userDropdown: $("#userDropdown"),

    sellBtn: $("#sellBtn"),
    buyBtn: $("#buyBtn"),
    searchInput: $("#searchInput"),
    searchBtn: $("#searchBtn"),
    intentBox: $("#intentBox"),

    loginModal: $("#loginModal"),
    loginForm: $("#loginForm"),
    phoneGroup: $("#phoneGroup"),
    passGroup: $("#passGroup"),
    phoneInput: $("#phone"),
    passInput: $("#password"),

    centerModal: $("#centerModal"),
    centerModalContent: $("#centerModalContent"),

    categoriesModal: $("#categoriesModal"),
    categoriesModalContent: $("#categoriesModalContent"),
  };

  function safeLucide() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  // ===== Topbar height var for sticky categories
  function updateTopbarHeight() {
    if (!ui.topbar) return;
    document.documentElement.style.setProperty("--topbar-height", `${ui.topbar.offsetHeight}px`);
  }

  // ===== Hide categories row on scroll
  function initCategoriesRowAutoHide() {
    if (!ui.categoriesRow) return;

    let isHidden = false;
    let ticking = false;

    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;

      requestAnimationFrame(() => {
        const y = window.scrollY;

        if (!isHidden && y > 80) {
          ui.categoriesRow.classList.add("hide");
          isHidden = true;
        }

        if (isHidden && y < 10) {
          ui.categoriesRow.classList.remove("hide");
          isHidden = false;
        }

        ticking = false;
      });
    });
  }

  // ===== Menus
  function closeAllMenus() {
    $$(".actions-dropdown").forEach(d => d.classList.remove("active"));
    ui.userDropdown?.classList.remove("active");
  }

  function toggleDropdownById(id) {
    const dropdown = document.getElementById(id);
    if (!dropdown) return;

    const isOpen = dropdown.classList.contains("active");
    closeAllMenus();
    if (!isOpen) dropdown.classList.add("active");
  }

  function toggleUserMenu() {
    if (!ui.userDropdown) return;
    const isOpen = ui.userDropdown.classList.contains("active");
    closeAllMenus();
    if (!isOpen) ui.userDropdown.classList.add("active");
  }

  // ===== Search theme (sell/buy)
  const state = { isBuy: false };

  function updateSearchTheme() {
    if (!ui.searchInput || !ui.searchBtn || !ui.intentBox || !ui.sellBtn || !ui.buyBtn) return;

    const color = state.isBuy ? "var(--rukn-green)" : "var(--rukn-orange)";

    ui.sellBtn.className = `px-3 h-8 text-xs font-bold transition-colors ${!state.isBuy ? "bg-[var(--rukn-orange)] text-white" : "text-gray-500"}`;
    ui.buyBtn.className  = `px-3 h-8 text-xs font-bold transition-colors ${ state.isBuy ? "bg-[var(--rukn-green)] text-white" : "text-gray-500"}`;

    ui.searchInput.style.borderColor = color;
    ui.searchInput.placeholder = state.isBuy ? "ابحث عن طلب..." : "ابحث عن إعلان...";
    ui.searchBtn.style.backgroundColor = color;
    ui.intentBox.style.borderColor = color;
  }

  function initSearch() {
    ui.sellBtn?.addEventListener("click", () => {
      state.isBuy = false;
      updateSearchTheme();
    });

    ui.buyBtn?.addEventListener("click", () => {
      state.isBuy = true;
      updateSearchTheme();
    });

    ui.searchInput?.addEventListener("input", (e) => {
      const hasValue = (e.target.value || "").trim().length > 0;
      ui.searchBtn.disabled = !hasValue;
      ui.searchBtn.classList.toggle("opacity-50", !hasValue);
      ui.searchBtn.classList.toggle("cursor-not-allowed", !hasValue);
    });

    updateSearchTheme();
  }

  // ===== Auth UI (server decides, JS only reflects)
  function applyAuthUI() {
    const loggedIn = !!window.RUKN?.isAuthenticated;

    if (loggedIn) {
      ui.guestActions?.classList.add("hidden");
      ui.authButtonsMobile?.classList.add("hidden");
      ui.userActionsDropdowns?.classList.remove("hidden");
      repositionUserIcons();
    } else {
      ui.guestActions?.classList.remove("hidden");
      ui.authButtonsMobile?.classList.remove("hidden");
      ui.userActionsDropdowns?.classList.add("hidden");
      closeAllMenus();
    }
  }

  // ===== Move user icons next to logo in mobile portrait
  function repositionUserIcons() {
    const userActions = ui.userActionsDropdowns;
    const mobilePlaceholder = document.getElementById("mobileUserPlaceholder");
    const desktopContainer = document.getElementById("desktopAuthContainer");
    if (!userActions || userActions.classList.contains("hidden")) return;

    const isMobile = window.innerWidth <= 991;
    const isPortrait = window.matchMedia("(orientation: portrait)").matches;

    closeAllMenus();

    if (isMobile && isPortrait) {
      if (mobilePlaceholder && !mobilePlaceholder.contains(userActions)) {
        mobilePlaceholder.appendChild(userActions);
      }
    } else {
      if (desktopContainer && !desktopContainer.contains(userActions)) {
        desktopContainer.appendChild(userActions);
      }
    }
  }

  // ===== Login modal - SIMPLIFIED (like old header.js) - inline scripts handle errors
  function openLogin() {
    if (!ui.loginModal) return;
    ui.loginModal.classList.remove("hidden");
    requestAnimationFrame(() => ui.loginModal.classList.add("active"));
    document.body.style.overflow = "hidden";

    // Focus on phone input
    setTimeout(() => ui.phoneInput?.focus(), 100);
  }

  function closeLogin() {
    if (!ui.loginModal) return;
    ui.loginModal.classList.remove("active");
    setTimeout(() => {
      ui.loginModal.classList.add("hidden");
      document.body.style.overflow = "";
    }, 250);
  }

  function togglePass() {
    if (!ui.passInput) return;
    const icon = $(".toggle-password");
    if (ui.passInput.type === "password") {
      ui.passInput.type = "text";
      icon?.classList.replace("fa-eye", "fa-eye-slash");
    } else {
      ui.passInput.type = "password";
      icon?.classList.replace("fa-eye-slash", "fa-eye");
    }
  }

  function clearError(groupEl) {
    groupEl?.classList.remove("error");
  }

  // ===== Phone sanitization (digits only, max 10) - like old header.js
  function sanitizePhone() {
    if (!ui.phoneInput) return;
    ui.phoneInput.value = (ui.phoneInput.value || "").replace(/\D+/g, "").slice(0, 10);
  }

  function initLoginModal() {
    // Open modal buttons
    $$("[data-open-login]").forEach(btn => btn.addEventListener("click", (e) => {
      e.preventDefault();
      openLogin();
    }));

    // Close modal buttons
    $$("[data-close-login]").forEach(btn => btn.addEventListener("click", (e) => {
      e.preventDefault();
      closeLogin();
    }));

    // Password toggle
    $("[data-toggle-pass]")?.addEventListener("click", togglePass);

    // Phone input - sanitize on input
    ui.phoneInput?.addEventListener("input", () => {
      sanitizePhone();
      clearError(ui.phoneGroup);
    });

    // Phone input - sanitize on paste
    ui.phoneInput?.addEventListener("paste", () => {
      setTimeout(sanitizePhone, 0);
    });

    // Password input - clear error on type
    ui.passInput?.addEventListener("input", () => clearError(ui.passGroup));

    // Click outside closes
    ui.loginModal?.addEventListener("click", (ev) => {
      if (ev.target === ui.loginModal) closeLogin();
    });

    // Escape key closes
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && ui.loginModal && !ui.loginModal.classList.contains("hidden")) {
        closeLogin();
      }
    });

    // Form submission - Django handles validation, we just submit
    // The inline scripts at bottom of base.html will reopen modal if login_error
    ui.loginForm?.addEventListener("submit", (e) => {
      // Let Django handle everything - just make sure phone is sanitized
      sanitizePhone();

      // Basic client-side validation (optional - Django will validate anyway)
      const phone = (ui.phoneInput?.value || "").trim();
      const pass = (ui.passInput?.value || "").trim();
      const phoneRegex = /^07\d{8}$/;

      clearError(ui.phoneGroup);
      clearError(ui.passGroup);

      let ok = true;

      if (!phoneRegex.test(phone)) {
        ui.phoneGroup?.classList.add("error");
        ui.phoneInput?.focus();
        ok = false;
      }

      if (!pass) {
        ui.passGroup?.classList.add("error");
        if (ok) ui.passInput?.focus();
        ok = false;
      }

      if (!ok) {
        e.preventDefault();
        return;
      }

      // If validation passes, let form submit to Django
      // Django will redirect back with ?login_error=1 if wrong credentials
      // The inline script at bottom will reopen the modal
    });
  }

  // ===== Center modal (mobile)
  function openCenterModal(html) {
    if (!ui.centerModal || !ui.centerModalContent) return;
    ui.centerModalContent.innerHTML = html;
    ui.centerModal.classList.remove("hidden");
    safeLucide();
    // Close modal when any link inside it is clicked (handles same-page hash navigation)
    ui.centerModalContent.querySelectorAll("a[href]").forEach(a => {
      a.addEventListener("click", () => closeCenterModal(), { once: true });
    });
  }

  function closeCenterModal() {
    ui.centerModal?.classList.add("hidden");
  }

  function initCenterModal() {
    ui.centerModal?.addEventListener("click", (e) => {
      if (e.target === ui.centerModal) closeCenterModal();
    });
  }

  // ===== Categories Modal: reads structure from the Django-rendered mega-menu DOM =====

  // Title is an <a> link so tapping it navigates (issue 3 fix)
  function catModalHeader(title, titleHref, showBack) {
    return `
      <div class="popup-header">
        ${showBack ? `
          <span data-cat-back style="position:absolute;right:12px;top:50%;transform:translateY(-50%);cursor:pointer;">
            <i data-lucide="chevron-right"></i>
          </span>` : ""}
        <a href="${titleHref}" style="color:inherit;text-decoration:none;">${title}</a>
        <button data-modal-close class="close-btn" aria-label="إغلاق">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
  }

  function wireCatModalButtons(backFn) {
    ui.categoriesModalContent?.querySelector("[data-modal-close]")
      ?.addEventListener("click", closeCategoriesModal);
    if (backFn) {
      ui.categoriesModalContent?.querySelector("[data-cat-back]")
        ?.addEventListener("click", backFn);
    }
    safeLucide();
  }

  // 3-level mega-menu: <h6> is a direct child of the column div (NOT inside an <a>)
  // 2-level mega-menu: <h6> is wrapped in <a class="sub-link">
  function isThreeLevelMenu(megaMenu) {
    const firstH6 = megaMenu.querySelector("h6");
    if (!firstH6) return false;
    return firstH6.parentElement.tagName !== "A";
  }

  // Get the column divs from the grid inside the mega-menu, skip promo-card.
  function getColumnDivs(megaMenu) {
    const gridDiv = megaMenu.querySelector(":scope > div");
    if (!gridDiv) return [];
    return Array.from(gridDiv.querySelectorAll(":scope > div"))
      .filter(el => !el.classList.contains("promo-card"));
  }

  // Get actual child links from a column:
  // - 3-level: every .sub-link is a leaf
  // - 2-level: skip the .sub-link that wraps the h6 (that IS the group itself)
  function getChildLinks(colDiv, threeLevel) {
    const all = Array.from(colDiv.querySelectorAll(".sub-link"));
    return threeLevel ? all : all.filter(l => !l.querySelector("h6"));
  }

  // Level 1 modal: groups (column headers) as navigable items
  function renderCatLevel1(catName, catHref, megaMenu) {
    if (!ui.categoriesModalContent) return;

    const threeLevel = isThreeLevelMenu(megaMenu);
    const columnDivs = getColumnDivs(megaMenu);
    let bodyHTML = "";

    columnDivs.forEach((colDiv, idx) => {
      const h6 = colDiv.querySelector("h6");
      if (!h6) return;

      const groupName = h6.textContent.trim();
      const childLinks = getChildLinks(colDiv, threeLevel);

      if (childLinks.length > 0) {
        // Has children → show as navigable row with arrow
        bodyHTML += `
          <div class="popup-option has-children" data-col-idx="${idx}">
            ${groupName}
          </div>`;
      } else {
        // No children → direct link
        const groupHref = !threeLevel
          ? (h6.closest("a")?.getAttribute("href") || catHref)
          : catHref;
        bodyHTML += `<a href="${groupHref}" class="popup-option">${groupName}</a>`;
      }
    });

    bodyHTML += `<a href="${catHref}" class="popup-option highlight">عرض كل ${catName}</a>`;

    ui.categoriesModalContent.innerHTML =
      catModalHeader(catName, catHref, false) +
      `<div style="padding:16px">${bodyHTML}</div>`;

    ui.categoriesModalContent.querySelectorAll("[data-col-idx]").forEach(item => {
      item.addEventListener("click", () => {
        const colDiv = columnDivs[parseInt(item.dataset.colIdx, 10)];
        if (!colDiv) return;
        const h6 = colDiv.querySelector("h6");
        const groupName = h6?.textContent.trim() || "";
        const groupHref = !threeLevel
          ? (h6?.closest("a")?.getAttribute("href") || catHref)
          : catHref;
        renderCatLevel2(groupName, groupHref, colDiv, threeLevel, catName, catHref, megaMenu);
      });
    });

    wireCatModalButtons(null);
  }

  // Level 2 modal: child links inside a group
  function renderCatLevel2(groupName, groupHref, colDiv, threeLevel, parentName, parentHref, megaMenu) {
    if (!ui.categoriesModalContent) return;

    const childLinks = getChildLinks(colDiv, threeLevel);
    let bodyHTML = "";

    childLinks.forEach(link => {
      const name = link.textContent.trim();
      const href = link.getAttribute("href") || "#";
      bodyHTML += `<a href="${href}" class="popup-option">${name}</a>`;
    });

    // Prefer any explicit "مشاهدة الكل" / browse link in the column
    const viewAllEl = Array.from(colDiv.querySelectorAll("a")).find(
      a => !a.classList.contains("sub-link") && a.getAttribute("href") && a.getAttribute("href") !== "#"
    );
    const viewAllHref = viewAllEl?.getAttribute("href") || groupHref;
    bodyHTML += `<a href="${viewAllHref}" class="popup-option highlight">عرض كل ${groupName}</a>`;

    ui.categoriesModalContent.innerHTML =
      catModalHeader(groupName, groupHref, true) +
      `<div style="padding:16px">${bodyHTML}</div>`;

    wireCatModalButtons(() => renderCatLevel1(parentName, parentHref, megaMenu));
  }

  function openCategoriesModal(linkEl) {
    if (!ui.categoriesModal || !ui.categoriesModalContent) return;
    const catName = linkEl.textContent.trim();
    const catHref = linkEl.getAttribute("href") || "#";
    const group = linkEl.closest(".group");
    const megaMenu = group?.querySelector(".mega-menu");
    if (!megaMenu) return; // no children → let browser navigate
    renderCatLevel1(catName, catHref, megaMenu);
    ui.categoriesModal.classList.remove("hidden");
  }

  function closeCategoriesModal() {
    ui.categoriesModal?.classList.add("hidden");
  }

  function initCategoriesModal() {
    $$("[data-mobile-category]").forEach(a => {
      a.addEventListener("click", (e) => {
        if (window.innerWidth > 991) return; // desktop uses mega-menu
        const group = a.closest(".group");
        const megaMenu = group?.querySelector(".mega-menu");
        if (!megaMenu) return; // no children → navigate normally
        e.preventDefault();
        e.stopPropagation();
        openCategoriesModal(a);
      });
    });

    ui.categoriesModal?.addEventListener("click", (e) => {
      if (e.target === ui.categoriesModal) closeCategoriesModal();
    });
  }

  // ===== Mobile modal helpers =====

  function popupHeaderHTML(title) {
    return `
      <div class="popup-header">
        ${title}
        <button class="close-btn" onclick="window.RUKN_UI.closeCenterModal()" aria-label="إغلاق">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
  }

  function accountItemHTML(icon, title, href, extraClass = "") {
    return `
      <a href="${href}" class="account-item ${extraClass}">
        <i class="fas fa-${icon}"></i>
        <span class="text-sm font-bold">${title}</span>
      </a>
    `;
  }

  function handleFavorites(e) {
    e.stopPropagation();
    if (window.innerWidth > 991) { toggleDropdownById("favDropdown"); return; }
    const dropdown = document.getElementById("favDropdown");
    let contentHTML = "";
    if (dropdown) {
      const scroll = dropdown.querySelector(".fav-scroll");
      const footer = dropdown.querySelector(".dropdown-footer");
      contentHTML = scroll ? scroll.innerHTML : '<div class="p-4 text-center text-sm text-gray-400">لا يوجد منتجات في المفضلة</div>';
      if (footer) {
        const link = footer.querySelector(".btn-view-all");
        if (link) contentHTML += `<a href="${link.href}" class="popup-option highlight">${link.textContent}</a>`;
      }
    } else {
      contentHTML = '<div class="p-4 text-center text-sm text-gray-400">لا يوجد منتجات في المفضلة</div>';
    }
    openCenterModal(`${popupHeaderHTML("المفضلة")}<div style="padding:16px">${contentHTML}</div>`);
  }

  function handleMessages(e) {
    e.stopPropagation();
    if (window.innerWidth > 991) { toggleDropdownById("msgDropdown"); return; }
    const dropdown = document.getElementById("msgDropdown");
    let contentHTML = "";
    if (dropdown) {
      const scroll = dropdown.querySelector(".msg-scroll");
      const footer = dropdown.querySelector(".dropdown-footer");
      contentHTML = scroll ? scroll.innerHTML : '<div class="p-4 text-center text-sm text-gray-400">لا يوجد رسائل</div>';
      if (footer) {
        const link = footer.querySelector(".btn-view-all");
        if (link) contentHTML += `<a href="${link.href}" class="popup-option highlight">${link.textContent}</a>`;
      }
    } else {
      contentHTML = '<div class="p-4 text-center text-sm text-gray-400">لا يوجد رسائل</div>';
    }
    openCenterModal(`${popupHeaderHTML("الرسائل")}<div style="padding:16px">${contentHTML}</div>`);
    safeLucide();
  }

  function handleNotifications(e) {
    e.stopPropagation();
    if (window.innerWidth > 991) { toggleDropdownById("notifDropdown"); return; }
    const dropdown = document.getElementById("notifDropdown");
    let contentHTML = "";
    if (dropdown) {
      const scroll = dropdown.querySelector(".notif-scroll");
      const footer = dropdown.querySelector(".dropdown-footer");
      contentHTML = scroll ? scroll.innerHTML : '<div class="p-4 text-center text-sm text-gray-400">لا يوجد إشعارات</div>';
      if (footer) {
        const link = footer.querySelector(".btn-view-all");
        if (link) contentHTML += `<a href="${link.href}" class="popup-option highlight">${link.textContent}</a>`;
      }
    } else {
      contentHTML = '<div class="p-4 text-center text-sm text-gray-400">لا يوجد إشعارات</div>';
    }
    openCenterModal(`${popupHeaderHTML("الإشعارات")}<div style="padding:16px">${contentHTML}</div>`);
    safeLucide();
  }

  function handleUserAccount(e) {
    e.stopPropagation();
    if (window.innerWidth > 991) { toggleUserMenu(); return; }
    const userName = window.RUKN?.username || "المستخدم";
    const userAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=ff7a18&color=fff`;
    openCenterModal(`
      ${popupHeaderHTML("الحساب")}
      <div style="padding:16px">
        <div class="text-center mb-4">
          <img src="${userAvatar}" class="w-16 h-16 rounded-full mx-auto mb-2">
          <div class="font-bold">${userName}</div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          ${accountItemHTML("user", "الملف الشخصي", "/my-account/#tab-info")}
          ${accountItemHTML("bullhorn", "إعلاناتي", "/my-account/#tab-ads")}
          ${accountItemHTML("shopping-cart", "طلباتي", "/my-account/#tab-requests")}
          ${!window.RUKN?.isStore ? accountItemHTML("flag", "بلاغاتي", "/lost-found/?tab=mine") : ""}
          ${accountItemHTML("wallet", "المحفظة", "/my-account/#tab-wallet")}
          ${accountItemHTML("user-plus", "دعوة الأصدقاء", "/my-account/#tab-wallet")}
          ${window.RUKN?.isStaff ? accountItemHTML("tachometer-alt", "لوحة التحكم", "/admin/") : ""}
        </div>
        <a href="/logout/" class="account-item text-red-500 w-full" style="margin-top:12px;display:flex;">
          <i class="fas fa-sign-out-alt"></i>
          <span class="text-sm font-bold">تسجيل الخروج</span>
        </a>
      </div>
    `);
  }

  // ===== Wire header dropdown buttons (mobile-aware)
  function initHeaderDropdowns() {
    $$("[data-toggle-dropdown]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-toggle-dropdown");

        if (window.innerWidth <= 991) {
          if (id === "favDropdown")   { handleFavorites(e);     return; }
          if (id === "msgDropdown")   { handleMessages(e);      return; }
          if (id === "notifDropdown") { handleNotifications(e); return; }
        }

        if (id) toggleDropdownById(id);
      });
    });

    $("[data-toggle-user-menu]")?.addEventListener("click", (e) => {
      e.stopPropagation();
      if (window.innerWidth <= 991) { handleUserAccount(e); return; }
      toggleUserMenu();
    });

    window.addEventListener("click", () => closeAllMenus());
    ui.userDropdown?.addEventListener("click", (e) => e.stopPropagation());
  }

  // ===== Notification Icons — Lucide-based, matched to mockup
  // Returns { icon, bg, border, color } based on notification kind + status
  function getNotifIconData(kind, status) {
    if (kind === 'ad') {
      if (status === 'pending')   return { icon: 'clock',         bg: '#fff7ed', border: '#fdba74', color: '#c2410c' };
      if (status === 'approved')  return { icon: 'check-circle',  bg: '#dcfce7', border: '#86efac', color: '#15803d' };
      if (status === 'rejected')  return { icon: 'x-circle',      bg: '#fee2e2', border: '#fca5a5', color: '#b91c1c' };
      if (status === 'featured' || status === 'featured_expired')
                                  return { icon: 'star',           bg: '#fff7ed', border: '#fdba74', color: '#c2410c' };
      return                             { icon: 'megaphone',      bg: '#fff7ed', border: '#fdba74', color: '#c2410c' };
    }
    if (kind === 'request') {
      if (status === 'pending')   return { icon: 'clock',         bg: '#fff7ed', border: '#fdba74', color: '#c2410c' };
      if (status === 'approved')  return { icon: 'check-circle',  bg: '#dcfce7', border: '#86efac', color: '#15803d' };
      if (status === 'rejected')  return { icon: 'x-circle',      bg: '#fee2e2', border: '#fca5a5', color: '#b91c1c' };
      if (status === 'featured' || status === 'featured_expired')
                                  return { icon: 'star',           bg: '#dcfce7', border: '#86efac', color: '#15803d' };
      return                             { icon: 'shopping-cart',  bg: '#dcfce7', border: '#86efac', color: '#15803d' };
    }
    if (kind === 'wallet') {
      if (status === 'reward')    return { icon: 'gift',           bg: '#f5f3ff', border: '#c4b5fd', color: '#7c3aed' };
      return                             { icon: 'wallet',         bg: '#fef9c3', border: '#fde68a', color: '#b45309' };
    }
    if (kind === 'fav')          return   { icon: 'heart',         bg: '#fdf2f8', border: '#f9a8d4', color: '#db2777' };
    if (kind === 'store_follow') return   { icon: 'user-plus',     bg: '#eef2ff', border: '#a5b4fc', color: '#4338ca' };
    return                               { icon: 'bell',           bg: '#f3f4f6', border: '#e5e7eb', color: '#6b7280' };
  }

  function getNotificationBadge(kind, status) {
    if (status === 'pending') return { text: 'قيد المراجعة', cls: 'status-pending' };
    if (status === 'approved') return { text: 'مقبول', cls: 'status-active' };
    if (status === 'rejected') return { text: 'مرفوض', cls: 'status-rejected' };
    if (status === 'featured_expired') return { text: 'انتهى التمييز', cls: 'status-featured' };
    if (status === 'charged') return { text: 'شحن', cls: 'status-active' };
    if (status === 'used') return { text: 'خصم', cls: 'status-rejected' };
    if (status === 'reward') return { text: 'مكافأة', cls: 'status-active' };
    if (kind === 'fav') return { text: 'مفضلة', cls: 'status-fav' };
    if (kind === 'store_follow' && status === 'followed') return { text: 'متابعة', cls: 'status-active' };
    if (kind === 'store_follow' && status === 'unfollowed') return { text: 'إلغاء متابعة', cls: 'status-unfollow' };
    if (kind === 'system') return { text: 'إشعار', cls: 'status-system' };

    return { text: '', cls: '' };
  }

  function injectNotificationIcons() {
    const items = $$('.dropdown-noti-item');

    items.forEach(item => {
      const kind   = item.dataset.kind   || 'system';
      const status = item.dataset.status || '';
      const iconBox  = item.querySelector('.noti-icon-box');
      const badgeBox = item.querySelector('.noti-badge-box');

      if (iconBox) {
        const data = getNotifIconData(kind, status);
        // Apply icon-box colours
        iconBox.style.background   = data.bg;
        iconBox.style.borderColor  = data.border;
        iconBox.style.color        = data.color;
        // Inject Lucide icon element
        iconBox.innerHTML = '';
        const iconEl = document.createElement('i');
        iconEl.setAttribute('data-lucide', data.icon);
        iconBox.appendChild(iconEl);
      }

      if (badgeBox) {
        const badge = getNotificationBadge(kind, status);
        if (badge.text) {
          badgeBox.textContent = badge.text;
          badgeBox.className = 'noti-badge-box ' + badge.cls;
        }
      }
    });

    safeLucide();
  }

  function getNotificationRedirectUrl(el) {
    const kind = el.dataset.kind || '';
    const storeId = el.dataset.storeId || '';

    // Store-related notifications → store profile
    if (storeId) return `/stores/${storeId}/`;

    const base = '/my-account/';
    switch (kind) {
      case 'ad':           return `${base}#tab-ads`;
      case 'request':      return `${base}#tab-requests`;
      case 'wallet':       return `${base}#tab-wallet`;
      case 'message':      return `${base}#tab-msgs`;
      case 'fav':
      case 'report':
      default:             return `${base}#tab-noti`;
    }
  }

  function initNotificationRead() {
    $$('.dropdown-noti-item[data-notif-id]').forEach(link => {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        const id = this.dataset.notifId;
        const item = this;
        const dest = getNotificationRedirectUrl(this);

        if (!this.classList.contains('is-unread')) {
          window.location.href = dest;
          return;
        }

        fetch(`/my-account/noti/${id}/read/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.RUKN.csrfToken,
            'Content-Type': 'application/json',
          },
        })
        .then(res => res.json())
        .then(data => {
          if (data.ok) {
            item.classList.remove('is-unread');
            item.querySelector('.noti-unread-dot')?.remove();

            const badge = document.querySelector('.notif-badge');
            if (badge) {
              if (data.unread > 0) {
                badge.textContent = data.unread;
                badge.classList.remove('hidden');
              } else {
                badge.classList.add('hidden');
                document.querySelector('.notif-icon')?.classList.remove('filled');
              }
            }
          }
          window.location.href = dest;
        })
        .catch(() => {
          window.location.href = dest;
        });
      });
    });
  }

  // ===== Init
  document.addEventListener("DOMContentLoaded", () => {
    safeLucide();

    updateTopbarHeight();
    window.addEventListener("resize", updateTopbarHeight);
    window.addEventListener("load", updateTopbarHeight);

    initCategoriesRowAutoHide();
    initHeaderDropdowns();
    initSearch();
    initLoginModal();
    initCenterModal();
    initCategoriesModal();

    applyAuthUI();
    repositionUserIcons();

    // Inject notification icons after DOM is ready
    injectNotificationIcons();
    injectMessageIcons();
    initNotificationRead();

  });

  // ===== Message Icons
  function getMessageIconName(type) {
    const icons = {
      'store': 'store',
      'ad': 'megaphone',
      'request': 'file-text'
    };
    return icons[type] || 'message-square';
  }

  function injectMessageIcons() {
    const items = $$('.dropdown-msg-item');

    items.forEach(item => {
      const type = item.dataset.type || 'ad';
      const iconBox = item.querySelector('.msg-icon-box');

      if (iconBox && iconBox.children.length === 0) {
        const iconName = getMessageIconName(type);
        const i = document.createElement('i');
        i.setAttribute('data-lucide', iconName);
        iconBox.appendChild(i);
      }
    });

    safeLucide();
  }

  window.addEventListener("resize", repositionUserIcons);
  window.addEventListener("orientationchange", () => setTimeout(repositionUserIcons, 200));

  // Expose these if you need them elsewhere
  window.RUKN_UI = {
    openLogin,
    closeLogin,
    openCenterModal,
    closeCenterModal,
    openCategoriesModal,
    closeCategoriesModal,
    handleFavorites,
    handleMessages,
    handleNotifications,
    handleUserAccount,
  };

  // ===== BACKWARDS COMPATIBILITY =====
  // Make old code that removes "hidden" class work with new modal system
  // This allows pages like report-modal.js to work without changes
  if (ui.loginModal) {
    let isOpening = false; // Flag to prevent infinite loop

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class' && !isOpening) {
          const classList = ui.loginModal.classList;

          // If "hidden" was removed but modal is not properly open
          if (!classList.contains('hidden') && !classList.contains('active')) {
            // Set flag and open properly using the new system
            isOpening = true;
            openLogin();
            setTimeout(() => { isOpening = false; }, 100);
          }
        }
      });
    });

    observer.observe(ui.loginModal, {
      attributes: true,
      attributeFilter: ['class']
    });
  }
})();

/* =========================================================
   Global success modal helpers (modal lives in base.html)
========================================================= */
window.openSuccessModal = function (message, title) {
  const modal = document.getElementById("successModal");
  const msg   = document.getElementById("successMsg");
  const ttl   = document.getElementById("successTitle");
  if (!modal) return;
  if (msg) msg.innerText   = message;
  if (ttl) ttl.innerText   = title || "تم التنفيذ بنجاح";
  modal.classList.remove("hidden");
  modal.classList.add("flex");
};

window.closeSuccessModal = function () {
  const modal = document.getElementById("successModal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.classList.remove("flex");
};

/* =========================================================
   Store "cannot add requests" modal – global helpers
========================================================= */
window.openStoreNoRequestsModal = function () {
  const m = document.getElementById("storeNoRequestsModal");
  if (!m) return;
  m.classList.remove("hidden");
  m.classList.add("flex");
  document.body.classList.add("overflow-hidden");
};

window.closeStoreNoRequestsModal = function () {
  const m = document.getElementById("storeNoRequestsModal");
  if (!m) return;
  m.classList.add("hidden");
  m.classList.remove("flex");
  document.body.classList.remove("overflow-hidden");
};

// Wire close buttons and backdrop on DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  const m = document.getElementById("storeNoRequestsModal");
  if (!m) return;

  document.getElementById("closeStoreNoRequestsModalBtn")?.addEventListener("click", window.closeStoreNoRequestsModal);
  document.getElementById("closeStoreNoRequestsModalX")?.addEventListener("click", window.closeStoreNoRequestsModal);
  m.addEventListener("click", function (e) {
    if (e.target === m) window.closeStoreNoRequestsModal();
  });

  // Intercept all [data-create-request-btn] elements site-wide
  if (window.RUKN?.isStore) {
    document.addEventListener("click", function (e) {
      const el = e.target.closest("[data-create-request-btn]");
      if (!el) return;
      e.preventDefault();
      window.openStoreNoRequestsModal();
    }, true);
  }
});

/* =========================================================
   Invite Friends link – copy referral link to clipboard
========================================================= */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const inviteLinkEl = document.getElementById("inviteFriendsLink");
    if (!inviteLinkEl) return;

    const referralCode = inviteLinkEl.dataset.referralCode || "";
    if (!referralCode) return;

    inviteLinkEl.addEventListener("click", function (e) {
      e.preventDefault();

      const registerUrl = inviteLinkEl.dataset.registerUrl || "/register/";
      const u = new URL(registerUrl, window.location.origin);
      u.searchParams.set("ref", referralCode);
      const fullLink = u.toString();

      if (navigator.clipboard?.writeText) {
        navigator.clipboard
          .writeText(fullLink)
          .then(() => openSuccessModal("تم نسخ رابط الدعوة بنجاح!", "تم النسخ"))
          .catch(() => openSuccessModal(fullLink, "رابط الدعوة"));
      } else {
        const t = document.createElement("textarea");
        t.value = fullLink;
        t.style.cssText = "position:fixed;left:-9999px";
        document.body.appendChild(t);
        t.select();
        document.execCommand("copy");
        t.remove();
        openSuccessModal("تم نسخ رابط الدعوة بنجاح!", "تم النسخ");
      }
    });
  });
})();