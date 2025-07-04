document.addEventListener("DOMContentLoaded", () => {
  const app = document.getElementById("app");
  const isCorrect = app.dataset.correct === "true";

  if (isCorrect) {
    const successSound = new Audio("/static/sounds/success.mp3");
    successSound.volume = 0.4;
    successSound.play();

    // Confetti
    const count = 200;
    const defaults = {
      origin: { y: 0.7 }
    };

    function fire(particleRatio, opts) {
      confetti({
        ...defaults,
        ...opts,
        particleCount: Math.floor(count * particleRatio)
      });
    }

    fire(0.25, {
      spread: 26,
      startVelocity: 55,
    });
    fire(0.2, {
      spread: 60,
    });
    fire(0.35, {
      spread: 100,
      decay: 0.91,
      scalar: 0.8
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 25,
      decay: 0.92,
      scalar: 1.2
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 45,
    });

  } else {
    const errorSound = new Audio("/static/sounds/error.mp3");
    errorSound.volume = 0.4;
    errorSound.play();

    document.body.classList.add("shake");
  }
});

function handleClick(clickedBtn) {
  const formId = clickedBtn.getAttribute("form");
  const form = formId ? document.getElementById(formId) : clickedBtn.closest("form");

  if (form && !form.checkValidity()) {
    // No hacer nada si el formulario no es válido
    return;
  }

  // Esperar un ciclo para permitir que el navegador procese el submit primero
  setTimeout(() => {
    const buttons = document.querySelectorAll('.action-btn');
    buttons.forEach(btn => {
      btn.disabled = true;
      btn.classList.add('disabled');
    });
  }, 0);
}
