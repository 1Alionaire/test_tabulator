
// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

// ==================== Open Filter Tab ====================
const filterPanel = document.getElementById("main-section-filter");

document.getElementById("main-menu-filter-toggle").addEventListener("click", function (e) {
    filterPanel.classList.toggle('invisible');
    filterPanel.classList.toggle('visible-flex');
});

// ==================== Generate table ====================
const ORIGINALS = new Map();
let table;

function onlyOnCreate(cell) {
  return cell.getRow().getData()._isNew === true;
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
              sorter: "string"
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
              editable: onlyOnCreate 
            },
            {
              title:"Date", 
              field:"date_registered", 
              editor: "date", 
              formatter:"date", 
              width:80 
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
              field: "sample_type",
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
              field: "turn_around_time",
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
            },
            {
              title: "Status",
              field: "status",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['status'].map(o => [o.value, o.label])),
              width: 80,
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
  table.setData(URLS.mainProjectGetURL);
    });

  // =================== Create new row ===================
document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

  // =================== Save ===================
function collectChanges() {
  const byRow = new Map();

  for (const cell of table.getEditedCells()) {
    const data = cell.getRow()?.getData();
    if (!data || !data.lab_id) continue;

    const labId = String(data.lab_id);          // единый тип ключа

    let entry = byRow.get(labId);
    if (!entry) {
      entry = {lab_id: labId, fields: {}, version: ORIGINALS.get(labId)};
      byRow.set(labId, entry);
    }
    entry.fields[cell.getField()] = cell.getValue();
  }

  return [...byRow.values()];
}

document.getElementById("main-menu-save-toggle").addEventListener("click", saveChanges);

async function saveChanges() {
  const changes = collectChanges();
  console.log(changes)
  if (!changes.length) return;

  // saveBtn.disabled = true;
  try {
    const res = await fetch(URLS.mainProjectUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify({changes}),
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
  } catch (e) {
    alert("Не удалось сохранить. Правки остались в таблице.");
    console.log(e)
  } finally {
  }
};

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
  if (filterCompany) filters.push({ field: "company", type: "=", value: filterCompany });

  const filterStatus = document.querySelector("#filter-input-status").value;
  if (filterStatus) filters.push({ field: "status", type: "=", value: filterStatus });

  const filterTurnAroundTime = document.querySelector("#filter-input-turn-around-time").value;
  if (filterTurnAroundTime) filters.push({ field: "turn_around_time", type: "=", value: filterTurnAroundTime });
  // 
  const filterSampleType = document.querySelector("#filter-input-sample-type").value;
  if (filterSampleType) filters.push({ field: "sample_type", type: "=", value: filterSampleType });

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
    
