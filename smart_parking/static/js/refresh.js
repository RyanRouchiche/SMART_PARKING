import { scheduleStaticTokenRefresh } from "./utils.js";
document.addEventListener("DOMContentLoaded", async function () {
  console.log("DOC HERE");
  await scheduleStaticTokenRefresh();
});
