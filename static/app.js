// Cleans up the web address when loaded
window.addEventListener("load", () => {
  history.replaceState(null, null, window.location.pathname);
});


// Nav scroll
document.addEventListener("DOMContentLoaded", () => {
    let lastScroll = 0;
    const header = document.querySelector('.nav');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > lastScroll) {
            header.classList.add('nav-hidden');
        } else {
            header.classList.remove('nav-hidden');
        }

        lastScroll = currentScroll;
    });
});

// Define variables
const panels    = document.querySelectorAll('.test-panel');
const submitBtn = document.getElementById('submitBtn');
const form      = document.querySelector('.tests-select');
const LOGGED_IN = document.getElementById('app').dataset.loggedIn === "true";

let selected = null;

document.addEventListener('DOMContentLoaded', () => {
  const loginAlert       = document.getElementById('customAlert');
  const loginCancelBtn   = loginAlert.querySelector('.cancel');

  const unavailableAlert = document.getElementById('unavailableAlert');
  const unavailableCancelBtn = unavailableAlert.querySelector('.cancel');

  // Close Alert
  function setAlertHandlers(overlay, cancelButton) {
    // Cancel button
    cancelButton.addEventListener('click', () => overlay.classList.add('hidden'));
    // click elsewhere
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {          // solo si toca el fondo semitransparente
        overlay.classList.add('hidden');
      }
    });
  }

  setAlertHandlers(loginAlert,       loginCancelBtn);
  setAlertHandlers(unavailableAlert, unavailableCancelBtn);

  // Show alerts if
  panels.forEach(panel => {
    panel.addEventListener('click', () => {
      // 1. user not logged
      if (!LOGGED_IN) {
        loginAlert.classList.remove('hidden');
        return;
      }

      // 2. unavailable
      if (panel.dataset.available === 'false') {
        unavailableAlert.classList.remove('hidden');
        return;
      }

      // 3) Remove unselected panel
      if (selected === panel) {
        panel.classList.remove('selected');
        selected = null;
      } else {
        panels.forEach(p => p.classList.remove('selected'));
        panel.classList.add('selected');
        selected = panel;
      }
      submitBtn.classList.toggle('enabled', selected !== null);
    });
  });

  // Prevent empty submission
  form.addEventListener('submit', (e) => {
    if (!selected) {             
      e.preventDefault();
      return;
    }

    // Prevent more than one submission
    submitBtn.disabled = true;
    submitBtn.classList.add('disabled');

    // Clean previous inputs
    form.querySelectorAll('input[name="tests"]').forEach(i => i.remove());

    // Create hidden input with selected test
    const input = document.createElement('input');
    input.type  = 'hidden';
    input.name  = 'tests';
    input.value = selected.dataset.title.toLowerCase();
    form.appendChild(input);
  });
});


// Animation on scroll when visible
document.addEventListener("DOMContentLoaded", () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    document.querySelectorAll('.animate-fade-in, .animate-fade-left').forEach(el => {
        observer.observe(el);
    });
});

var swiper = new Swiper(".swiper", {
  effect: "coverflow",
  grabCursor: true,
  centeredSlides: true,
  initialSlide: 2,
  speed: 600,
  preventClicks: true,
  slidesPerView: "auto",
  coverflowEffect: {
      rotate: 0,
      stretch: 80,
      depth: 350,
      modifier: 1,
      slideShadows: true,

  },
});

let textTimeout;

function updateVisibleText() {
    const visibleSlide = document.querySelector('.swiper-slide-active');
    if (!visibleSlide) return;

    const currentQuestion = visibleSlide.getAttribute('data-question');

    const allTexts = document.querySelectorAll('.question-text');
    const currentTexts = document.querySelectorAll(`.question-text[data-for="${currentQuestion}"]`);

    if (!currentTexts.length) return;

    // If already visible
    const alreadyVisible = [...currentTexts].every(text => text.classList.contains('visible'));
    if (alreadyVisible) return;

    // Hide texts
    allTexts.forEach(text => text.classList.remove('visible'));

    // Cancell previous timeouts
    if (textTimeout) clearTimeout(textTimeout);

    // Show texts (with delay)
    textTimeout = setTimeout(() => {
        currentTexts.forEach(text => text.classList.add('visible'));
    }, 300);
}



// Observer that detects changes in slides
const observer = new MutationObserver(() => {
  updateVisibleText();
});

// Apply observer to each slide
document.querySelectorAll('.swiper-slide').forEach(slide => {
  observer.observe(slide, { attributes: true, attributeFilter: ['class'] });
});

// Open and close items accordion style section progress
const headers = document.querySelectorAll('.accordion-header');

headers.forEach(header => {
  header.addEventListener('click', () => {
    const content = header.nextElementSibling;
    const isOpen = content.classList.contains('open');

    document.querySelectorAll('.accordion-content').forEach(c => {
      c.style.maxHeight = null;
      c.classList.remove('open');
      c.previousElementSibling.classList.remove('active');
    });

    if (!isOpen) {
      content.classList.add('open');
      header.classList.add('active');
      content.style.maxHeight = content.scrollHeight + "px";
    }
  });
});



