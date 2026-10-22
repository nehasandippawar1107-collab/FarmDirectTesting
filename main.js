/**
 * FarmDirect - Interactive Client-Side JavaScript
 * Handles cart interactions, payment option toggles, filter helpers, and UI feedback
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initToast();
  initAjaxAddToCart();
  initPaymentSelector();
  initQuantityButtons();
  initAlertDismissal();
});

/* ==========================================================================
   Mobile Navigation Toggle
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const isOpen = navLinks.classList.contains('open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
      toggleBtn.innerHTML = isOpen ? '✕' : '☰';
    });
  }
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
let toastTimeout;
function showToast(message, type = 'success') {
  let toast = document.getElementById('toast-popup');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-popup';
    toast.className = 'toast-popup';
    document.body.appendChild(toast);
  }

  const icon = type === 'success' ? '🌱' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  toast.className = 'toast-popup show';

  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

function initToast() {
  // Available globally
  window.showToast = showToast;
}

/* ==========================================================================
   AJAX Add-to-Cart with Smooth Feedback
   ========================================================================== */
function initAjaxAddToCart() {
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('form.ajax-add-to-cart');
    if (!form) return;

    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Adding...</span>';
    }

    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const data = await response.json();
      if (response.ok && data.success) {
        showToast(data.message, 'success');
        // Update cart badge if returned
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge && typeof data.cart_count !== 'undefined') {
          cartBadge.textContent = data.cart_count;
          cartBadge.style.transform = 'scale(1.2)';
          setTimeout(() => {
            cartBadge.style.transform = 'scale(1)';
          }, 200);
        }
      } else {
        showToast(data.message || 'Could not add to cart.', 'error');
      }
    } catch (err) {
      // Fallback submit if AJAX encounters network error
      form.submit();
      return;
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    }
  });
}

/* ==========================================================================
   Payment Selector Toggle on Checkout
   ========================================================================== */
function initPaymentSelector() {
  const methodCards = document.querySelectorAll('.payment-method-card');
  const detailsContainers = {
    'COD': document.getElementById('payment-details-cod'),
    'UPI': document.getElementById('payment-details-upi'),
    'Card': document.getElementById('payment-details-card'),
    'NetBanking': document.getElementById('payment-details-netbanking')
  };

  if (!methodCards.length) return;

  methodCards.forEach(card => {
    card.addEventListener('click', () => {
      // Unselect all
      methodCards.forEach(c => c.classList.remove('selected'));
      // Select clicked
      card.classList.add('selected');

      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        const method = radio.value;

        // Hide all detail boxes
        Object.values(detailsContainers).forEach(box => {
          if (box) box.style.display = 'none';
        });

        // Show matching detail box
        if (detailsContainers[method]) {
          detailsContainers[method].style.display = 'block';
        }
      }
    });
  });
}

/* ==========================================================================
   Interactive Quantity Buttons (+ / -)
   ========================================================================== */
function initQuantityButtons() {
  document.querySelectorAll('.qty-control').forEach(control => {
    const input = control.querySelector('.qty-input');
    const plusBtn = control.querySelector('.qty-btn-plus');
    const minusBtn = control.querySelector('.qty-btn-minus');
    const form = control.closest('form');

    if (!input) return;

    if (plusBtn) {
      plusBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const current = parseInt(input.value, 10) || 1;
        const max = parseInt(input.getAttribute('max'), 10) || 999;
        if (current < max) {
          input.value = current + 1;
          if (form && form.classList.contains('auto-submit-qty')) {
            form.submit();
          }
        }
      });
    }

    if (minusBtn) {
      minusBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const current = parseInt(input.value, 10) || 1;
        const min = parseInt(input.getAttribute('min'), 10) || 1;
        if (current > min) {
          input.value = current - 1;
          if (form && form.classList.contains('auto-submit-qty')) {
            form.submit();
          }
        }
      });
    }
  });
}

/* ==========================================================================
   Flash Alert Dismissal
   ========================================================================== */
function initAlertDismissal() {
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });
}

/* Quick Fill Demo Credential Helper */
window.fillDemo = function(email, password) {
  const emailInput = document.querySelector('input[name="email"]');
  const passwordInput = document.querySelector('input[name="password"]');
  if (emailInput && passwordInput) {
    emailInput.value = email;
    passwordInput.value = password;
    showToast(`Filled credentials for ${email}`, 'success');
  }
};
