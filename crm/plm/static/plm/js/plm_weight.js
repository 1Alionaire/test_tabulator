
// ==================== Making whole table ====================
let weightTable;

// ================= custom function for input tabulator ================
function weightEnterDownEditor(cell, onRendered, success, cancel, editorParams) {
    const input = document.createElement("input");

    input.type = "number";
    input.value = cell.getValue() ?? "";

    input.style.width = "100%";
    input.style.height = "100%";
    input.style.boxSizing = "border-box";
    input.style.padding = "4px";

    let finished = false;

    onRendered(function () {
        input.focus();
        input.select();
    });

    input.addEventListener("keydown", function (e) {

        if (e.key === "Enter") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;

            // сохраняем значение в Tabulator
            const accepted = success(input.value);

            // например, validation не прошла
            if (accepted === false) {
                finished = false;
                return;
            }

            // переходим в ячейку ниже
            setTimeout(function () {
                cell.navigateDown();
            }, 0);
        }

        if (e.key === "Escape") {
            e.preventDefault();
            e.stopPropagation();

            finished = true;
            cancel();
        }
    });

    // если пользователь кликнул мышкой вне ячейки —
    // тоже сохраняем значение
    input.addEventListener("blur", function () {
        if (!finished) {
            finished = true;
            success(input.value);
        }
    });

    return input;
}

(async () => { 

weightTable = new Tabulator("#samples-weight-table", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        history:true,
        height: "calc(100vh - 120px)",
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
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Crucible", 
              field:"w_crucible", 
              width: 130, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },

            {
              title:"Crucible with sample", 
              field:"w_crucible_with_sample", 
              width: 130, 
              editor: weightEnterDownEditor, 
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
              editor: weightEnterDownEditor, 
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
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Petri with Sample", 
              field:"w_petri_with_sample", 
              width: 130, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Residue", 
              field:"residue", 
              width: 130, 
              editable: false, 
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
      weightTable.on("tableBuilt", () => bindTypeToEdit(weightTable)); // bindTypeToEdit in plm_entry.js

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
    row.delete(); // deleting row
  }
});



function calculateWeights() {
  const data = weightTable.getRows();
  for (row of data) {
    let varCrucible = row.getData().w_crucible;

    row.update({w_sample: Math.round(((row.getData().w_crucible_with_sample || 0) - (varCrucible || 0)) * 10000) / 10000 });
    row.update({org:  Math.round( (((row.getData().w_sample || 0) - ((row.getData().w_sample_ashed || 0) - (varCrucible || 0))) / (row.getData().w_sample || 0) * 100 ) * 100 ) / 100 });
    row.update({residue: Math.round(  ((((row.getData().w_petri_with_sample || 0) - ((row.getData().w_petri || 0))) / (row.getData().w_sample || 0)) * 100)   * 100) / 100});
    row.update({caco3: Math.round( ((100 - row.getData().residue - row.getData().org)) * 100) / 100 });
  }
}

document.getElementById("weight-test-toggle").addEventListener("click", function () {
    calculateWeights();
});


// ============================ Save changes ===========================
document.getElementById("weight-save-toggle").addEventListener("click", weightSaveChanges);

async function weightSaveChanges() {
    try {
      const response = await fetch(URLS.weightUpdateURL, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(weightTable.getData()),
      });

      if (response.status === 422) {
        showErrors((await response.json()).errors);
        return;                                   // флаги не снимаем — правки живы
      }
      if (!response.ok) {
        console.error("STATUS:", response.status, "BODY:", await response.text());
        return;
      }

      weightTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

    }
    catch (e) {
      console.log(e)
    } finally {
      entryDeletedIds.clear();
    }
};

