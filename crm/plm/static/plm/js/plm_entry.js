// ==================== Переключение вкладок ====================

const tabNav = document.querySelector('.control-panel');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.panel-btn');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.panel-btn').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));

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

(async () => { 
const response = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await response.json();

console.log(tableOptions);
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
              field:"row_number", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample", 
              width: 80, 
              editor:"input", 
              headerSort: false,
              
            },
            {
              title:"Homogenity", 
              field:"homo_area", 
              width: 80, 
              editor:"input", 
              headerSort: false,
              
            },

            {
              title:"Description", 
              field:"description", 
              width: 500, 
              editor:"input", 
              headerSort: false,
              
            },
            {
              title:"Location", 
              field:"location", 
              width: 500, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Method", 
              field:"method", 
              width: 80, 
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
              width: 80, 
              editor:"input", 
              headerSort: false,
              
            },
          ],
      });
})();

function checkNewRows() {
  let freshCell = null
  const data = dataEntryTable.getRows();
  for (row of data) {
    if (!row.getData().id) {
      freshCell = row.getPosition()
    }
    if (row.getData().id && freshCell)
    {
      return true;
    }
  }
  return false;
}

function rewriteLabIds() {
  const data = dataEntryTable.getRows();
  labId = data[0].getData().lab_sample.slice(0, -2);
  for (row of data) {
    row.update({ lab_sample: `${labId}-${row.getPosition()}` });
    row.update({ row_number: `${row.getPosition()}` });
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
    const position = row.getPosition();   //getting positions from rows
    
    if (data.id) {  // if deleted row has id(it means dataEntryTable has data)
      entryDeletedIds.add(data.id);  // adding to set of deleted existing records  
    }
    row.delete(); // deleting row
    rewriteLabIds();
  }
});

document.getElementById("data-entry-save-toggle").addEventListener("click", saveChanges);

// ===================== Save =================

function collectChanges() {
  const updatedData = {}; // initialize update dict 
  const createdData = {};  // initialize create dict 

  for (const cell of dataEntryTable.getEditedCells()) {  // going through all edited cells
    const data = cell.getRow()?.getData();  //parse data from whole row?
    
    if (!data || !data.lab_sample) continue; // if we dont have data -> continue

    const labId = String(data.lab_sample);          // единый тип ключа
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
        createdData[labId].fields["row_number"] = cell.getRow().getPosition(); 
        createdData[labId].fields["lab_sample"] = labId;
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

async function saveChanges() {
  // In case we have changes affects whole dataEntryTable(insert rows in middle, deleting existing rows)
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
  // In case we dont have changes affects whole dataEntryTable(edit descriptions or adding rows at the end of dataEntryTable)
  else {
    const changes = collectChanges();
    if (!changes.updated.length && !changes.created.length) {
      console.log('no data?')
      return;
    }
    try {
      const response = await fetch(URLS.dataEntryUpdateURL, {
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
      // showToast(`dataEntryTable Saved: ${resultMessage}`, "success");

    }
    catch (e) {
      console.log(e)
    } finally {
      entryDeletedIds.clear();
    }
  }
};


// document.getElementById("data-entry-test-toggle").addEventListener("click", function () {
//   console.log(JSON.stringify(dataEntryTable.getData()));
// });

