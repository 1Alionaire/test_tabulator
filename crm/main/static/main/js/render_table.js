
// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

// ==================== Open Filter Tab ====================
const filterPanel = document.getElementById("main-section-filter");

document.getElementById("main-menu-filter-toggle").addEventListener("click", function (e) {
    filterPanel.classList.toggle('invisible'); //add visible class
    filterPanel.classList.toggle('visible-flex'); //add invisible class
});

// ==================== Generate table ====================
const ORIGINALS = new Map();
let table;
const deletedIds = new Set();

function onlyOnCreate(cell) {
  return cell.getRow().getData()._isNew === true;
}

function checkNOBType(cell) {
  if (cell.getRow().getData().project_type === '3' || cell.getRow().getData().project_type === '4') return true
}

function checkCOCFile(cell) {
  if (cell.getRow().getData().has_coc === true) {
    return 'Check'
  }
  else {
    return 'Upload'
  }
}

(async () => { 
  const response = await fetch(URLS.tableOptionsGetURL); // parse all options from database
  const statusOptions = await response.json(); //collect into status dict

     table = new Tabulator("#main-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        rowFormatter: function (row) {
          row.getElement().classList.toggle("row-overdue", row.getData().is_overdue === true);
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
              title: "lab_id_sort",  
              field: "lab_id_sort", 
              visible: false, 
              sorter: "string"
            },

            {
              title:"Lab ID", 
              field:"lab_id", 
              width: 100, 
              editor:"input", 
              headerSort: false,
              
            },
            {
              title:"Date", 
              field:"date_registered", 
              editor: "date", 
              formatter: formatDateMDY,  
              width:120, 
              headerSort: false,
              
            },
            {
              title:"Time",
              field:"time_registered",
              width: 80,
              formatter: formatTimeHM,
              editor: tabulatorTimeEditor,
            },
            {
              title: "Company", 
              field: "company",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['company'].map(o => [o.value, o.label])),
              editor: "list",
              editable: onlyOnCreate,
              editorParams: { values: statusOptions['company'] },
              headerSort: false,
              width: 150,
              
            },
            {
              title:"Project Name",  
              field:"project_name", 
              width:400, 
              editor: tabulatorTextEditor, 
              headerSort: false,
              
            },
            {
              title:"Project Address",  
              field:"project_address", 
              hozAlign:"center", width:400, 
              editor: tabulatorTextEditor, 
              headerSort: false,
              
            },
            {
              title: "Type<br>Analysis", 
              field: "project_type",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['project_type'].map(o => [o.value, o.label])),
              editor: "list",
              editable: onlyOnCreate,
              editorParams: { values: statusOptions['project_type']},
              width : 100,
              headerSort: false, 
              
            },
            {
              title:"Samples", 
              field:"number_samples", 
              width: 75, 
              editor:"number", 
              headerSort: false,
              editorParams: {
                min: 0,
                step: 1,
              },
              validator: ["required", "min:0", "integer"],
              
              },
            {
              title: "TurnAround<br>Time",
              field: "turn_around_time",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['turn_around_time'].map(o => [o.value, o.label])),
              editor: "list",
              editorParams: { values: statusOptions['turn_around_time'] },
              width: 90,
              headerSort: false,
              
            },
            {
              title:"NOB<br>Samples", 
              field:"nob_number_samples", 
              editor: "number", 
              width:75, 
              headerSort: false,
              editorParams: {
                min: 0,
                step: 1,
              },
              validator: ["required", "min:0", "integer"],
              editable: checkNOBType,
              
            },
            {
              title: "Status",
              field: "status",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['status'].map(o => [o.value, o.label])),
              width: 80,
              headerSort: false,
              
            },
            {
              title: "Link",
              field: "id",
              formatter: "link",
              formatterParams: {
                urlPrefix: "redirect/",
                target: "_blank",
                label: "Link",
              },
              headerSort: false,
            },
            {
              title:"Technician", 
              field:"technician", 
              width:100, 
              editor:"input", 
              editable:true, 
              headerSort: false,
            },
            {
              title:"Comment", 
              field:"comment", 
              width:100, 
              editor:"input", 
              headerSort: false,
            },
            {
              title: "COC File",
              field: "id",
              formatter: "link",
              formatterParams: {
                urlPrefix: "upload-coc/",
                target: "_blank",
                label: checkCOCFile,
              },
              headerSort: false,
              width: 70,
            },
            {
              title: 'Is Overdue',
              field : "is_overdue", 
              editable: false,
              visible: false,
            },
          ],
      });

     table.on("tableBuilt", () => {
       document.getElementById("main-load-more").addEventListener("click", loadNextPage);
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
    const page = await fetchPage(`${URLS.mainProjectGetURL}?${params}`);
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

  // =================== Refresh table ===================
document.getElementById("main-menu-refresh-toggle").addEventListener("click", function() {
  const changes = collectChanges(); // collecting all changes
  const hasChanges = changes.updated.length || changes.created.length || changes.deleted.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  loadFirstPage();
});

  // =================== Create new row ===================
document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

  // =================== Save ===================
function collectChanges() {
  const updatedData = {};
  const createdData = {};
  
  for (const cell of table.getEditedCells()) {  // going through all edited cells
    const data = cell.getRow()?.getData();  //parse data from whole row?
    
    if (!data || !data.lab_id) continue; // if we dont have data -> continue

    const labId = String(data.lab_id);          // единый тип ключа
    const systemId = String(data.id); 

    if (isEmpty(systemId)) {
      if (labId in createdData) {
        createdData[labId].fields[cell.getField()] = cell.getValue();
        }
      else {
        entry = {lab_id: labId, fields: {}, version: ORIGINALS.get(labId)};
        createdData[labId] = entry;
        createdData[labId].fields[cell.getField()] = cell.getValue();
      }
    }
    else {
      if (systemId in updatedData) {
        updatedData[systemId].fields[cell.getField()] = cell.getValue();
      }
      else {
        entry = {id: systemId, fields: {}, version: ORIGINALS.get(systemId)};
        updatedData[systemId] = entry;
        updatedData[systemId].fields[cell.getField()] = cell.getValue();
      }
    };
  }

    const result = {
      updated: Object.values(updatedData),
      created: Object.values(createdData),
      deleted: [...deletedIds]
    };
  return result;
}

document.getElementById("main-menu-save-toggle").addEventListener("click", saveChanges);

async function saveChanges() {
  const changes = collectChanges();
  if (!changes.updated.length && !changes.created.length && !changes.deleted.length) {
    return;
  }

  if (changes.deleted.length && !confirm("Projects will be deleted. Continue?")) return

  try {
    const res = await fetch(URLS.mainProjectUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(changes),
    });

    if (!res.ok) {
      await showResponseError(res);
      return;                                   // флаги не снимаем — правки живы
    }

    table.getEditedCells().forEach(cell => {
      cell.clearEdited();
      cell.getElement().classList.remove("dirty");
    });

    const resultJSON = await res.json();

    let resultMessage = ''
    if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
    if (resultJSON.created) {resultMessage += `Created: ${resultJSON.created}`};
    if (resultJSON.deleted) {resultMessage += `Deleted: ${resultJSON.deleted}`};
    console.log(resultMessage)
    showToast(`Table Saved: ${resultMessage}`, "success");


  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
    console.log(e)
  } finally {
    deletedIds.clear();
    loadFirstPage();
  }
};

window.addEventListener("unhandledrejection", (e) => {
  console.error("Необработанный промис:", e.reason);
});

//  ==================== Filter =================
function fillSelect(selector, items) {
  const select = document.querySelector(selector);
  select.innerHTML = '<option value="">— all —</option>';
  for (const item of items) {

    const opt = document.createElement("option");
    opt.value = item.value;
    opt.label = item.label;
    select.append(opt);
  }
}

async function initFilterPanel() {
  const response = await fetch(URLS.tableOptionsGetURL);
  const result = await response.json();
  companies = result['company'];
  statuses = result['status'];
  turnAroundTime = result['turn_around_time'];
  sampleType = result['project_type'];
  fillSelect("#filter-input-company", companies);
  fillSelect("#filter-input-status", statuses);
  fillSelect("#filter-input-turn-around-time", turnAroundTime);
  fillSelect("#filter-input-sample-type", sampleType);
};

initFilterPanel();

const form = document.getElementById('filter-form');



// document.getElementById("filter-panel-reset-filter-button").addEventListener("click", function() {
//   table.setFilter();
//     });
//
// ================== deleting rows =============

document.getElementById("main-menu-delete-toggle").addEventListener("click", function () {
  const rows = table.getSelectedRows();
  for (const row of rows ) {

    table.deleteRow(row.getIndex());
    deletedIds.add(row.getData().id);
    
  }
});

document.getElementById("main-menu-undo-toggle").addEventListener("click", function() {
  table.undo();
  deletedIds.clear();
    });

document.getElementById("main-menu-redo-toggle").addEventListener("click", function() {
  table.redo();
    });

document.getElementById("main-menu-test-toggle").addEventListener("click", function() {
  checkNOBType();
});

// const form = document.getElementById('filter-form');

// единственный источник правды для значений по умолчанию
function defaultFilters() {
  const year = new Date().getFullYear();
  return {
    date_registered__gte: `${year}-01-01`,
    date_registered__lte: `${year}-12-31`,
  };
}

function applyDefaults() {
  // 1. чистим все поля
  for (const el of form.elements) {
    if (!el.name) continue;                       // кнопки пропускаем
    if (el.tagName === 'SELECT') {
      for (const opt of el.options) opt.selected = false;
    } else {
      el.value = '';
    }
  }
  // 2. раскладываем дефолты
  for (const [name, value] of Object.entries(defaultFilters())) {
    const field = form.elements[name];
    if (field) field.value = value;
  }
}

function loadTable() {
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(form)) {
    if (value) params.append(key, value);
  }
  loadFirstPage(params);
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  loadTable();
});

document.getElementById('filter-reset').addEventListener('click', () => {
  applyDefaults();
  loadTable();
});


