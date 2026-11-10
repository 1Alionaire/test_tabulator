// ==================== Переключение вкладок ====================

const tabNav = document.querySelector('.tabs');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.tab').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));
    document.querySelectorAll('.action-group').forEach((p, j) => p.classList.toggle('active', j === index));

    if (index === 1) dataEntryTable?.redraw(true);
    if (index === 2) weightTable?.redraw(true);
    if (index === 3) nobTable?.redraw(true);
    if (index === 4) temTable?.redraw(true);
});


// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

const updatedData = new Map();

function markDirty(row, field) {
  const id = row.getData().id;
  if (!updatedData.has(id)) updatedData.set(id, {});
  updatedData.get(id)[field] = row.getData()[field];
  updatedData.get(id)['version'] = row.getData()['version'];
}

const entryORIGINALS = new Map();
let dataEntryTable;
const entryDeletedIds = new Set();
const dirtyRows = [];
const entryDeletedIdsInEnd = new Set();


(async () => { 
const response = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await response.json();

dataEntryTable = new Tabulator("#samples-data-entry-table", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        history:true,
        height: "100%",
        width: "100%", 
        layout:"fitColumns",
        editTriggerEvent: "dblclick",
        ajaxURL: URLS.dataEntryURL,
        selectableRange: true,
        columnDefaults: {
          contextMenu: cellMenu,
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle", 
        },
        clipboard: true,
        clipboardCopyStyled: false,
        clipboardCopyConfig: { rowHeaders: false, columnHeaders: false },
        clipboardCopyRowRange: "range",
        clipboardPasteParser: "range",
        clipboardPasteAction: "range",
        editorEmptyValue: null,
        columns:[
            {
              title:"ID", 
              field:"id", 
              visible: false
            },
            {
              title:"Row Number", 
              field:"row_number", 
              visible: false
            },
            {
              title:"Version",
              field:"version",
              visible: false
            },
            { 
              title:"Client ID", 
              field:"client_sample", 
              width: 100, 
              editor: tabulatorTextEditor, 
            },
            {
              title:"Homogenity", 
              field:"homo_area", 
              width: 125, 
              editor: tabulatorTextEditor, 
              
            },
            {
              title:"Layer", 
              field:"layer", 
              width: 55, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Description", 
              field:"description", 
              width: 500, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Location", 
              field:"location", 
              width: 500, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Method", 
              field:"method", 
              width: 70, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleMethod'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleMethod'] },
            },
            {
              title:"Lab Sample", 
              field:"lab_sample", 
              width: 140, 
              editor:"input", 
              headerSort: false,
              
            },
          ],
      });
      dataEntryTable.on("tableBuilt", () => bindTypeToEdit(dataEntryTable));
      
      dataEntryTable.on("cellEdited", (cell) => {
        if (cell.getRow().getData().id) {
          markDirty(cell.getRow(), cell.getField());
        }
        else {
          if (!dirtyRows.includes(cell.getRow().getData())) {
            dirtyRows.push(cell.getRow().getData());
          };
        };
      });

      dataEntryTable.on("clipboardPasted", (clipboard, rowData, rows) => {
        const fields = new Set(rowData.flatMap(Object.keys));

        rows.forEach((row) => {
          fields.forEach((field) => markDirty(row, field));
          if (!dirtyRows.includes(row.getData())) {
            dirtyRows.push(row.getData());
          };
        });
    });
})();

// =================== Refresh table ===================
document.getElementById("data-entry-refresh-toggle").addEventListener("click", function() {
  
  const hasChanges = dirtyRows.size || entryDeletedIds.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  dataEntryTable.setData(URLS.dataEntryURL);
  dirtyRows.length = 0;
  entryDeletedIds.clear();
  showToast("Refreshed", "success");
});


  // =================== When adding or deleting row all LabId rewriting ===================
function rewriteLabIds() {
  const data = dataEntryTable.getRows();
  labId = data[0].getData().lab_sample.slice(0, -2);
  for (row of data) {
      row.update({ lab_sample: `${labId}-${row.getPosition()}` });
      row.update({ row_number: `${row.getPosition()}` });
  }
}

document.getElementById("data-entry-save-toggle").addEventListener("click", entrySaveChanges);

