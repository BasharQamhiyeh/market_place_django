document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ attribute_options_toggle.js (final) running");

  function toggleOptions(attributeBlock) {
    // Each attribute inline has its own select for input_type
    const selectField = attributeBlock.querySelector('select[name$="-input_type"]');
    if (!selectField) return;

    // The "Options" section lives in a nested .djn-group for AttributeOption
    const optionsGroup = attributeBlock.querySelector('.djn-group[data-inline-model*="attributeoption"]');
    if (!optionsGroup) return;

    function updateVisibility() {
      const show = selectField.value === "select";
      optionsGroup.style.display = show ? "" : "none";
    }

    selectField.addEventListener("change", updateVisibility);
    updateVisibility(); // initial
  }

  // Function to scan all attribute blocks
  function initAll() {
    document
      .querySelectorAll('.djn-group[data-inline-model*="marketplace-attribute"] .djn-item')
      .forEach(toggleOptions);
  }

  // Initial run and also re-run when nested-admin updates the DOM
  initAll();
  document.body.addEventListener("nested:ready", initAll);
  document.body.addEventListener("nested:initialized", initAll);
  document.body.addEventListener("formset:added", initAll);
});
