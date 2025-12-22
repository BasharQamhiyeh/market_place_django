document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ attribute_options_toggle.js running");

  function toggleOptions(attributeBlock) {
    const inputType = attributeBlock.querySelector('select[name$="-input_type"]');
    if (!inputType) return;

    const uiType = attributeBlock.querySelector('select[name$="-ui_type"]'); // ✅ new
    const optionsGroup = attributeBlock.querySelector('.djn-group[data-inline-model*="attributeoption"]');
    if (!optionsGroup) return;

    function setDisabled(el, disabled) {
      if (!el) return;
      el.disabled = disabled;
      if (disabled) el.classList.add("disabled");
      else el.classList.remove("disabled");
    }

    function updateVisibility() {
      const isSelect = inputType.value === "select";

      // show/hide options list
      optionsGroup.style.display = isSelect ? "" : "none";

      // ui_type only meaningful for select
      setDisabled(uiType, !isSelect);

      // optional: reset ui_type when not select (prevents weird stale values)
      if (!isSelect && uiType) {
        uiType.value = "dropdown";
      }
    }

    inputType.addEventListener("change", updateVisibility);
    updateVisibility();
  }

  function initAll() {
    document
      .querySelectorAll('.djn-group[data-inline-model*="marketplace-attribute"] .djn-item')
      .forEach(toggleOptions);
  }

  initAll();
  document.body.addEventListener("nested:ready", initAll);
  document.body.addEventListener("nested:initialized", initAll);
  document.body.addEventListener("formset:added", initAll);
});