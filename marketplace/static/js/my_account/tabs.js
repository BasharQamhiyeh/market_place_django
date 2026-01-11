(function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const tabs = document.querySelectorAll(".tab-content");

  function openTab(key) {
    buttons.forEach(btn => btn.classList.toggle("active", btn.dataset.tab === key));
    tabs.forEach(tab => tab.classList.toggle("active", tab.id === "tab-" + key));
    window.location.hash = key; // keep deep-linking
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  buttons.forEach(btn => btn.addEventListener("click", () => openTab(btn.dataset.tab)));

  const hash = window.location.hash.replace("#", "");
  if (hash && document.getElementById("tab-" + hash)) openTab(hash);
})();
