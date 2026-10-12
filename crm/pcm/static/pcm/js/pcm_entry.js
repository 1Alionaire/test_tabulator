// ==================== Switching tabs ====================

const tabNav = document.querySelector('.tabs');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.tab').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));
    document.querySelectorAll('.action-group').forEach((p, j) => p.classList.toggle('active', j === index));

    // if (index === 1) dataEntryTable?.redraw(true);
    // if (index === 2) weightTable?.redraw(true);
    // if (index === 3) nobTable?.redraw(true);
    // if (index === 4) temTable?.redraw(true);
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

function roundTo(value, places) {
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
}

function toMinutes(timeValue) {    // "HH:MM" or "HH:MM:SS"
  if (isEmpty(timeValue)) return null;
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
  const duration = ((minutesOut - minutesIn) % 1440 + 1440) % 1440;   // sampling past midnight
  const averageFlow = (Number(data.flow_rate_before) + Number(data.flow_rate_after)) / 2;
  return roundTo(averageFlow * duration, 2);
}

// returns [fibers/mm², fibers/cc], without blank correction
function calculateFiberResults(amountFibers, fields, sampleVolume) {
  if (isEmpty(amountFibers) || !Number(fields)) return [null, null];
  const fiberDensity = Number(amountFibers) / (Number(fields) * FIELD_AREA_MM2);
  if (!Number(sampleVolume)) return [roundTo(fiberDensity, 2), null];
  const fiberConcentration = fiberDensity * FILTER_COLLECTION_AREA_MM2 / (Number(sampleVolume) * 1000);
  return [roundTo(fiberDensity, 2), roundTo(fiberConcentration, 3)];
}


// ==================== Data entry table ====================
const VOLUME_INPUT_FIELDS = ["time_in", "time_out", "flow_rate_before", "flow_rate_after"];

const entryDeletedIds = new Set();
let entryHasChanges = false;
let dataEntryTable;

// volume typed by hand stays until time in/out and both flow rates are filled
function updateSampleVolume(row) {
  const volume = calculateSampleVolume(row.getData());
  if (volume !== null) row.update({sample_volume: volume});
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
              editor: timeEditor,
            },
            {
              title:"Time Out",
              field:"time_out",
              width: 100,
              formatter: formatTimeHM,
              editor: timeEditor,
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

      dataEntryTable.on("cellEdited", (cell) => {
        entryHasChanges = true;
        if (VOLUME_INPUT_FIELDS.includes(cell.getField())) updateSampleVolume(cell.getRow());
      });

      // range paste passes internal rows, not row components
      dataEntryTable.on("clipboardPasted", (clipboard, rowData, rows) => {
        entryHasChanges = true;
        rows.forEach(row => updateSampleVolume(row.getComponent()));
      });
})();

// =================== Refresh table ===================
document.getElementById("data-entry-refresh-toggle").addEventListener("click", function() {
  if ((entryHasChanges || entryDeletedIds.size) && !confirm("Unsaved changes will be lost. Continue?")) {
    return;
  }
  dataEntryTable.setData(URLS.dataEntryGetURL);
  entryDeletedIds.clear();
  entryHasChanges = false;
  showToast("Refreshed", "success");
});

// =================== Row numbers and lab sample ids follow table order (server does the same on save) ===================
function rewriteLabIds() {
  dataEntryTable.getRows().forEach((row, index) => {
    row.update({row_number: index + 1, lab_sample: `${PROJECT_LAB_ID}-${index + 1}`});
  });
}




// ============================ Save changes ===========================
document.getElementById("data-entry-save-toggle").addEventListener("click", entrySaveChanges);

async function entrySaveChanges() {
  if (entryDeletedIds.size && !confirm("Deleted samples will lose their analysis results. Continue?")) {
    return;
  }

  const payload = {
    rows: dataEntryTable.getData("active").map(row => ({
      id: row.id,
      client_sample: row.client_sample,
      iwa_owa: row.iwa_owa,
      location: row.location,
      time_in: row.time_in,
      time_out: row.time_out,
      flow_rate_before: row.flow_rate_before,
      flow_rate_after: row.flow_rate_after,
      sample_volume: row.sample_volume,
    })),
    deleted: [...entryDeletedIds],
  };

  try {
    const response = await fetch(URLS.dataEntryUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;                                   // keep edits and deleted ids, user can fix and save again
    }

    const resultJSON = await response.json();
    entryDeletedIds.clear();
    entryHasChanges = false;
    dataEntryTable.setData(URLS.dataEntryGetURL);
    if (!analysisHasChanges) analysisTable.setData(URLS.analysisGetURL);   // volumes changed

    showToast(`Table Saved: Updated: ${resultJSON.updated} Created: ${resultJSON.created} Deleted: ${resultJSON.deleted}`, "success");
  }
  catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
};

const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

function normalizeTime(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return "";
  if (TIME_RE.test(s)) return s;

  const digits = s.replace(/\D/g, "");
  let h, m;

  if (digits.length <= 2) {          // "9" → 09:00, "14" → 14:00
    h = digits.padStart(2, "0");
    m = "00";
  } else if (digits.length === 3) {  // "930" → 09:30
    h = `0${digits[0]}`;
    m = digits.slice(1);
  } else if (digits.length === 4) {  // "1430" → 14:30
    h = digits.slice(0, 2);
    m = digits.slice(2);
  } else {
    return null;
  }

  const result = `${h}:${m}`;
  return TIME_RE.test(result) ? result : null;
}

function timeEditor(cell, onRendered, success, cancel) {
  const input = document.createElement("input");
  input.type = "text";
  input.value = cell.getValue() ?? "";
  input.placeholder = "ЧЧ:ММ";
  input.inputMode = "numeric";
  input.style.cssText =
    "width:100%;height:100%;box-sizing:border-box;border:none;outline:none;" +
    "padding:0 6px;background:transparent;text-align:inherit;font:inherit;color:inherit;";

  let finished = false;

  function commit() {
    if (finished) return;
    const value = normalizeTime(input.value);
    if (value === null) {
      finished = true;
      return cancel();
    }
    finished = true;
    success(value);
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      e.stopImmediatePropagation();
      commit();
      const nextRow = cell.getRow().getNextRow();
      if (nextRow) {
        requestAnimationFrame(() => nextRow.getCell(cell.getField()).edit());
      }
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopImmediatePropagation();
      finished = true;
      cancel();
    }
  });

  input.addEventListener("blur", commit);

  onRendered(() => {
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });

  return input;
}

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
    action: () => InsertRow(false)
  },
  {
    label: "Insert Row below",
    action: () => InsertRow(true)
  },
  { separator: true },
  {
    label: "Delete Row",
    action: async function () {
      const ranges = dataEntryTable.getRanges();
      if (!ranges.length) return;

      const rows = ranges[0].getRows();
      for (const row of rows) {
        if (row.getData().id) {   // row already saved in database
          entryDeletedIds.add(row.getData().id);
        }
      }
      await Promise.all(rows.map(row => row.delete()));
      rewriteLabIds();
      entryHasChanges = true;
    }
  }
];

async function InsertRow(isBelow) {
  const ranges = dataEntryTable.getRanges();
  const cells = ranges.length ? ranges[0].getCells() : [];
  const cell = cells[0]?.[0] ?? cells[0];

  // below the selected row, or at the end when nothing is selected (empty table)
  if (cell) {
    await dataEntryTable.addRow({}, isBelow, cell.getRow());
  } else {
    await dataEntryTable.addRow({}, isBelow);
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