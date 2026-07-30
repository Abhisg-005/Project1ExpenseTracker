document.addEventListener("DOMContentLoaded", () => {
  const amountInput = document.getElementById("amount");
  if (amountInput) {
    amountInput.focus();
  }

  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.remove("show");
      setTimeout(() => alert.remove(), 200);
    }, 3500);
  });
});
