document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            const button = form.querySelector("button[type='submit']");
            if (button && !form.action.includes("delete-user")) {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = "Working…";
            }
        });
    });
});