// ============================ Save changes ===========================
async function entrySaveChanges() {
// Save scenario 1: we have changes affects whole dataEntryTable(insert rows in middle, deleting existing rows)
  if ((entryDeletedIds.size || checkNewRows(dataEntryTable)) && (confirm("All previous samples results will be deleted, continue?"))) {
    try {
      const response = await fetch(URLS.dataEntryURL, {
        method: "PUT",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(dataEntryTable.getData()),
      });

      if (!response.ok) {
        await showResponseError(response);
        return;                                   // флаги не снимаем — правки живы
      }

      dataEntryTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

      showToast(`Table Saved`, "success");
      dirtyRows.size = 0;
    }
    catch (e) {
      showToast(`Error: ${e}`, "error");
    } finally {
      entryDeletedIds.clear();
    }
  } 
// Save scenario 2: we dont have changes affects whole dataEntryTable(edit existing cells or adding rows at the end of dataEntryTable)
  else {
    if (!updatedData.size && !dirtyRows.length && !entryDeletedIdsInEnd.size) { 
      console.log('no data?')
      return;
    };
    let payload = {
      created: dirtyRows, 
      updated: Array.from(updatedData, ([id, fields]) => ({
      id: Number(id), ...fields,
    })),
      deleted: [...entryDeletedIdsInEnd]
    } 
    try {
      const response = await fetch(URLS.dataEntryURL, { // fetch data
        method: "PATCH",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        await showResponseError(response);
        return;                                   // флаги не снимаем — правки живы
      }

      dataEntryTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

      const resultJSON = await response.json();
      let resultMessage = ''
      if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
      if (resultJSON.created) {resultMessage += `Created: ${resultJSON.created}`};

      dirtyRows.splice(0);
      dataEntryTable.setData(URLS.dataEntryURL);
      entryDeletedIds.clear();
      entryDeletedIdsInEnd.clear();
      // showToast("Refreshed", "success");
      nobTable.setData(URLS.nobGetURL);
      temTable.setData(URLS.temGetURL);

      showToast(`Table Saved ${resultMessage}`, "success");
    }
    catch (e) {
      showToast(`Error: ${e}`, "error");
    } finally {
      entryDeletedIds.clear();
    }
  }
};

const cellMenu = [
  {
    label: "Copy",
    action: function (e, cell) {
      const table = cell.getTable();
      const ranges = table.getRanges();

      if (ranges.length) {
        table.copyToClipboard("range");     // весь выделенный диапазон
      } else {
        navigator.clipboard.writeText(String(cell.getValue() ?? ""));
      }
    }
  },
  { separator: true },
  {
    label: "Insert Row under",
    action: () => InsertRow(dataEntryTable, false)
  },
  {
    label: "Insert Row below",
    action: () => InsertRow(dataEntryTable, true)
  },
  { separator: true },
  {
    label: "Delete Row",
    action: function () {
      const ranges = dataEntryTable.getRanges(); // parsing total range
      if (!ranges.length) return; // in case no selected range

      const rows = ranges[0].getRows(); // parsing rows from selectable range
      for (const row of rows) {
        if (row.getData().id) { 
          // const data = row.getData(); //selecting data from tows
          if (row.getPosition() == dataEntryTable.getRows().length ) {
            entryDeletedIdsInEnd.add(row.getData().id);
          }
          else {
            entryDeletedIds.add(row.getData().id);
          }
        }
        row.delete(); // deleting row
        rewriteLabIds();
      }
    }
  }, 
  { separator: true },
{
    label: "Test",
    action: function () {
      console.log(`entryDeletedIdsInEnd : ${entryDeletedIdsInEnd}`)
      console.log(`entryDeletedIds : ${entryDeletedIds}`)
    }
  }, 
];

async function InsertRow(input_table, isBelow) {
  const ranges = input_table.getRanges();
  const cells = ranges.length ? ranges[0].getCells() : [];
  const cell = cells[0]?.[0] ?? cells[0];

  // below the selected row, or at the end when nothing is selected (empty table)
  if (cell) {
    await input_table.addRow({}, isBelow, cell.getRow());
  } else {
    await input_table.addRow({}, isBelow);
  }
  rewriteLabIds();
};

const btn = document.getElementById('info-toggle');
const panel = document.getElementById('project-info');

btn.addEventListener('click', () => {
  const isOpen = btn.getAttribute('aria-expanded') === 'true';
  btn.setAttribute('aria-expanded', String(!isOpen));
  panel.hidden = isOpen;                       // прячем, если было открыто
  btn.querySelector('.arrow').textContent = isOpen ? '▶' : '▼';
});

async function initProjectFormPanel() {
  const response = await fetch(URLS.projectFormURL);
  const result = await response.json();
  document.querySelector('#date-collect').value = result.date_collect;
  document.querySelector('#date-analyze').value = result.date_analyze;
  document.querySelector('#date-report').value = result.date_report;
  document.querySelector('#date-review').value = result.date_review;
  const select = document.querySelector('#select-reviewer');
  select.innerHTML = '<option value="">— all —</option>';
  for (const item of result.reviewer_choices) {
    const opt = document.createElement("option");
    if (item.id === result.reviewed_by) {
        opt.selected = true;
    }
    opt.value = item.id;
    opt.label = item.username;
    select.append(opt);
  }
};

initProjectFormPanel();

// ==================== Project form: save one field ====================
// PATCH sends only the changed field; input name = serializer field, e.g. {"date_collect": "2026-11-06"}
async function projectFormSave(element) {
  const field = element.name;
  const value = element.value === '' ? null : element.value;  // cleared date -> null (dates are nullable)

  try {
    const response = await fetch(URLS.projectFormURL, {
      method: "PATCH",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify({[field]: value}),
    });

    if (!response.ok) {
      // DRF errors: {"date_collect": ["..."]} or {"detail": "..."}
      const body = await response.json().catch(() => ({}));
      showToast(`Error: ${body[field]?.join(' ') ?? body.detail ?? response.status}`, "error");
      return;
    }

    const result = await response.json();
    element.value = result[field] ?? '';  // show what the server saved
    showToast("Saved", "success");
  } catch (e) {
    showToast(`Error: ${e}`, "error");
  }
}

// each field saves itself on change; element name = serializer field (#select-reviewer -> reviewed_by)
const PROJECT_FORM_FIELDS = ['#date-collect', '#date-analyze', '#date-report', '#date-review', '#select-reviewer'];

for (const selector of PROJECT_FORM_FIELDS) {
  document.querySelector(selector).addEventListener('change', function(e) {
    projectFormSave(e.target);
  });
}


