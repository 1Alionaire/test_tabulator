// ==================== Switching tabs ====================

const tabNav = document.querySelector('.tabs');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.tab').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));
    document.querySelectorAll('.action-group').forEach((p, j) => p.classList.toggle('active', j === index));

});


// ==================== CSRF token ====================
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}
const csrftoken = getCookie('csrftoken');


// ==================== PCM calculations (NIOSH 7400) ====================
// live preview only: the server recalculates the same values on save (pcm_table_logic.py)
const FIELD_AREA_MM2 = 0.00785;             // Walton-Beckett graticule field area, mm²
const FILTER_COLLECTION_AREA_MM2 = 385;     // effective collection area of 25-mm filter, mm²
const updatedData = new Map();

function roundTo(value, places) {
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
}

function toMinutes(timeValue) {    // "HH:MM" or "HH:MM:SS"
  if (isEmpty(timeValue)) return null; // if you null -> null  
  const [hours, minutes] = String(timeValue).split(":").map(Number);
  return hours * 60 + minutes;
}

// liters = average flow rate (L/min) * sampling time (min)
function calculateSampleVolume(data) {
  const minutesIn = toMinutes(data.time_in); 
  const minutesOut = toMinutes(data.time_out);
  if (minutesIn === null || minutesOut === null || isEmpty(data.flow_rate_before) || isEmpty(data.flow_rate_after)) {
    return null;
  }
  const duration = ((minutesOut - minutesIn) % 1440 + 1440) % 1440;   // sampling mintues past midnight
  const averageFlow = (Number(data.flow_rate_before) + Number(data.flow_rate_after)) / 2; // average flow
  return roundTo(averageFlow * duration, 2);
}


// ==================== Data entry table ====================
const VOLUME_INPUT_FIELDS = ["time_in", "time_out", "flow_rate_before", "flow_rate_after"];

// sent on save; row number and lab sample follow the table order and are set by the server
const ENTRY_SAVE_FIELDS = ["client_sample", "iwa_owa", "location", "time_in", "time_out",
                           "flow_rate_before", "flow_rate_after", "sample_volume"];

// row.getData() returns the same object until the table is reloaded,
// table.getData() returns copies - so edited rows are looked up through getRows()
const entryDirtyRows = new Set();
const entryDeletedIds = new Set();   // ids of saved rows deleted in the table
const entryDeletedIdsInEnd = new Set();
let dataEntryTable;

// volume typed by hand stays until time in/out and both flow rates are filled
function updateSampleVolume(row) {
  const volume = calculateSampleVolume(row.getData());
  if (volume !== null) row.update({sample_volume: volume});
}

function markRowDirty(row) {
  entryDirtyRows.add(row.getData());
}

function markDirty(row, field) {
  const id = row.getData().id;
  if (!updatedData.has(id)) updatedData.set(id, {});
  updatedData.get(id)[field] = row.getData()[field];
}

(async () => {
const response = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await response.json();

const workAreaLabels = Object.fromEntries(tableOptions['sampleWorkArea'].map(o => [o.value, o.label]));
const workAreaValues = Object.fromEntries(tableOptions['sampleWorkArea'].map(o => [o.label, o.value]));

dataEntryTable = new Tabulator("#samples-data-entry-table", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false, headerSort: false
        },
        history:true,
        height: "100%",
        layout:"fitColumns",
        editTriggerEvent: "dblclick",
        ajaxURL: URLS.dataEntryGetURL,
        selectableRange: true,
        selectableRangeColumns: true,
        selectableRangeRows: true,
        selectableRangeClearCells: true,
        selectableRangeClearCellsValue: null,   // Delete/Backspace on a range
        editorEmptyValue: null,
        columnDefaults: {
          contextMenu: cellMenu,
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
              title:"Lab Sample",
              field:"lab_sample",
              width: 140,
            },
            {
              title:"Client ID",
              field:"client_sample",
              width: 120,
              editor: tabulatorTextEditor,
            },
            {
              title:"IWA / OWA",
              field:"iwa_owa",
              width: 90,
              formatter: (cell) => workAreaLabels[cell.getValue()] ?? "",
              editor: "list",
              editorParams: { values: tableOptions['sampleWorkArea'] },
              mutatorClipboard: (value) => workAreaValues[String(value).trim().toUpperCase()] ?? value,  // "IWA" pasted from Excel
            },
            {
              title:"Location",
              field:"location",
              minWidth: 300,
              editor: tabulatorTextEditor,
            },
            {
              title: "Time In",
              field: "time_in",
              width: 100,
              formatter: formatTimeHM,
              editor: tabulatorTimeEditor,
            },
            {
              title:"Time Out",
              field:"time_out",
              width: 100,
              formatter: formatTimeHM,
              editor: tabulatorTimeEditor,
            },
            {
              title:"Flow Before<br>L/min",
              field:"flow_rate_before",
              width: 110,
              editor: tabulatorNumberEditor,
            },
            {
              title:"Flow After<br>L/min",
              field:"flow_rate_after",
              width: 110,
              editor: tabulatorNumberEditor,
            },
            {
              title:"Volume<br>L",
              field:"sample_volume",
              width: 110,
              editor: tabulatorNumberEditor,
            },
          ],
      });
      dataEntryTable.on("tableBuilt", () => bindTypeToEdit(dataEntryTable));

      // also fires when a selected range is cleared with Delete/Backspace
      dataEntryTable.on("cellEdited", (cell) => { // in case cell edited
        markRowDirty(cell.getRow()); // add to dirty Rows
        if (cell.getRow().getData().id) { // if sample exists
          markDirty(cell.getRow(), cell.getField()); // mark cell dirty
        }
        if (VOLUME_INPUT_FIELDS.includes(cell.getField())) updateSampleVolume(cell.getRow()); //if field
      });

      // range paste passes internal rows, not row components
      dataEntryTable.on("clipboardPasted", (clipboard, rowData, rows) => {
        const fields = new Set(rowData.flatMap(Object.keys));

        rows.forEach(row => {
          // fields.forEach((field) => markDirty(row, field));
          fields.forEach((field) => {
              if (row.getData().id) {
                markDirty(row, field);
              }
          });
          markRowDirty(row.getComponent());
          updateSampleVolume(row.getComponent());
        });
      });
})();

