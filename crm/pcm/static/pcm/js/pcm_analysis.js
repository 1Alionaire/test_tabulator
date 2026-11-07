// ==================== Analysis table ====================
const ANALYSIS_INPUT_FIELDS = ["amount_fibers", "fields"];

let analysisHasChanges = false;

// returns [fibers/mm², fibers/cc], without blank correction
function calculateFiberResults(amountFibers, fields, sampleVolume, segment_area) {
  if (isEmpty(amountFibers) || !Number(fields)) return [null, null];
  const fiberDensity = Number(amountFibers) / (Number(fields) * segment_area);
  if (!Number(sampleVolume)) return [roundTo(fiberDensity, 2), null];
  const fiberConcentration = fiberDensity * FILTER_COLLECTION_AREA_MM2 / (Number(sampleVolume) * 1000);
  return [roundTo(fiberDensity, 2), roundTo(fiberConcentration, 3)];
}

function updateFiberResults(row) {
  const data = row.getData();
  const [fiberPerMm, fiberPerCubCm] = calculateFiberResults(data.amount_fibers, data.fields, data.sample_volume, data.segment_area);
  row.update({
    fiber_per_mm: fiberPerMm,
    fiber_per_cub_cm: fiberPerCubCm,
  });
}

const analysisTable = new Tabulator("#samples-analysis-table", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false, headerSort: false
        },
        history:true,
        height: "100%",
        layout:"fitColumns",
        editTriggerEvent: "dblclick",
        ajaxURL: URLS.analysisURL,
        selectableRange: true,
        selectableRangeColumns: true,
        selectableRangeRows: true,
        selectableRangeClearCells: true,
        selectableRangeClearCellsValue: null,   // Delete/Backspace on a range
        editorEmptyValue: null,
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
        columns:[
            {
              title:"ID",
              field:"id",
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
              width: 80,
            },
            {
              title:"Location",
              field:"location",
              width: 500,
            },
            {
              title:"Volume<br>L",
              field:"sample_volume",
              width: 100,
            },
            {
              title:"Segment<br>Area",
              field:"segment_area",
              width: 100,
            editor: tabulatorNumberEditor
            },
            {
              title: "Original count",
              columns: [
                { title:"Fibers", field:"amount_fibers", width: 90, editor: tabulatorNumberEditor },
                { title:"Fields", field:"fields", width: 90, editor: tabulatorNumberEditor },
                { title:"F/mm²", field:"fiber_per_mm", width: 100 },
                { title:"F/cc", field:"fiber_per_cub_cm", width: 100 },
              ],
            },

          ],
      });

analysisTable.on("tableBuilt", () => bindTypeToEdit(analysisTable)); 

analysisTable.on("cellEdited", (cell) => {
  analysisHasChanges = true;
  if (ANALYSIS_INPUT_FIELDS.includes(cell.getField())) updateFiberResults(cell.getRow());
});

// range paste passes internal rows, not row components
analysisTable.on("clipboardPasted", (clipboard, rowData, rows) => {
  analysisHasChanges = true;
  rows.forEach(row => updateFiberResults(row.getComponent()));
});

// =================== Refresh table ===================
document.getElementById("analysis-refresh-toggle").addEventListener("click", function() {
  if (analysisHasChanges && !confirm("Unsaved changes will be lost. Continue?")) {
    return;
  }
  analysisTable.setData(URLS.analysisURL);
  analysisHasChanges = false;
  showToast("Refreshed", "success");
});

// ============================ Save changes ===========================
document.getElementById("analysis-save-toggle").addEventListener("click", analysisSaveChanges);

async function analysisSaveChanges() {
    const payload = analysisTable.getData().map(row => ({
      id: row.id,
      amount_fibers: row.amount_fibers,
      fields: row.fields,
    }));

  try {
    const response = await fetch(URLS.analysisURL, {
      method: "PATCH",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;                                   // keep edits, user can fix and save again
    }

    analysisHasChanges = false;
    analysisTable.setData(URLS.analysisURL);
    showToast("Table Saved", "success");
  }
  catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
};

// ==================== Analyst ====================
const analysisOverlay = document.getElementById("take-analysis-overlay");
const analysisOverlay1 = document.getElementById("take-analysis-overlay1");
analysisOverlay.querySelector(".take-btn").addEventListener("click", analystTakeProject);

async function checkProjectAnalyst() {
  try {
    const response = await fetch(URLS.projectAnalyst);
    if (!response.ok) throw new Error(response.status);

    const data = await response.json();
    analysisOverlay.hidden = !isEmpty(data.analyst);
    analysisOverlay1.hidden = !isEmpty(data.analyst);
    document.getElementById("analysis-analyst-username").textContent = data.analyst_username ?? "";
  } catch (err) {
    console.error("checkProjectAnalyst:", err);
  }
};

async function analystTakeProject() {
  try {
    const response = await fetch(URLS.projectAnalyst, {
      method: "PATCH",
      headers: {"X-CSRFToken": csrftoken},
    });

    if (!response.ok) {
      await showResponseError(response);
      return;
    }
    data = await response.json()
    await checkProjectAnalyst();
    showToast("The project has been picked up for work", "success");
    document.querySelector('#z-criterion-low').textContent = `Low : ${data.low}`
    document.querySelector('#z-criterion-medium').textContent = `Medium : ${data.medium}`
    document.querySelector('#z-criterion-high').textContent = `High : ${data.high}`
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
};

checkProjectAnalyst();
