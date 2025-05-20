document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("Confirm-Btn")
    .addEventListener("click", hideConfirmModal);
});
function showConfirmModal(text) {
  document.getElementById("confirmModal").style.display = "flex";
  const message = document.getElementById("ConfirmText");
  if (message) {
    message.textContent = text;
  }
}
function hideConfirmModal() {
  document.getElementById("confirmModal").style.display = "none";
}
