// ==================== Переключение вкладок ====================

const tabNav = document.querySelector('.control-panel');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.panel-btn');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.panel-btn').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));

    if (index === 1) dataEntryTable?.redraw(true);
    if (index === 2) weightTable?.redraw(true);
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

// ================= custom function for input tabulator ================
function entryEnterDownEditor(cell, onRendered, success, cancel, editorParams) {
    const input = document.createElement("input");

    input.type = "text";
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
const response = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await response.json();

dataEntryTable = new Tabulator("#samples-data-entry-table", {
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
        ajaxURL: URLS.dataEntryGetURL,
        selectableRange: true,
        columnDefaults: {
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
        columns:[
            {
              title:"ID", 
              field:"id", 
              width: 80, 
              visible: false
            },
            {
              title:"Row Number", 
              field:"row_number", 
              width: 80, 
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample", 
              width: 80, 
              editor: entryEnterDownEditor, 
              
            },
            {
              title:"Homogenity", 
              field:"homo_area", 
              width: 80, 
              editor: entryEnterDownEditor, 
              
            },
            {
              title:"Layer", 
              field:"layer", 
              width: 40, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Description", 
              field:"description", 
              width: 500, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Location", 
              field:"location", 
              width: 500, 
              editor: entryEnterDownEditor, 
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
})();

// =================== Refresh table ===================
document.getElementById("data-entry-refresh-toggle").addEventListener("click", function() {
  const changes = entryCollectChanges(); // collecting all changes
  const hasChanges = changes.updated.length || changes.created.length || entryDeletedIds.length //put all possible changes in const
  if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) { //asking user for continue if we have changes
        return;
    }
  dataEntryTable.setData(URLS.dataEntryGetURL);
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
    if (row.getData().is_blank == false && row.getData().is_qc_sample == false) {
      row.update({ lab_sample: `${labId}-${row.getPosition()}` });
      row.update({ row_number: `${row.getPosition()}` });
    }
  }
}


  // =================== Create new row ===================
document.getElementById("data-entry-insert-toggle").addEventListener("click", function() {
  const ranges = dataEntryTable.getRanges(); // parsing ranges from selectable range
  if (!ranges.length) return; // in case no selected range
  
  const cells = ranges[0].getCells(); // parsing rows from selectable range
  const cell = cells[0]?.[0] ?? cells[0]; 

  dataEntryTable.addRow({}, false, cell.getRow());  // adding row in dataEntryTable
  rewriteLabIds();
});


// ================== deleting rows =============
document.getElementById("data-entry-delete-toggle").addEventListener("click", function () {
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
});

document.getElementById("data-entry-save-toggle").addEventListener("click", entrySaveChanges);

// ===================== Save =================

function entryCollectChanges() {
  const updatedData = {}; // initialize update dict 
  const createdData = {};  // initialize create dict 

  for (const cell of dataEntryTable.getEditedCells()) {  // going through all edited cells
    const data = cell.getRow()?.getData();  //parse data from whole row?

    if (!data || !data.lab_sample) continue; // if we dont have data -> continue

    const labId = String(data.lab_sample);           // единый тип ключа
    const systemId = String(data.id); 

    // in case its new cell
    if (isEmpty(systemId)) { 
      if (labId in createdData) { // already has record in createdData dict
        createdData[labId].fields[cell.getField()] = cell.getValue(); //add info: field_name : cell_value
        }
      else { //in case dont have record with lab sample yet 
        entry = {lab_sample: labId, fields: {}, version: entryORIGINALS.get(labId)}; // creating new json element
        createdData[labId] = entry; 
        createdData[labId].fields[cell.getField()] = cell.getValue(); //add info: field_name : cell_value
        createdData[labId].fields["row_number"] = cell.getRow().getPosition(); // add row_number to data 
        createdData[labId].fields["lab_sample"] = labId; // add lab_sample to data
      }
    }
    // in case its already existing cell 
    else {
      if (systemId in updatedData) { // already has record in updatedData dict
        updatedData[systemId].fields[cell.getField()] = cell.getValue(); // add info: field_name : cell_value
      }
      else {
        entry = {id: systemId, fields: {}, version: entryORIGINALS.get(systemId)}; // creating new json element
        updatedData[systemId] = entry; 
        updatedData[systemId].fields[cell.getField()] = cell.getValue(); //add info: field_name : cell_value
      }
    };
  }

    const result = {
      updated: Object.values(updatedData),
      created: Object.values(createdData),
    };
  return result;
}

// ============================ Save changes ===========================
async function entrySaveChanges() {
// Save scenario 1: we have changes affects whole dataEntryTable(insert rows in middle, deleting existing rows)
  if ((entryDeletedIds.length || checkNewRows()) && (confirm("All previous samples results will be deleted, continue?"))) {
    try {
      const response = await fetch(URLS.dataEntryReplaceAllURL, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(dataEntryTable.getData()),
      });

      if (response.status === 422) {
        showErrors((await response.json()).errors);
        return;                                   // флаги не снимаем — правки живы
      }
      if (!response.ok) {
        console.error("STATUS:", response.status, "BODY:", await response.text());
        return;
      }

      dataEntryTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

    }
    catch (e) {
      console.log(e)
    } finally {
      entryDeletedIds.clear();
    }
  } 
// Save scenario 2: we dont have changes affects whole dataEntryTable(edit existing cells or adding rows at the end of dataEntryTable)
  else {
    const changes = entryCollectChanges(); // collect changed cells and new cells 
    if (!changes.updated.length && !changes.created.length) {
      console.log('no data?')
      return;
    }
    try {
      const response = await fetch(URLS.dataEntryUpdateURL, { // fetch data
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(changes),
      });

      if (response.status === 422) {
        showErrors((await response.json()).errors);
        return;                                   // флаги не снимаем — правки живы
      }
      if (!response.ok) {
        console.error("STATUS:", response.status, "BODY:", await response.text());
        return;
      }

      dataEntryTable.getEditedCells().forEach(cell => {
        cell.clearEdited();
        cell.getElement().classList.remove("dirty");
      });

      const resultJSON = await response.json();
      let resultMessage = ''
      if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
      if (resultJSON.created) {resultMessage += `Created: ${resultJSON.created}`};

    }
    catch (e) {
      console.log(e)
    } finally {
      entryDeletedIds.clear();
    }
  }
};



// =================== function for start typing in cell without doubleclick ===================
function bindTypeToEdit(table) {
  const holder = table.element.querySelector(".tabulator-tableholder");
  if (!holder) {
    console.error("tableholder не найден — вызов слишком рано");
    return;
  }

  holder.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select")) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key.length !== 1) return;

    const ranges = table.getRanges();
    if (!ranges.length) return;

    const cells = ranges[0].getCells();
    const cell = cells[0]?.[0] ?? cells[0];
    if (!cell) return;

    if (e.key === "Enter") {
        e.preventDefault();
        cell.navigateDown();
        return;
    }

      if (e.key === "F2") {
        e.preventDefault();
        cell.edit();               // правка без стирания
        return;
    }

    e.preventDefault();
    cell.edit();

    requestAnimationFrame(() => {
      const input = cell.getElement().querySelector("input, textarea");
      if (!input) return;
      input.value = e.key;
    });
  });
}
