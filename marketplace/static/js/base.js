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
  }

  function closeCenterModal() {
    ui.centerModal?.classList.add("hidden");
  }

  function initCenterModal() {
    ui.centerModal?.addEventListener("click", (e) => {
      if (e.target === ui.centerModal) closeCenterModal();
    });
  }

  let categoryStack = [];

  function popupHeader(title, showBack, backActionName) {
    return `
      <div class="popup-header">
        ${showBack ? `<span class="back-btn" data-cat-back style="position:absolute;right:12px;top:50%;transform:translateY(-50%);cursor:pointer;">
          <i data-lucide="chevron-right"></i>
        </span>` : ""}
        ${title}
        <button class="close-btn" data-modal-close aria-label="إغلاق">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
  }


  function openCategoriesModal(rootKey) {
    if (!ui.categoriesModal) return;
    categoryStack = [rootKey];
    renderCategoriesLevel();
    ui.categoriesModal.classList.remove("hidden");
  }

  function closeCategoriesModal() {
    ui.categoriesModal?.classList.add("hidden");
    categoryStack = [];
  }

  function initCategoriesModal() {
    // open from top nav ONLY on mobile (<=991)
    $$("[data-mobile-category]").forEach(a => {
      a.addEventListener("click", (e) => {
        if (window.innerWidth > 991) return; // desktop uses mega-menu
        e.preventDefault();
        e.stopPropagation();
        const key = a.getAttribute("data-mobile-category");
        if (key) openCategoriesModal(key);
      });
    });

    ui.categoriesModal?.addEventListener("click", (e) => {
      if (e.target === ui.categoriesModal) closeCategoriesModal();
    });
  }

  // ===== Wire header dropdown buttons
  function initHeaderDropdowns() {
    // action dropdowns
    $$("[data-toggle-dropdown]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-toggle-dropdown");
        if (id) toggleDropdownById(id);
      });
    });

    // user menu
    $("[data-toggle-user-menu]")?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleUserMenu();
    });

    // outside click closes
    window.addEventListener("click", () => closeAllMenus());
    ui.userDropdown?.addEventListener("click", (e) => e.stopPropagation());
  }

  // ===== Notification Icons (same as my_account noti.js)
  function getNotificationColor(kind) {
    const colors = {
      'request': '#15803d',
      'ad': '#c2410c',
      'wallet': '#b45309',
      'fav': '#b91c1c',
      'store_follow': '#15803d',
      'system': '#6b7280'
    };
    return colors[kind] || '#6b7280';
  }

  function getNotificationIcon(kind, status) {
    if (kind === 'request') return `
      <svg viewBox="0 0 24 24" fill="none">
        <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
        <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
        <path d="M3 4h2l2.4 12h10.2l2-8H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>`;

    if (kind === 'ad') return `
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4a1 1 0 0 0-1 1Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M14 6v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>`;

    if (kind === 'wallet') return `
      <svg viewBox="0 0 24 24" fill="none">
        <rect x="2" y="6" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
        <path d="M16 12h4" stroke="currentColor" stroke-width="2"/>
      </svg>`;

    if (kind === 'fav') return `
      <svg viewBox="0 0 24 24" fill="none">
        <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      </svg>`;

    if (kind === 'store_follow') return `
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M3 9l1-5h16l1 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5 9v10h14V9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 19v-6h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;

    return `
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 7h18s-3 0-3-7Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" stroke-width="2"/>
      </svg>`;
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
      const kind = item.dataset.kind || 'system';
      const status = item.dataset.status || '';
      const iconBox = item.querySelector('.noti-icon-box');
      const badgeBox = item.querySelector('.noti-badge-box');

      if (iconBox) {
        const color = getNotificationColor(kind);
        iconBox.innerHTML = getNotificationIcon(kind, status);

        // Force color on SVG
        const svg = iconBox.querySelector('svg');
        if (svg) {
          svg.style.color = color;
          svg.querySelectorAll('path, circle, rect, polygon').forEach(el => {
            if (el.getAttribute('stroke')) el.setAttribute('stroke', color);
            if (el.getAttribute('fill') === 'currentColor') el.setAttribute('fill', color);
          });
        }
      }

      if (badgeBox) {
        const badge = getNotificationBadge(kind, status);
        if (badge.text) {
          badgeBox.textContent = badge.text;
          badgeBox.className = 'noti-badge-box ' + badge.cls;
        }
      }
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
  };
})();