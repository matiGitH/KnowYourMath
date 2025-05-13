console.log("JavaScript is working!");

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
            header.classList.add('hidden');
        } else {
            header.classList.remove('hidden');
        }

        lastScroll = currentScroll;
    });
});

// Algo del form
const panels = document.querySelectorAll('.test-panel');
const submitBtn = document.getElementById('submitBtn');
const form = document.querySelector('.tests-select');
let selected = new Set();

panels.forEach(panel => {
  panel.addEventListener('click', () => {
    const test = panel.dataset.title;
    panel.classList.toggle('selected');

    if (selected.has(test)) {
      selected.delete(test);
    } else {
      selected.add(test);
    }

    submitBtn.classList.toggle('enabled', selected.size > 0);
  });
});

form.addEventListener('submit', (e) => {
  if (selected.size === 0) {
    e.preventDefault(); // No dejar enviar si no hay tests
    return;
  }

  // Limpiar inputs anteriores
  document.querySelectorAll('input[name="tests"]').forEach(input => input.remove());

  // Crear inputs hidden por cada test seleccionado
  selected.forEach(test => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'tests';  // esto lo vas a recibir en Flask con request.form.getlist('tests')
    input.value = test.toLowerCase();
    form.appendChild(input);
  });

  // No hay preventDefault acá, así se envía el form normalmente
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
    console.log(`Ahora está la pregunta ${currentQuestion}`);

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


  


// // BACKGROUND-AWARE TEXT

// window.addEventListener("load", () => {
//     const canvas = document.getElementById("textCanvas");
//     const ctx = canvas.getContext("2d");
  
//     canvas.width = window.innerWidth;
//     canvas.height = window.innerHeight;
  
//     // Dibuja primero el fondo (imitamos el CSS)
//     const halfWidth = canvas.width / 2;
//     ctx.fillStyle = "#ff6200";
//     ctx.fillRect(0, 0, halfWidth, canvas.height);
  
//     ctx.fillStyle = "#ffffff";
//     ctx.fillRect(halfWidth, 0, halfWidth, canvas.height);
  
//     // Luego escribimos el texto pixel a pixel con color según fondo
//     const text = "Texto dinámico";
//     const fontSize = 80;
//     ctx.font = `${fontSize}px sans-serif`;
  
//     const textWidth = ctx.measureText(text).width;
//     const x = (canvas.width - textWidth) / 2;
//     const y = canvas.height / 2 + fontSize / 3;
  
//     // Creamos una imagen temporal con el texto en negro
//     const tempCanvas = document.createElement("canvas");
//     tempCanvas.width = canvas.width;
//     tempCanvas.height = canvas.height;
//     const tempCtx = tempCanvas.getContext("2d");
  
//     tempCtx.font = ctx.font;
//     tempCtx.fillStyle = "black";
//     tempCtx.fillText(text, x, y);
  
//     const textImageData = tempCtx.getImageData(0, 0, canvas.width, canvas.height);
//     const pixels = textImageData.data;
  
//     for (let i = 0; i < pixels.length; i += 4) {
//       const alpha = pixels[i + 3];
//       if (alpha > 128) { // si el pixel es parte del texto
//         const px = (i / 4) % canvas.width;
//         // Si el pixel está sobre el fondo blanco (derecha), pintamos naranja
//         if (px > halfWidth) {
//           pixels[i] = 255;   // rojo
//           pixels[i + 1] = 98;  // verde
//           pixels[i + 2] = 0;   // azul
//         } else {
//           // Si está sobre el fondo naranja, pintamos oscuro
//           pixels[i] = 28;
//           pixels[i + 1] = 29;
//           pixels[i + 2] = 30;
//         }
//       }
//     }
  
//     ctx.putImageData(textImageData, 0, 0);
//   });
  