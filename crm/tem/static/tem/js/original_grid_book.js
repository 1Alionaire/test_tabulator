// ==================== Generate table ====================

// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');


const ORIGINALS = new Map();
let table;

const updatedData = new Map();

function markDirty(row, field) {
  const id = row.getData().id;
  if (!updatedData.has(id)) updatedData.set(id, {});
  updatedData.get(id)[field] = row.getData()[field];
  updatedData.get(id)['version'] = row.getData()['version'];
}

(async () => { 
     table = new Tabulator("#main-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        history:true, // history for undo/redo
        height: "100%", // height
        width: "100%",  // width 
        layout:"fitColumns", // layout 
        editTriggerEvent: "click", // edit trigger for editing
        footerElement: '<span id="main-rows-loaded"></span>' +
          '<button type="button" id="main-load-more" class="tabulator-page">Load more</button>',
        selectableRows:true,  
        columnDefaults: {
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle",
        },
        columns:[
          {
              title: "id", 
              field: "id", 
              visible: false, 
            },
            {
              title: "position",  
              field: "position", 
              visible: false, 
              sorter: "string"
            },
            {
              title:"year", 
              field:"year", 
              width: 80, 
              editable: false, 
              headerSort: false,
              
            },
            {
              title:"Grid Box", 
              field:"grid_box", 
              editable: false, 
              width:120,
              formatter: function (cell) {
                const row = cell.getRow();
                const prev = row.getPrevRow();
                const el = cell.getElement();
                const value = cell.getValue();

                const isRepeat = prev && prev.getData().grid_box === value && value;

                el.classList.toggle("merged-continue", Boolean(isRepeat));
                return isRepeat ? "" : (value ?? "");
              },
            },
            {
              title:"Grid ID I", 
              field:"grid_id_1", 
              editable: false, 
              width:120, 
            },
            {
              title:"Grid ID II", 
              field:"grid_id_2", 
              editable: false, 
              width:120, 
            },
            {
              title:"Project", 
              field:"plm_tem_project",
              editor: tabulatorTextEditor,
              width:120, 
            },
            {
              title:"Sample", 
              field:"plm_tem_sample",
              editor: tabulatorTextEditor,
              width:120, 
            },
          ],
      });

     table.on("cellEdited", (cell) => { // in case cell edited
        if (cell.getRow().getData().id) { // if sample exists
          markDirty(cell.getRow(), cell.getField()); // mark cell dirty
        }
      });

     table.on("tableBuilt", () => {
       loadFirstPage();
     });

     // infinite scroll: подгружаем следующую страницу, когда до низа осталось меньше SCROLL_LOAD_MARGIN
     table.on("scrollVertical", (top) => {
       const holder = table.element.querySelector(".tabulator-tableholder");
       if (top + holder.clientHeight >= holder.scrollHeight - SCROLL_LOAD_MARGIN) loadNextPage();
     });
  })();

// ==================== Cursor pagination ====================
// API отдаёт {next, previous, results}; next — готовый URL следующей страницы (курсор + фильтры)
const PAGE_SIZE = 200;
const SCROLL_LOAD_MARGIN = 300;
let currentQuery = '';   // фильтры текущего набора данных
let nextPageURL = null;  // null — последняя страница уже загружена
let pageLoading = false;
let loadGeneration = 0;  // ответы на запросы до смены фильтров отбрасываем


async function fetchPage(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`load failed (${res.status})`);
  return res.json();
}

function updatePageFooter() {
  document.getElementById("main-rows-loaded").textContent =
    `Loaded: ${table.getDataCount()}${nextPageURL ? '' : ' (all)'}`;
  document.getElementById("main-load-more").style.display = nextPageURL ? '' : 'none';
}

async function loadFirstPage(query = currentQuery) {
  const generation = ++loadGeneration;
  currentQuery = query;
  const params = new URLSearchParams(query);
  params.set('page_size', PAGE_SIZE);
  try {
    const page = await fetchPage(`${URLS.temOriginalGridBoxGetURL}?${params}`);
    if (generation !== loadGeneration) return;
    nextPageURL = page.next;
    await table.setData(page.results);
    updatePageFooter();
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
}

async function loadNextPage() {
  if (!nextPageURL || pageLoading) return;
  pageLoading = true;
  const generation = loadGeneration;
  try {
    const page = await fetchPage(nextPageURL);
    if (generation !== loadGeneration) return;
    nextPageURL = page.next;
    // строка могла сместиться между запросами (сменили lab_id) — дубли не добавляем
    const loadedIds = new Set(table.getData().map(r => r.id));
    const rows = page.results.filter(r => !loadedIds.has(r.id));
    if (rows.length) {
      // addData, а не setData — несохранённые правки в уже загруженных строках остаются
      await table.addData(rows, false);
      // addData пишет каждую строку в историю — без очистки Undo удалял бы подгруженные строки
      table.clearHistory();
    }
    updatePageFooter();
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  } finally {
    pageLoading = false;
  }
}

document.getElementById("main-menu-save-toggle").addEventListener("click", saveChanges);

async function saveChanges() {
  const payload = Array.from(updatedData, ([id, fields]) => ({
      id: Number(id),
      ...fields,
    }));

  if (!payload.length) {
    showToast("No changes to save", "info");
    return;
  }

  try {
    const res = await fetch(URLS.temOriginalGridBoxUpdateURL, {
      method: "PATCH",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      await showResponseError(res);
      return;                                   // флаги не снимаем — правки живы
    }

    updatedData.clear()

    const resultJSON = await res.json();

    let resultMessage = ''
    if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
    showToast(`Table Saved: ${resultMessage}`, "success");

    } catch (e) {
      if (e.status === 409) {
        showResponseError(e.message, "error");
      } else {
        showToast(`Error: ${e.message}`, "error");
      }
    } finally {
      loadFirstPage();
    }
};

document.getElementById("main-menu-create-toggle").addEventListener("click", async () => {
    const res = await fetch(URLS.temOriginalGridBoxUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
    });
    saveChanges();
    loadFirstPage();
  }
);

