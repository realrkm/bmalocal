/**
 * BMALocal - Password Visibility Toggle (Show / Hide Password)
 * Automatically provides show/hide password buttons for Log In, Sign Up,
 * and any password fields across the BMALocal application.
 */
(function () {
  'use strict';

  // SVG Icons (Lucide clean vector icons)
  var EYE_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>' +
    '<circle cx="12" cy="12" r="3"/>' +
    '</svg>';

  var EYE_SLASH_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>' +
    '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>' +
    '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>' +
    '<line x1="2" y1="2" x2="22" y2="22"/>' +
    '</svg>';

  function attachToggle(input) {
    if (!input) return;

    // Check if already initialized or already inside a wrapper
    if (input.dataset.bmaPasswordInit === 'true' || input.closest('.bma-password-wrapper')) {
      return;
    }

    var parent = input.parentNode;
    if (!parent) return;

    // Mark input as processed and track that it's a password field
    input.dataset.bmaPasswordInit = 'true';
    input.setAttribute('data-bma-password-field', 'true');

    // Create wrapper container
    var wrapper = document.createElement('div');
    wrapper.className = 'bma-password-wrapper';

    // Preserve vertical spacing by transferring bottom margin if present
    try {
      var compStyle = window.getComputedStyle(input);
      if (compStyle && compStyle.marginBottom && parseFloat(compStyle.marginBottom) > 0) {
        wrapper.style.marginBottom = compStyle.marginBottom;
        input.style.marginBottom = '0px';
      }
    } catch (e) {}

    // Insert wrapper into DOM and move input inside wrapper
    parent.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    // Create toggle button
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'bma-password-toggle-btn';
    btn.setAttribute('aria-label', 'Show password');
    btn.setAttribute('title', 'Show password');
    btn.tabIndex = -1; // Avoid disrupting standard tab navigation between fields
    btn.innerHTML = EYE_SVG;

    // Prevent clicking the button from blurring the input
    btn.addEventListener('mousedown', function (e) {
      e.preventDefault();
    });

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      var isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.innerHTML = isPassword ? EYE_SLASH_SVG : EYE_SVG;
      var newLabel = isPassword ? 'Hide password' : 'Show password';
      btn.setAttribute('aria-label', newLabel);
      btn.setAttribute('title', newLabel);

      // Restore focus to input and keep cursor at end of text
      input.focus();
      try {
        var len = input.value.length;
        input.setSelectionRange(len, len);
      } catch (err) {}
    });

    wrapper.appendChild(btn);
  }

  var scanScheduled = false;
  function scheduleScan() {
    if (scanScheduled) return;
    scanScheduled = true;
    requestAnimationFrame(function () {
      scanScheduled = false;
      scanAllPasswordInputs();
    });
  }

  function scanAllPasswordInputs() {
    var selector =
      'input[type="password"]:not([data-bma-password-init="true"]), ' +
      'input[data-bma-password-field="true"]:not([data-bma-password-init="true"])';
    var inputs = document.querySelectorAll(selector);
    for (var i = 0; i < inputs.length; i++) {
      attachToggle(inputs[i]);
    }
  }

  // Initial trigger
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleScan);
  } else {
    scheduleScan();
  }

  // MutationObserver to detect modal insertions, view switches (Log In <-> Sign Up), etc.
  var observer = new MutationObserver(function (mutations) {
    var hasInputs = false;
    for (var i = 0; i < mutations.length; i++) {
      var m = mutations[i];
      if (m.addedNodes && m.addedNodes.length > 0) {
        for (var j = 0; j < m.addedNodes.length; j++) {
          var node = m.addedNodes[j];
          if (node.nodeType === 1) {
            if (node.tagName === 'INPUT' || (node.querySelector && node.querySelector('input'))) {
              hasInputs = true;
              break;
            }
          }
        }
      }
      if (hasInputs) break;
    }
    if (hasInputs) {
      scheduleScan();
    }
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  // Focus fallback: if a user clicks/tabs into any password input, ensure it is enhanced
  document.addEventListener(
    'focusin',
    function (e) {
      if (
        e.target &&
        e.target.tagName === 'INPUT' &&
        (e.target.type === 'password' || e.target.getAttribute('data-bma-password-field') === 'true')
      ) {
        if (!e.target.dataset.bmaPasswordInit) {
          attachToggle(e.target);
        }
      }
    },
    true
  );

  // Periodic safety check during the first 5 seconds of app launch (covers Skulpt async compilation)
  var safetyCounter = 0;
  var safetyInterval = setInterval(function () {
    scheduleScan();
    safetyCounter++;
    if (safetyCounter > 10) {
      clearInterval(safetyInterval);
    }
  }, 500);

  // Expose globally so Anvil Python or other JS routines can trigger directly
  window.initBmaPasswordToggles = scheduleScan;
})();
