// ==================== Project info ====================
document.getElementById("project-info-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  try {
    const response = await fetch(this.action, {
      method: "POST",
      headers: {"X-CSRFToken": csrftoken},
      body: new FormData(this),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;
    }

    showToast("Project saved", "success");
  }
  catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
});