// =================== Detecting changes ===================
// saved rows deleted in the table and still gone (undo brings a deleted row back)
function getDeletedIds() {
  const presentIds = new Set(dataEntryTable.getRows().map(row => row.getData().id));
  return [...entryDeletedIds].filter(id => !presentIds.has(id));
}

function entryHasChanges() {
  const rows = dataEntryTable.getRows().map(row => row.getData());
  return rows.some(data => !data.id || entryDirtyRows.has(data)) || getDeletedIds().length > 0;
}

function entryPayloadRow(data) {
  const row = {id: data.id};
  for (const field of ENTRY_SAVE_FIELDS) row[field] = data[field];
  return row;
}

// drops local changes and loads the saved samples
function reloadEntryTable() {
  entryDirtyRows.clear();
  entryDeletedIds.clear();
  updatedData.clear()
  return dataEntryTable.setData(URLS.dataEntryGetURL);
}

// =================== Refresh table ===================
document.getElementById("data-entry-refresh-toggle").addEventListener("click", function() {
  if (entryHasChanges() && !confirm("Unsaved changes will be lost. Continue?")) {
    return;
  }
  reloadEntryTable();
  showToast("Refreshed", "success");
});

// =================== Row numbers and lab sample ids follow table order (server does the same on save) ===================
function rewriteLabIds() {
  dataEntryTable.getRows().forEach((row, index) => {
    row.update({row_number: index + 1, lab_sample: `${PROJECT_LAB_ID}-${index + 1}`});
  });
}

// ============================ Save changes ===========================
const entrySaveButton = document.getElementById("data-entry-save-toggle");
entrySaveButton.addEventListener("click", entrySaveChanges);

async function entrySaveChanges() {
  const rows = dataEntryTable.getRows().map(row => row.getData()); // parse all rows 

  // Save scenario 1: saved rows were deleted in the middle of table or new rows inserted above them,
  // so saved samples change their numbers - the whole table replaces all samples
  if (getDeletedIds().length || checkNewRows(dataEntryTable)) { //if we have deleted  or new rows in the middle
    if (!confirm("All previous samples results will be deleted, continue?")) {
      return;                                   // nothing is saved, the edits stay in the table
    }
    await sendEntryChanges(URLS.dataEntryReplaceAllURL, {rows: rows.map(entryPayloadRow)}, true, // full replacement samples
                           (result) => `Table Saved: Replaced: ${result.created}`);
    return;
  }
  // Save scenario 2: edited saved rows and new rows at the end of the table
  const payload = {
    updated: Object.fromEntries(updatedData), //take json with updated data
    created: rows.filter(data => !data.id).map(entryPayloadRow), // take new samples
    deleted: [...entryDeletedIdsInEnd] // take only in the end deleted samples, they are not influence whole table
  };
  if (!updatedData.size && !payload.created.length && !payload.deleted.length) {
    showToast("No changes to save", "info");
    return;
  }
  await sendEntryChanges(URLS.dataEntryUpdateURL, payload, false,
                         (result) => `Table Saved: Updated: ${result.updated} Created: ${result.created}`);
}

async function sendEntryChanges(url, payload, replacesAll, successMessage) {
  entrySaveButton.disabled = true;              // a second click while saving would create the new rows twice
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;                                   // keep edits and deleted ids, user can fix and save again
    }

    const resultJSON = await response.json();
    showToast(successMessage(resultJSON), "success");

    // volumes changed; after replacing all samples the analysis rows no longer exist
    if (replacesAll || !analysisHasChanges) {
      analysisHasChanges = false;
      analysisTable.setData(URLS.analysisGetURL);
    }
    await reloadEntryTable();                   // new samples get their ids
  }
  catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
  finally {
    entrySaveButton.disabled = false;
  }
}

const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;   // used by normalizeTime in utils.js

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
    label: "Insert row above",
    action: () => InsertRow(true)
  },
  {
    label: "Insert row below",
    action: () => InsertRow(false)
  },
  { separator: true },
  {
    label: "Delete row",
    action: async function () {
      const ranges = dataEntryTable.getRanges();
      if (!ranges.length) return;

      const rows = ranges[0].getRows();
      for (const row of rows) {
        if (row.getData().id) { 
          if (row.getPosition() === dataEntryTable.getRows().length ) {
            entryDeletedIdsInEnd.add(row.getData().id);
          }
          else {
            entryDeletedIds.add(row.getData().id);
          }
        }
      }
      await Promise.all(rows.map(row => row.delete()));
      rewriteLabIds();
    }
  },
  {
    label: "Test",
    action: async function () {
      console.log(updatedData);
    }
  }
];

// above = true: above the selected row (Tabulator addRow puts the row before the target)
async function InsertRow(above) {
  const ranges = dataEntryTable.getRanges();
  const cells = ranges.length ? ranges[0].getCells() : [];
  const cell = cells[0]?.[0] ?? cells[0];

  // next to the selected row, or at the top / end when nothing is selected (empty table)
  if (cell) {
    await dataEntryTable.addRow({}, above, cell.getRow());
  } else {
    await dataEntryTable.addRow({}, above);
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

// ==================== Project info ====================
document.getElementById("project-info-form").addEventListener("submit", async function (e) {
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


