// ==================== Analysis table ====================
const QC_INPUT_FIELDS = ["qc_amount_fibers", "qc_fields"];

let qcHasChanges = false;

// Sr for the QC check: relative_std_deviation_low of the analyst's month (#z-criterion-low)
const QC_SR = Number(document.getElementById("z-criterion-low")?.dataset.sr) || null;

// |√X₁ − √X₂| <= 2.77 × ((√X₁ + √X₂) / 2) × Sr -> 1 (Accept), otherwise 2 (Reject)
// X₁ = original F/mm², X₂ = QC F/mm²; the server repeats this check on save
function qcUpdateResult(fiberPerMm, qcFiberPerMm) {
  if (isEmpty(fiberPerMm) || QC_SR === null) return null;
  const sqrtOriginal = Math.sqrt(Number(fiberPerMm));
  const sqrtQc = Math.sqrt(Number(qcFiberPerMm));
  const limit = 2.77 * ((sqrtOriginal + sqrtQc) / 2) * QC_SR;
  return Math.abs(sqrtOriginal - sqrtQc) <= limit ? 1 : 2;
}

function qcUpdateFiberResults(row) {
  const data = row.getData();
  const [qcFiberPerMm, qcFiberPerCubCm] = calculateFiberResults(data.qc_amount_fibers, data.qc_fields, data.sample_volume, data.segment_area);
  // no QC count yet -> clear the old verdict
  const qcAcceptOrReject = (qcFiberPerMm !== null && qcFiberPerMm !== 0)
    ? qcUpdateResult(data.fiber_per_mm, qcFiberPerMm)
    : null;
  row.update({
    qc_fiber_per_mm: qcFiberPerMm,
    qc_fiber_per_cub_cm: qcFiberPerCubCm,
    qc_accept_or_reject: qcAcceptOrReject,
  });
}
let qcTable;

(async () => {

const response = await fetch(URLS.tableOptionsGetURL); // parse all options from database
const statusOptions = await response.json(); //collect into status dict
    qcTable = new Tabulator("#samples-qc-table", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false, headerSort: false
        },
        history:true,
        height: "100%",
        layout:"fitColumns",
        editTriggerEvent: "dblclick",
        ajaxURL: URLS.qcURL,
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
              width: 120,
            },
            {
              title: "Original count",
              columns: [
                { title:"Fibers", field:"amount_fibers", width: 90, editable:false},
                { title:"Fields", field:"fields", width: 90, editable:false },
                { title:"F/mm²", field:"fiber_per_mm", width: 100, editable:false},
                { title:"F/cc", field:"fiber_per_cub_cm", width: 100, editable:false},
              ],
            },
            {
              title: "QC count",
              columns: [
                { title:"Fibers", field:"qc_amount_fibers", width: 90, editor: tabulatorNumberEditor },
                { title:"Fields", field:"qc_fields", width: 90, editor: tabulatorNumberEditor },
                { title:"F/mm²", field:"qc_fiber_per_mm", width: 100 },
                { title:"F/cc", field:"qc_fiber_per_cub_cm", width: 100 },
              ],
            },
            {
              title:"Accept<br>Reject",
              field:"qc_accept_or_reject",
              width: 80,
              editor: "list",
              formatter: (cell) => Object.fromEntries(statusOptions['SampleQCAcceptOrReject'].map(o => [o.value, o.label]))[cell.getValue()] ?? "",
            },
            {
              title:"Time<br>Analysis",
              field:"time_analysis",
              width: 80,
              editor: tabulatorTimeEditor,
              formatter: formatTimeHM,
            },
          ],
      });
    qcTable.on("tableBuilt", () => bindTypeToEdit(qcTable));

    qcTable.on("cellEdited", (cell) => {
      qcHasChanges = true;
      if (QC_INPUT_FIELDS.includes(cell.getField())) qcUpdateFiberResults(cell.getRow());
    });

    // range paste passes internal rows, not row components
    qcTable.on("clipboardPasted", (clipboard, rowData, rows) => {
      qcHasChanges = true;
      rows.forEach(row => qcUpdateFiberResults(row.getComponent()));
    });

})();

// ============================ Save changes ===========================
document.getElementById("qc-save-toggle").addEventListener("click", qcSaveChanges);

async function qcSaveChanges() {
    const payload = qcTable.getData().map(row => ({
      id: row.id,
      qc_amount_fibers: row.qc_amount_fibers,
      qc_fields: row.qc_fields,
    }));

  try {
    const response = await fetch(URLS.qcURL, {
      method: "PATCH",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      await showResponseError(response);
      return;                                   // keep edits, user can fix and save again
    }

    qcHasChanges = false;
    qcTable.setData(URLS.qcURL);
    showToast("Table Saved", "success");
  }
  catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
};
