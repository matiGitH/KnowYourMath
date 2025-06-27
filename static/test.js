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
