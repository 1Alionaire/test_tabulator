
const weightDeletedIds = new Set();

const cellWeightMenu = [
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
    action: function() {
      const ranges = weightTable.getRanges(); // parsing ranges from selectable range
      if (!ranges.length) return; // in case no selected range
      
      const cells = ranges[0].getCells(); // parsing rows from selectable range
      const cell = cells[0]?.[0] ?? cells[0]; 

      weightTable.addRow({}, false, cell.getRow());  // adding row in weightTable
    }
  },
  {
    label: "Insert Row below",
    action: function() {
      const ranges = weightTable.getRanges(); // parsing ranges from selectable range
      if (!ranges.length) return; // in case no selected range
      
      const cells = ranges[0].getCells(); // parsing rows from selectable range
      const cell = cells[0]?.[0] ?? cells[0]; 

      weightTable.addRow({}, true, cell.getRow());  // adding row in weightTable
    }
  },
  { separator: true },
  {
    label: "Delete Row",
    action: function () {
      const ranges = weightTable.getRanges(); // parsing total range
      if (!ranges.length) return; // in case no selected range

      const rows = ranges[0].getRows(); // parsing rows from selectable range
      for (const row of rows) {
        const data = row.getData(); //selecting data from tows

        if (data.id) { 
            weightDeletedIds.add(data.id);
        }
        row.delete(); // deleting row
      }
    }
  }
];

// ==================== Making whole table ====================
let weightTable;

(async () => { 

weightTable = new Tabulator("#samples-weight-table", {
        ajaxURL: URLS.weightURL,
        height: "100%",   // table scrolls inside itself, not the page
        columnDefaults: {
          contextMenu: cellWeightMenu,
            ...columnDefaultParameters,
        },
        selectableRange: true,
        selectableRangeRows: true,
        clipboard: true,
        selectableRangeClearCells: true,
        selectableRangeClearCellsValue: null,
        editorEmptyValue: null,
        clipboardCopyStyled: false,
        clipboardCopyConfig: { rowHeaders: false, columnHeaders: false },
        clipboardCopyRowRange: "range",
        clipboardPasteParser: "range",
        clipboardPasteAction: "range",
        ...universalTabulatorParameters,
        columns:[
            {
              title:"ID", 
              field:"id",
              visible: false
            },
            {
              title:"Row Number", 
              field:"sample__row_number",
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample",
              width: 100,
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Lab Sample Id",
              field:"sample.lab_sample",
              width: 160,
              editable: false,
            },
            {
              title:"Crucible", 
              field:"w_crucible", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },

            {
              title:"Crucible</br>with sample",
              field:"w_crucible_with_sample", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
              
            },
            {
              title:"Sample Weight", 
              field:"w_sample", 
              width: 120,
              editable: false, 
              headerSort: false,
            },
            {
              title:"Sample Ashed", 
              field:"w_sample_ashed", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Organic", 
              field:"org", 
              width: 120,
              editable: false, 
              headerSort: false,
            },
            {
              title:"Petri", 
              field:"w_petri", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Petri<br>with Sample",
              field:"w_petri_with_sample", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Residue", 
              field:"residue", 
              width: 120,
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"CACO3", 
              field:"caco3", 
              width: 120,
              editable: false, 
              headerSort: false,
            },
          ],
      });
      weightTable.on("tableBuilt", () => bindTypeToEdit(weightTable));

      weightTable.on("cellEdited", (cell) => {
          cell.getRow().update({ _dirty: true });
          calculateWeights();
        });

    weightTable.on("clipboardPasted", (clipboard, rowData, rows) => {
      for (const row of rows) {
        const component = row.getComponent?.() ?? row;
        component.update({ _dirty: true });
      }
      calculateWeights();
    });
})();


function calculateWeights() {
  const updates = [];

  for (const row of weightTable.getRows()) {
    const d = row.getData();
    const crucible = Number(d.w_crucible);
    if (!crucible) continue;

    const wSample = round4((Number(d.w_crucible_with_sample) || 0) - crucible);
    const org = wSample
      ? round2((wSample - ((Number(d.w_sample_ashed) || 0) - crucible)) / wSample * 100)
      : 0;
    const residue = wSample
      ? round2(((Number(d.w_petri_with_sample) || 0) - (Number(d.w_petri) || 0)) / wSample * 100)
      : 0;

    row.update({ w_sample: wSample, org, residue, caco3: round2(100 - residue - org) });
  }
}

const round2 = (n) => Math.round(n * 100) / 100;
const round4 = (n) => Math.round(n * 10000) / 10000;

function returnNull(inputValue){
  if (isEmpty(inputValue)) {
    return null
  }
  else {
    return inputValue
  }
}

// ============================ Save changes ===========================
document.getElementById("weight-save-toggle").addEventListener("click", weightSaveChanges);

const WEIGHT_FIELDS = [
  "client_sample", "w_crucible", "w_crucible_with_sample",
  "w_sample", "w_sample_ashed", "org",
  "w_petri", "w_petri_with_sample", "residue", "caco3",
];

const SERVICE_FIELDS = new Set(["_uid", "_dirty", "id", "version", "sample", "sample__row_number"]);

function isRowEmpty(data) {
  return Object.entries(data).every(
    ([k, v]) => SERVICE_FIELDS.has(k) || v === null || v === undefined || v === ""
  );
}

function weightCollectChanges() {
  const updated = [];
  const created = [];

  for (const data of weightTable.getData()) {
    if (!data._dirty || isRowEmpty(data)) continue;

    const row = {
      ...Object.fromEntries(WEIGHT_FIELDS.map((f) => [f, returnNull(data[f])])),
      version: data.version,
    };

    if (data.id) {
      updated.push({ id: data.id, ...row });
    } else {
      created.push(row);
    }
  }

  return { updated, created, deleted: [...weightDeletedIds] };
}
async function weightSaveChanges() {
    try {
      const changes = weightCollectChanges();
      if (!changes.updated.length && !changes.created.length && !changes.deleted) {
        console.log('no data?')
        return;
        }
      const response = await fetch(URLS.weightURL, {
        method: "PATCH",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(changes),
      });

      if (!response.ok) {
        await showResponseError(response);
        return;                                   // флаги не снимаем — правки живы
      }

      weightTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

      showToast(`Table Saved`, "success");
    }
    catch (e) {
      showToast(`Error: ${e.message}`, "error");
    } finally {
      // entryDeletedIds.clear();
    }
};

// =================== Refresh table ===================
document.getElementById("weight-refresh-toggle").addEventListener("click", function() {
  const changes = weightCollectChanges(); // collecting all changes
  const hasChanges = changes.updated.length || changes.created.length || weightDeletedIds.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  weightTable.setData(URLS.weightURL);
  showToast(`Refreshed`, "success");
});

