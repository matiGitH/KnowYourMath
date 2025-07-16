// Ask for confirmation for skipping
document.addEventListener("DOMContentLoaded", () => {
  const skipBtn   = document.getElementById("skipBtn");
  const overlay   = document.getElementById("customAlert");
  const cancelBtn = document.getElementById("cancelSkip");

  // Show alert
  skipBtn.addEventListener("click", () => {
    overlay.classList.remove("hidden");
  });

  // Cancel button
  cancelBtn.addEventListener("click", () => {
    overlay.classList.add("hidden");
  });

  // Close if clicked elsewhere
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.classList.add("hidden");
    }
  });
});


function handleClick(clickedBtn) {
  const formId = clickedBtn.getAttribute("form");
  const form = formId ? document.getElementById(formId) : clickedBtn.closest("form");

  if (form && !form.checkValidity()) {
    return;
  }

  setTimeout(() => {
    const buttons = document.querySelectorAll('.action-btn');
    buttons.forEach(btn => {
      btn.disabled = true;
      btn.classList.add('disabled');
    });
  }, 0);
}
