
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

function getLabId(cell) {
  return cell.getRow().getData().lab_id;
}

let table;

(async () => { 
    const response = await fetch(URLS.tableOptionsGetURL);
    const statusOptions = await response.json();

     table = new Tabulator("#plm-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        height: "100%",
        width: "100%", 
        layout:"fitColumns",
        editTriggerEvent: "click",
        ajaxURL: URLS.PLMProjectGetURL,
        pagination:"local",
        paginationSize: 200,
        paginationSizeSelector:[100, 200, 300],
        columnDefaults: {
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle",
          editable: false,
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
              field: "plm_project__id", 
              width: 100, 
              headerSort: false,
              formatter: "link",
              formatterParams: {
                urlPrefix: "detail/",
                target: "_blank",
                label: getLabId,
              },
            },
            {
              title:"Date", 
              field:"date_registered", 
              formatter:formatDateMDY, 
              width:110, 
              headerSort: false,
              
            },
            {
              title:"Time", 
              field:"time_registered", 
              formatter:"time",
              width:80 , 
              headerSort: false, 
              
            },
            {
              title: "Company",
              field: "company_id",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['company'].map(o => [o.value, o.label])),
              editorParams: { values: statusOptions['company'] },
              headerSort: false,
              width: 150,
              
            },
            {
              title:"Project Name", 
              field:"project_name", 
              width:400, 
              headerSort: false,
              
            },
            {
              title:"Project Address", 
              field:"project_address", 
              hozAlign:"center", width:400, 
              headerSort: false,
              
            },
            {
              title: "Type<br>Analysis",
              field: "project_type",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['project_type'].map(o => [o.value, o.label])),
              editorParams: { values: statusOptions['project_type']},
              width : 100,
              headerSort: false, 
            },
            {
              title:"Samples", 
              field:"number_samples", 
              width: 75,  
              headerSort: false,
              },
            {
              title: "TurnAround<br>Time",
              field: "turn_around_time",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['turn_around_time'].map(o => [o.value, o.label])),
              editorParams: { values: statusOptions['turn_around_time'] },
              width: 90,
              headerSort: false,
              
            },
            {
              title:"NOB<br>Samples", 
              field:"nob_number_samples", 
              width:75, 
              headerSort: false,
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
              title:"Technician", 
              field:"technician", 
              width:100, 
              headerSort: false,
            },
            {
              title:"Comment", 
              field:"comment", 
              width:100, 
              headerSort: false,
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
    filters.push({ field: "status", type: "in", value: filterStatusSelectedValues });
  }

  // Turn around time
  const filterTurnAroundTime = document.querySelector("#filter-input-turn-around-time");
  const filterTurnAroundTimeSelectedValues = Array.from(filterTurnAroundTime.selectedOptions)
    .map((option) => parseInt(option.value, 10));

  if (filterTurnAroundTimeSelectedValues.length) {
    filters.push({ field: "turn_around_time", type: "in", value: filterTurnAroundTimeSelectedValues });
  }

  const filterProjectName = document.querySelector("#filter-input-project-name").value;
  if (filterProjectName) filters.push(likeIgnoreCase("project_name", filterProjectName ));

  const filterProjectAddress = document.querySelector("#filter-input-project-address").value;
  if (filterProjectAddress) filters.push(likeIgnoreCase("project_address", filterProjectAddress));

  table.setFilter(filters);   // пустой массив = снять всё
}

document.getElementById("filter-panel-apply-button").addEventListener("click", applyFilters);

document.getElementById("filter-panel-reset-filter-button").addEventListener("click", function() {
  table.setFilter(); 
    });
    