document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("Confirm-Btn")
    .addEventListener("click", hideConfirmModal);
});
let confirmCallback = null;
function showConfirmModal(text, callback = null) {
  document.getElementById("confirmModal").style.display = "flex";
  const message = document.getElementById("ConfirmText");
  if (message) {
    message.textContent = text;
  }
  confirmCallback = callback;
}

function hideConfirmModal() {
  document.getElementById("confirmModal").style.display = "none";

  if (typeof confirmCallback === "function") {
    confirmCallback();
    confirmCallback = null;
  }
}
