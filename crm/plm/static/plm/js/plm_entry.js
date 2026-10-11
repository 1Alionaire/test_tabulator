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

const entryORIGINALS = new Map();
let dataEntryTable;
const entryDeletedIds = new Set();
const dirtyRows = [];

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
        ajaxURL: URLS.dataEntryGetURL,
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
        if (!dirtyRows.includes(cell.getRow().getData())) {
          dirtyRows.push(cell.getRow().getData());
        }
      });

      dataEntryTable.on("clipboardPasted", (clipboard, rowData, rows) => {
        rows.forEach(row =>  {
          if (!dirtyRows.includes(row.getData())) {
            dirtyRows.push(row.getData());
          };
        }
      );
    });
})();

// =================== Refresh table ===================
document.getElementById("data-entry-refresh-toggle").addEventListener("click", function() {
  const hasChanges = dirtyRows.size || entryDeletedIds.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  dataEntryTable.setData(URLS.dataEntryGetURL);
  dirtyRows.length = 0;
  entryDeletedIds.clear();
  showToast("Refreshed", "success");
});

// ===================== Checking fresh rows in middle of table for replacing whole table
function checkNewRows() {
  let freshCell = null //init variable 
  const data = dataEntryTable.getRows(); // parse whole table
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
  if ((entryDeletedIds.size || checkNewRows()) && (confirm("All previous samples results will be deleted, continue?"))) {
    try {
      const response = await fetch(URLS.dataEntryReplaceAllURL, {
        method: "POST",
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
    let payload = {
      created: dirtyRows.filter((element) => !element.id),
      updated: dirtyRows.filter((element) => element.id)
    } // collect changed cells and new cells 
    if (!dirtyRows.length) {
      console.log('no data?')
      return;
    }
    try {
      const response = await fetch(URLS.dataEntryUpdateURL, { // fetch data
        method: "POST",
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

      let dirtyRows = []
      dataEntryTable.setData(URLS.dataEntryGetURL);
      dirtyRows.length = 0;
      entryDeletedIds.clear();
      showToast("Refreshed", "success");
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
        const data = row.getData(); //selecting data from tows
        
        if (data.id) {  // if deleted row has id(it means dataEntryTable has data)
          entryDeletedIds.add(data.id);  // adding to set of deleted existing records  
        }
        row.delete(); // deleting row
        rewriteLabIds();
      }
    }
  }
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

// ==================== Project Date collected ====================
document.getElementById("project-date-collect-form").addEventListener("submit", async function (e) {
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
