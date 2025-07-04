// Ask for confirmation for skipping
document.addEventListener("DOMContentLoaded", () => {
    const skipBtn = document.getElementById("skipBtn");
    const alertBox = document.getElementById("customAlert");
    const cancelBtn = document.getElementById("cancelSkip");

    skipBtn.addEventListener("click", () => {
        alertBox.classList.remove("hidden");
    });

    cancelBtn.addEventListener("click", () => {
        alertBox.classList.add("hidden");
    });
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
