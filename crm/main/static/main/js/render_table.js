
// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

function isEmpty(inputString) {
  if (inputString == undefined || inputString == 'undefined' || 
    inputString == null || inputString == 'null' || 
    inputString == NaN ||  inputString == 'NaN'
  ) {
    return true
  } 
  else {
    return false
  }
};

// ==================== Open Filter Tab ====================
const filterPanel = document.getElementById("main-section-filter");

document.getElementById("main-menu-filter-toggle").addEventListener("click", function (e) {
    filterPanel.classList.toggle('invisible');
    filterPanel.classList.toggle('visible-flex');
});

// ==================== Generate table ====================
const ORIGINALS = new Map();
let table;
const deletedIds = new Set();

function onlyOnCreate(cell) {
  return cell.getRow().getData()._isNew === true;
}

function checkNOBType(cell) {
  if (cell.getRow().getData().sample_type_id == '3' || cell.getRow().getData().sample_type_id == '4') return true
}

(async () => { 
  const response = await fetch(URLS.tableOptionsGetURL);
  const statusOptions = await response.json();

     table = new Tabulator("#main-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        history:true,
        height: "100%",
        width: "100%", 
        layout:"fitColumns",
        editTriggerEvent: "click",
        ajaxURL: URLS.mainProjectGetURL,
        pagination:"local",
        paginationSize: 200,
        paginationSizeSelector:[100, 200, 300],
        selectableRows:true, 
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
              width: 80, 
              editor:"input", 
              headerSort: false
            },
            {
              title:"Date", 
              field:"date_registered", 
              editor: "date", 
              formatter:"date", 
              width:80, 
              headerSort: false
            },
            {
              title:"Time", 
              field:"time_registered", 
              editor: "time", 
              formatter:"time",
              width:80 , 
              headerSort: false 
            },
            {
              title: "Company",
              field: "company_id",
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
              editor:"input", 
              headerSort: false
            },
            {
              title:"Project Address", 
              field:"project_address", 
              hozAlign:"center", width:400, 
              editor:"input", 
              headerSort: false 
            },
            {
              title: "Type Analysis",
              field: "sample_type_id",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['sample_type'].map(o => [o.value, o.label])),
              editor: "list",
              editable: onlyOnCreate,
              editorParams: { values: statusOptions['sample_type']},
              width : 100,
              headerSort: false 
            },
            {
              title:"Amount Samples", 
              field:"number_samples", 
              hozAlign:"center", 
              width:100, 
              editor:"number", 
              headerSort: false,
              editorParams: {
                min: 0,
                step: 1,
              },
              validator: ["required", "min:0", "integer"],
            },
            {
              title: "Turn Around Time",
              field: "turn_around_time_id",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['turn_around_time'].map(o => [o.value, o.label])),
              editor: "list",
              editorParams: { values: statusOptions['turn_around_time'] },
              width: 80,
              headerSort: false 
            },
            {
              title:"NOB Amount Samples", 
              field:"nob_number_samples", 
              hozAlign:"center", 
              width:100, 
              editor: "number", 
              width:80, 
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
              field: "status_id",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['status'].map(o => [o.value, o.label])),
              width: 80,
              headerSort: false 
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
              headerSort: false
            },
            {
              title:"Technician", 
              field:"technician", 
              hozAlign:"center", 
              width:100, 
              editor:"input", 
              editable:true, 
              headerSort: false 
            },
            {
              title:"Comment", 
              field:"comment", 
              hozAlign:"center", 
              width:100, 
              editor:"input", 
              headerSort: false 
            },

          ],
      });
  })();


  // =================== Refresh table ===================
document.getElementById("main-menu-refresh-toggle").addEventListener("click", function() {
  const changes = collectChanges(); // collecting all changes
  const hasChanges = changes.updated.length || changes.created.length || changes.deleted.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  table.setData(URLS.mainProjectGetURL);
});

  // =================== Create new row ===================
document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

  // =================== Save ===================
function collectChanges() {
  const updatedData = {};
  const createdData = {};

  if (deletedIds && !confirm("Projects will be deleted. Continue?")) return

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
    console.log('no data?')
    return;
  }
  // saveBtn.disabled = true;
  try {
    const res = await fetch(URLS.mainProjectUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(changes),
    });

    if (res.status === 422) {
      showErrors((await res.json()).errors);
      return;                                   // флаги не снимаем — правки живы
    }
    if (!res.ok) {
      console.error("STATUS:", res.status, "BODY:", await res.text());
      return;
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
    showToast(`Error: ${res.error}`, "error");
    console.log(e)
  } finally {
    deletedIds.clear();
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
  sampleType = result['sample_type'];
  fillSelect("#filter-input-company", companies);
  fillSelect("#filter-input-status", statuses);
  fillSelect("#filter-input-turn-around-time", turnAroundTime);
  fillSelect("#filter-input-sample-type", sampleType);
};

initFilterPanel();

function applyFilters() {
  
  const filters = [];

  const filterDateStart = document.querySelector("#filter-input-date-start").value;
  if (filterDateStart) filters.push({ field: "date_registered", type: ">=", value: filterDateStart });

  const filterDateEnd = document.querySelector("#filter-input-date-end").value;
  if (filterDateEnd) filters.push({ field: "date_registered", type: "<=", value: filterDateEnd });

  const filterCompany = document.querySelector("#filter-input-company").value;
  if (filterCompany) filters.push({ field: "company_id", type: "=", value: filterCompany });

  // Status of work
  const filterStatus = document.querySelector("#filter-input-status");
  const filterStatusSelectedValues = Array.from(filterStatus.selectedOptions)
    .map((option) => parseInt(option.value, 10));

  if (filterStatusSelectedValues.length) {
    filters.push({ field: "status_id", type: "in", value: filterStatusSelectedValues });
  }

  // Sample type 
  const filterSampleType = document.querySelector("#filter-input-sample-type");
  const filterSampleTypeSelectedValues = Array.from(filterSampleType.selectedOptions)
    .map((option) => parseInt(option.value, 10));

  if (filterSampleTypeSelectedValues.length) {
    filters.push({ field: "sample_type_id", type: "in", value: filterSampleTypeSelectedValues });
  }

  // Turn around time
  const filterTurnAroundTime = document.querySelector("#filter-input-turn-around-time");
  const filterTurnAroundTimeSelectedValues = Array.from(filterTurnAroundTime.selectedOptions)
    .map((option) => parseInt(option.value, 10));

  if (filterTurnAroundTimeSelectedValues.length) {
    filters.push({ field: "turn_around_time_id", type: "in", value: filterTurnAroundTimeSelectedValues });
  }

  const filterProjectName = document.querySelector("#filter-input-project-name").value;
  if (filterProjectName) filters.push({ field: "project_name", type: "like", value: filterProjectName });

  const filterProjectAddress = document.querySelector("#filter-input-project-address").value;
  if (filterProjectAddress) filters.push({ field: "project_address", type: "like", value: filterProjectAddress });

  table.setFilter(filters);   // пустой массив = снять всё
}

document.getElementById("filter-panel-apply-button").addEventListener("click", applyFilters);

document.getElementById("filter-panel-reset-filter-button").addEventListener("click", function() {
  table.setFilter(); 
    });
    
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

// ================ show notification ==============
function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;   // textContent, а не innerHTML —
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
        toast.addEventListener("transitionend", () => toast.remove(), { once: true });
    }, duration);
}

