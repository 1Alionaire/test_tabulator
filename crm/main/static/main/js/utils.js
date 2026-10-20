
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

// ================ time "HH:MM:SS" → "HH:MM" ==============
function formatTimeHM(cell) {
  const value = cell.getValue();
  if (!value) return "";
  return String(value).slice(0, 5);
}


// =================== function for start typing in cell without doubleclick ===================
function bindTypeToEdit(table) {
  const holder = table.element.querySelector(".tabulator-tableholder");
  if (!holder) {
    console.error("tableholder не найден — вызов слишком рано");
    return;
  }

  holder.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select")) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key.length !== 1) return;

    const ranges = table.getRanges();
    if (!ranges.length) return;

    const cells = ranges[0].getCells();
    const cell = cells[0]?.[0] ?? cells[0];
    if (!cell) return;

    if (e.key === "Enter") {
        e.preventDefault();
        cell.navigateDown();
        return;
    }

      if (e.key === "F2") {
        e.preventDefault();
        cell.edit();               // правка без стирания
        return;
    }

    e.preventDefault();
    cell.edit();

    requestAnimationFrame(() => {
      const input = cell.getElement().querySelector("input, textarea");
      if (!input) return;
      input.value = e.key;
    });
  });
}

async function generatePaper(inputURL) {
  try {
    const resp = await fetch(inputURL);
    if (!resp.ok) {
      const data = await resp.json();
      throw new Error(data.error);
    }

    // Имя файла из Content-Disposition, если сервер его прислал
    const cd = resp.headers.get("Content-Disposition") || "";
    const match = cd.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : "Invoice.pdf";

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function normalizeTime(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return "";
  if (TIME_RE.test(s)) return s;

  const digits = s.replace(/\D/g, "");
  let h, m;

  if (digits.length <= 2) {          // "9" → 09:00, "14" → 14:00
    h = digits.padStart(2, "0");
    m = "00";
  } else if (digits.length === 3) {  // "930" → 09:30
    h = `0${digits[0]}`;
    m = digits.slice(1);
  } else if (digits.length === 4) {  // "1430" → 14:30
    h = digits.slice(0, 2);
    m = digits.slice(2);
  } else {
    return null;
  }

  const result = `${h}:${m}`;
  return TIME_RE.test(result) ? result : null;
}

function tabulatorTimeEditor(cell, onRendered, success, cancel) {
  const input = document.createElement("input");
  input.type = "text";
  const raw = cell.getValue();
  input.value = raw ? String(raw).slice(0, 5) : ""; 
  // input.value = cell.getValue() ?? "";
  input.placeholder = "HH:MM";
  input.inputMode = "numeric";
  input.style.cssText =
    "width:100%;height:100%;box-sizing:border-box;border:none;outline:none;" +
    "padding:0 6px;background:transparent;text-align:inherit;font:inherit;color:inherit;";

  let finished = false;

  function commit() {
    if (finished) return;
    const value = normalizeTime(input.value);
    if (value === null) {
      finished = true;
      return cancel();
    }
    finished = true;
    success(value);
  }
    // Позволяем мышкой переставлять курсор внутри текста
    input.addEventListener("mousedown", (event) => {
        event.stopPropagation();
    });

  input.addEventListener("click", (event) => {
        event.stopPropagation();
    });


  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      e.stopImmediatePropagation();
      commit();
      const nextRow = cell.getRow().getNextRow();
      if (nextRow) {
        requestAnimationFrame(() => nextRow.getCell(cell.getField()).edit());
      }
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopImmediatePropagation();
      finished = true;
      cancel();
    }
  });

  input.addEventListener("blur", commit);

  onRendered(() => {
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });

  return input;
}

// ===================== Checking fresh rows in middle of table for replacing whole table
function checkNewRows(inputTable) {
  let freshCell = null //init variable 
  const data = inputTable.getRows(); // parse whole table
  for (row of data) {   // going through table
    if (!row.getData().id) { // fresh table doesnt have "id" value
      freshCell = row.getPosition() // taking position of fresh cell and put in var
    }
    if (row.getData().id && freshCell) // if next cell has "id" value and we already have fresh cell
    {
      return true;
    }
  }
  return false;
}