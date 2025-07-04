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

const panels = document.querySelectorAll('.test-panel');
const submitBtn = document.getElementById('submitBtn');
const form = document.querySelector('.tests-select');
let selected = null;

// Verificación previa
const LOGGED_IN = document.getElementById('app').dataset.loggedIn === "true";

document.addEventListener("DOMContentLoaded", () => {
  const alertBox = document.getElementById("customAlert");
  const cancelBtn = document.getElementById("cancelAlert");

  cancelBtn.addEventListener("click", () => {
    alertBox.classList.add("hidden");
  });

  panels.forEach(panel => {
    panel.addEventListener('click', () => {
      if (!LOGGED_IN) {
        alertBox.classList.remove("hidden"); // Mostrar alerta
        return;
      }

      const test = panel.dataset.title;

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

  form.addEventListener('submit', (e) => {
    if (!selected) {
      e.preventDefault();
      return;
    }

    // Prevent múltiple submits
    submitBtn.disabled = true;
    submitBtn.classList.add('disabled');

    // Eliminate previous inputs
    document.querySelectorAll('input[name="tests"]').forEach(input => input.remove());

    // Create hidden input
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'tests';
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
                observer.unobserve(entry.target); // solo una vez
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

    // Verificamos si ya están visibles
    const alreadyVisible = [...currentTexts].every(text => text.classList.contains('visible'));
    if (alreadyVisible) return;

    // Ocultamos todos los textos inmediatamente
    allTexts.forEach(text => text.classList.remove('visible'));

    // Cancelamos cualquier timeout anterior
    if (textTimeout) clearTimeout(textTimeout);

    // Mostramos los textos correspondientes con delay
    textTimeout = setTimeout(() => {
        currentTexts.forEach(text => text.classList.add('visible'));
    }, 300);
}



// Observador para detectar cambios de clase en slides (cuando cambia la activa)
const observer = new MutationObserver(() => {
  updateVisibleText();
});

// Aplicamos el observador a todos los slides
document.querySelectorAll('.swiper-slide').forEach(slide => {
  observer.observe(slide, { attributes: true, attributeFilter: ['class'] });
});

// Open and close items accordion style section progress
const headers = document.querySelectorAll('.accordion-header');

headers.forEach(header => {
  header.addEventListener('click', () => {
    const content = header.nextElementSibling;
    const isOpen = content.classList.contains('open');

    // Cerrar todos
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



