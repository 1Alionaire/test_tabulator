
document.querySelectorAll(".dropdown-toggle").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.stopPropagation(); // чтобы обработчик на document не закрыл сразу же
    btn.parentElement.classList.toggle("open");
  });
});

// закрытие при клике вне меню
document.addEventListener("click", () => {
  document
    .querySelectorAll(".dropdown.open")
    .forEach((d) => d.classList.remove("open"));
});

function isEmpty(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === "number") return Number.isNaN(value);
  if (Array.isArray(value)) return value.length === 0;

  const s = String(value).trim();
  return s === "" || s === "null" || s === "undefined" || s === "NaN" || s === "None";
}

// ================ show notification ==============
function showToast(message, type = "info", duration = 3000) {
  const container = document.getElementById("toast-container");

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message; // textContent, а не innerHTML —
  // сообщения с сервера могут содержать HTML/XSS

  container.appendChild(toast);

  // Элемент только что вставлен со стилями opacity:0.
  // Если сразу навесить .show, браузер объединит оба состояния в один пересчёт
  // и transition не сработает. requestAnimationFrame даёт браузеру
  // отрисовать начальное состояние, и только потом меняем классы.
  requestAnimationFrame(() => toast.classList.add("show"));

  setTimeout(() => {
    toast.classList.remove("show");
    // ждём окончания transition, потом удаляем узел из DOM
    toast.addEventListener("transitionend", () => toast.remove(), {
      once: true,
    });
  }, duration);
}

// ================ show error from failed fetch response ==============
async function showResponseError(response) {
  // сервер отдаёт {"error": "..."}; если тело не JSON (например, HTML-страница 500) — показываем код
  const body = await response.json().catch(() => ({}));
  showToast(`Error: ${body.error ?? response.status}`, "error");
}

// ================= custom function for input tabulator ================
function tabulatorTextEditor(cell, onRendered, success, cancel, editorParams) {
    const input = document.createElement("input");

    input.type = "text";
    input.value = cell.getValue() ?? "";

    input.style.width = "100%";
    input.style.height = "100%";
    input.style.boxSizing = "border-box";
    input.style.padding = "4px";

    let finished = false;

    onRendered(function () {
        requestAnimationFrame(() => {
            input.focus();

            const end = input.value.length;
            input.setSelectionRange(end, end);
        });
    });

    // Позволяем мышкой переставлять курсор внутри текста
    input.addEventListener("mousedown", (event) => {
        event.stopPropagation();
    });

    input.addEventListener("click", (event) => {
        event.stopPropagation();
    });

    input.addEventListener("keydown", function (e) {

        if (e.key === "Enter") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;

            // сохраняем значение в Tabulator
            const accepted = success(input.value);

            // например, validation не прошла
            if (accepted === false) {
                finished = false;
                return;
            }

            // переходим в ячейку ниже
            setTimeout(function () {
                cell.navigateDown();
            }, 0);
        }

        if (e.key === "Escape") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;
            cancel();
        }
    });

    // если пользователь кликнул мышкой вне ячейки —
    // тоже сохраняем значение
    input.addEventListener("blur", function () {
        if (!finished) {
            finished = true;
            success(input.value);
        }
    });

    return input;
}

// ================= custom function for input tabulator ================
function tabulatorNumberEditor(cell, onRendered, success, cancel, editorParams) {
    const input = document.createElement("input");

    input.type = "number";
    input.value = cell.getValue() ?? "";

    input.style.width = "100%";
    input.style.height = "100%";
    input.style.boxSizing = "border-box";
    input.style.padding = "4px";

    let finished = false;

    onRendered(function () {
        input.focus();
        input.select();
    });

    // Позволяем мышкой переставлять курсор внутри текста
    input.addEventListener("mousedown", (event) => {
        event.stopPropagation();
    });

    input.addEventListener("click", (event) => {
        event.stopPropagation();
    });

    input.addEventListener("keydown", function (e) {

        if (e.key === "Enter") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;

            // сохраняем значение в Tabulator
            const accepted = success(input.value);

            // например, validation не прошла
            if (accepted === false) {
                finished = false;
                return;
            }

            // переходим в ячейку ниже
            setTimeout(function () {
                cell.navigateDown();
            }, 0);
        }

        if (e.key === "Escape") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;
            cancel();
        }
    });

    // если пользователь кликнул мышкой вне ячейки —
    // тоже сохраняем значение
    input.addEventListener("blur", function () {
        if (!finished) {
            finished = true;
            success(input.value);
        }
    });

    return input;
}

// ================ date "YYYY-MM-DD" → "MM-DD-YYYY" ==============
function formatDateMDY(cell) {
  const value = cell.getValue();
  if (!value) return "";
  const [year, month, day] = value.split("-");
  return `${month}-${day}-${year}`;
}