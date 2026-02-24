document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ attribute_options_toggle.js running");

  function toggleOptions(attributeBlock) {
    const inputType = attributeBlock.querySelector('select[name$="-input_type"]');
    if (!inputType) return;

    const uiTypeField = attributeBlock.querySelector(".field-ui_type");
    const optionsGroup = attributeBlock.querySelector('.djn-group[data-inline-model*="attributeoption"]');

    function updateVisibility() {
      const isSelect = inputType.value === "select";

      // show/hide options list
      if (optionsGroup) optionsGroup.style.display = isSelect ? "" : "none";

      // show/hide the entire ui_type row
      if (uiTypeField) {
        uiTypeField.style.display = isSelect ? "" : "none";
        const uiTypeSelect = uiTypeField.querySelector("select");
        if (uiTypeSelect && !isSelect) uiTypeSelect.value = "";
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