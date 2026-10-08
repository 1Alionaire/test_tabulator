
// ==================== CSRF-токен ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');

// ==================== Analysis table ====================

const dirtyRows = [];
const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;
let timeTableHasChanges = false;

const pcmTimeTable = new Tabulator("#pcm-time-table", {
  rowHeader: {
    resizable: false, frozen: true, width: 40,
    hozAlign: "center", formatter:"rownum",
    cssClass: "range-header-col", editor: false, headerSort: false
  },
  history: true,
  height: "100%",
  layout: "fitColumns",
  editTriggerEvent: "dblclick",
  ajaxURL: URLS.PCMTimeTableGetURL,
  selectableRange: true,
  selectableRangeColumns: true,
  selectableRangeRows: true,
  selectableRangeClearCells: true,
  selectableRangeClearCellsValue: null,   // Delete/Backspace on a range
  editorEmptyValue: undefined,
  columnDefaults: {
    headerHozAlign: "center",
    hozAlign: "center",
    vertAlign: "middle",
    headerSort: false,   // sorting would break row order and range selection
  },
  clipboard: true,
  clipboardCopyStyled: false,
  clipboardCopyConfig: { rowHeaders: false, columnHeaders: false },
  clipboardCopyRowRange: "range",
  clipboardPasteParser: "range",
  clipboardPasteAction: "range",
  columns: [
    {
      title: "ID",
      field: "id",
      visible: false
    },
    {
      title: "Row Number",
      field: "row_number",
      visible: false
    },
    {
      title: "Project",
      field: "project",
      editor: tabulatorTextEditor, 
      width: 420,
    },
    {
      title: "Start Time",
      field: "start_time",
      editor: "input",
      width: 100,
      formatter:"time",
      validator: {
                type: function (cell, value) {
                  if (value === "" || value === null) return true;   // пустое разрешаем
                  return TIME_RE.test(value);
                },
              },
    },
    {
      title: "End Time",
      field: "end_time",
      width: 100,
      editor: "input",
      formatter:"time",
      validator: {
                type: function (cell, value) {
                  if (value === "" || value === null) return true;   // пустое разрешаем
                  return TIME_RE.test(value);
                },
              },
    },
  ],
});

pcmTimeTable.on("tableBuilt", () => bindTypeToEdit(pcmTimeTable)); 

pcmTimeTable.on("dataProcessed", () => ensureTrailingBlanks(pcmTimeTable, 100));


pcmTimeTable.on("cellEdited", (cell) => {
  console.log('test');
  const row = cell.getRow();
  const data = row.getData();

  if (!data._dirty) {
    row.update({ _dirty: true, row_number: row.getPosition() });
  }
});



let fillingBlanks = false;
let tempCounter = 0;

const SERVICE_FIELDS = new Set(["_uid", "_isNew", "_dirty", "id", "work_date"]);

function isRowEmpty(data) {
  return Object.entries(data).every(
    ([k, v]) => SERVICE_FIELDS.has(k) || v === null || v === undefined || v === ""
  );
}

function makeBlankRow() {
  return {
    _uid: `tmp-${++tempCounter}`,   // временный ключ строки
    _isNew: true,
  };
}

async function ensureTrailingBlanks(table, minimum = 20) {
  if (fillingBlanks) return;

  const rows = table.getRows();
  let trailing = 0;
  for (let i = rows.length - 1; i >= 0; i--) {
    if (!isRowEmpty(rows[i].getData())) break;
    trailing++;
  }
  if (trailing >= minimum) return;

  fillingBlanks = true;
  try {
    await table.addData(
      Array.from({ length: minimum - trailing }, makeBlankRow)
    );
  } finally {
    fillingBlanks = false;
  }
}



// // ============================ Save changes ===========================
document.getElementById("time-table-save-toggle").addEventListener("click", timeTableSaveChanges);

async function timeTableSaveChanges() {
  // results are recalculated on the server, only the counts are sent
  const changed = pcmTimeTable.getData().filter((d) => d._dirty)
  if (!changed.length) {
      console.log('no data?')
      return;
    }
  let payload = {
    updated : changed.filter((d) => d.id),      // есть id — обновление
     created : changed.filter((d) => !d.id),     // нет id — создание
    } // collect changed cells and new cells 


  try {
    const response = await fetch(URLS.PCMTimeTableUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;                                   // keep edits, user can fix and save again
    }
    showToast("Table Saved", "success");
  }
  catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
};

  // =================== Create new row ===================
document.getElementById("time-table-insert-row-toggle").addEventListener("click", function() {
  const ranges = pcmTimeTable.getRanges(); // parsing ranges from selectable range
  if (!ranges.length) return; // in case no selected range
  
  const cells = ranges[0].getCells(); // parsing rows from selectable range
  const cell = cells[0]?.[0] ?? cells[0]; 

  pcmTimeTable.addRow({}, false, cell.getRow());  // adding row in pcmTimeTable
  markAllDirty();
});

function markAllDirty() {
  for (const row of pcmTimeTable.getRows()) {
    if (isRowEmpty(row.getData())) continue;
    row.update({ _dirty: true, row_number: row.getPosition() });
  }
}