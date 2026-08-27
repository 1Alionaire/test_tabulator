
// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

// ==================== Переключение вкладок ====================

const filterPanel = document.getElementById("main-section-filter");
const createPanel = document.getElementById("main-section-create");

document.getElementById("main-menu-filter-toggle").addEventListener("click", function (e) {
    filterPanel.classList.toggle('invisible');
});

// ==================== Переключение вкладок ====================
function onlyOnCreate(cell) {
  return cell.getRow().getData()._isNew === true;
}

let table;

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
        columns:[
            {title:"Lab ID", field:"lab_id", width: 80, editor:"input", editable: onlyOnCreate },
            {title:"Date", field:"date_registered", editor: "date", formatter:"date", width:80  },
            {title:"Time", field:"time_registered", editor: "time", formatter:"time", width:80},
            {title: "Company",
              field: "company",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['company'].map(o => [o.value, o.label])),
              editor: "list",
              editable: onlyOnCreate,
              editorParams: { values: statusOptions['company'] },
            },
            {title:"Project Name", field:"project_name", width:400, editor:"input"},
            {title:"Project Address", field:"project_address", hozAlign:"center", width:400, editor:"input"},
            {
              title: "Type Analysis",
              field: "sample_type_id",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['sample_type'].map(o => [o.value, o.label])),
              editor: "list",
              editable: onlyOnCreate,
              editorParams: { values: statusOptions['sample_type']},
              width : 100,
            },
            {title:"Amount Samples", field:"number_samples", hozAlign:"center", width:100, editor:"number"},
            {
              title: "Turn Around Time",
              field: "turn_around_time",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['turn_around_time'].map(o => [o.value, o.label])),
              editor: "list",
              editorParams: { values: statusOptions['turn_around_time'] },
              width : 80,
            },
            {title:"NOB Amount Samples", field:"nob_number_samples", hozAlign:"center", width:100, editor:"number", width:80},
            {
              title: "Status",
              field: "status",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['status'].map(o => [o.value, o.label])),
              width: 80,
            },
              {title:"Technician", field:"technician", hozAlign:"center", width:100, editor:"input", editable:true},
              {title:"Comment", field:"comment", hozAlign:"center", width:100, editor:"input"},
          ],
      });
  })();

document.getElementById("main-menu-refresh-toggle").addEventListener("click", function() {
  table.setData(URLS.mainProjectGetURL);
    });

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

document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

const ORIGINALS = new Map();

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

    // const {rows} = await res.json();
    // table.updateData(rows);
    // rows.forEach(r => ORIGINALS.set(String(r.lab_id), r.updated_at));

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

