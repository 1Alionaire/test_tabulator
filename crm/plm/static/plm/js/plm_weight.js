
const weightDeletedIds = new Set();

// ==================== Making whole table ====================
let weightTable;

(async () => { 

weightTable = new Tabulator("#samples-weight-table", {
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
        ajaxURL: URLS.weightGetURL,
        selectableRange: true,
        selectableRangeColumns: true,
        selectableRangeRows: true,
        selectableRangeClearCells: true,

        columnDefaults: {
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle",
        },
        columns:[
            {
              title:"ID", 
              field:"id", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"Row Number", 
              field:"sample__row_number", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample", 
              width: 160, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Crucible", 
              field:"w_crucible", 
              width: 130, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },

            {
              title:"Crucible with sample", 
              field:"w_crucible_with_sample", 
              width: 160, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
              
            },
            {
              title:"Sample Weight", 
              field:"w_sample", 
              width: 130, 
              editable: false, 
              headerSort: false,
            },
            {
              title:"Sample Ashed", 
              field:"w_sample_ashed", 
              width: 130, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Organic", 
              field:"org", 
              width: 130, 
              editable: false, 
              headerSort: false,
            },
            {
              title:"Petri", 
              field:"w_petri", 
              width: 130, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Petri with Sample", 
              field:"w_petri_with_sample", 
              width: 130, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Residue", 
              field:"residue", 
              width: 130, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"CACO3", 
              field:"caco3", 
              width: 130, 
              editable: false, 
              headerSort: false,
            },
          ],
      });
      weightTable.on("tableBuilt", () => bindTypeToEdit(weightTable)); 

      weightTable.on("cellEdited", () => calculateWeights());
})();

  // =================== Create new row ===================
document.getElementById("weight-insert-toggle").addEventListener("click", function() {
  const ranges = weightTable.getRanges(); // parsing ranges from selectable range
  if (!ranges.length) return; // in case no selected range
  
  const cells = ranges[0].getCells(); // parsing rows from selectable range
  const cell = cells[0]?.[0] ?? cells[0]; 

  weightTable.addRow({}, false, cell.getRow());  // adding row in weightTable
});

// ================== deleting rows =============
document.getElementById("weight-delete-toggle").addEventListener("click", function () {
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
});

function calculateWeights() {
  const data = weightTable.getRows();
  for (row of data) {
    let varCrucible = row.getData().w_crucible;
    if (varCrucible) {
        row.update({w_sample: Math.round(((row.getData().w_crucible_with_sample || 0) - (varCrucible || 0)) * 10000) / 10000 });
        row.update({org:  Math.round( (((row.getData().w_sample || 0) - ((row.getData().w_sample_ashed || 0) - (varCrucible || 0))) / (row.getData().w_sample || 0) * 100 ) * 100 ) / 100 });
        row.update({residue: Math.round(  ((((row.getData().w_petri_with_sample || 0) - ((row.getData().w_petri || 0))) / (row.getData().w_sample || 0)) * 100)   * 100) / 100});
        row.update({caco3: Math.round( ((100 - row.getData().residue - row.getData().org)) * 100) / 100 });
    }
  }
}

document.getElementById("weight-test-toggle").addEventListener("click", function () {
    for (element of weightDeletedIds) {
        console.log(element);
    }
});

// ============================ Save changes ===========================
document.getElementById("weight-save-toggle").addEventListener("click", weightSaveChanges);

function weightCollectChanges() {
  const updatedData = {}; // initialize update dict 
  const createdData = {};  // initialize create dict 

  for (const cell of weightTable.getEditedCells()) {  // going through all edited cells
    const data = cell.getRow()?.getData();  //parse data from whole row?
    
    if (!data) continue; // if we dont have data -> continue

    const clientId = String(data.client_sample);           

    let all_data_row = {id:data.id,
                        client_sample:data.client_sample,
                        w_crucible:data.w_crucible, 
                        w_crucible_with_sample:data.w_crucible_with_sample, 
                        w_sample:data.w_sample,
                        w_sample_ashed:data.w_sample_ashed, 
                        org:data.org,
                        w_petri:data.w_petri,
                        w_petri_with_sample:data.w_petri_with_sample,
                        residue:data.residue,
                        caco3:data.caco3};

    // in case its new cell
    if (isEmpty(String(data.id))) { 
        createdData[clientId] = all_data_row
    }
    // in case its already existing cell 
    else {        
        updatedData[clientId] = all_data_row
      };
  }

    const result = {
      updated: Object.values(updatedData),
      created: Object.values(createdData),
      deleted: [...weightDeletedIds],
    };
  return result;
}

async function weightSaveChanges() {
    try {
      const changes = weightCollectChanges();
      if (!changes.updated.length && !changes.created.length && !changes.deleted) {
        console.log('no data?')
        return;
        }
      const response = await fetch(URLS.weightUpdateURL, {
        method: "POST",
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
      entryDeletedIds.clear();
    }
};

// =================== Refresh table ===================
document.getElementById("weight-refresh-toggle").addEventListener("click", function() {
  const changes = weightCollectChanges(); // collecting all changes
  const hasChanges = changes.updated.length || changes.created.length || weightDeletedIds.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  weightTable.setData(URLS.weightGetURL);
  showToast(`Refreshed`, "success");
});