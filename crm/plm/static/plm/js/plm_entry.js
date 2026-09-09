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

const deletedIds = new Set();
const insertPositions = new Set();
let tempCounter = 0;

(async () => { 
const response = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await response.json();

console.log(tableOptions);
table = new Tabulator("#samples-data-entry-table", {
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
        ajaxURL: URLS.dataEntryGetURL,
        // selectableRows:true, 
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
  const data = table.getRows();
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
  const data = table.getRows();
  labId = data[0].getData().lab_sample.slice(0, -2);
  for (row of data) {
    row.update({ lab_sample: `${labId}-${row.getPosition()}` });
  }
}


  // =================== Create new row ===================
document.getElementById("data-entry-insert-toggle").addEventListener("click", function() {
  const ranges = table.getRanges(); // parsing ranges from selectable range
  if (!ranges.length) return; // in case no selected range
  
  const cells = ranges[0].getCells(); // parsing rows from selectable range
  const cell = cells[0]?.[0] ?? cells[0]; 

  insertPositions.add(cell.getRow().getPosition()); 

  table.addRow({}, false, cell.getRow());  // adding row in table
  rewriteLabIds();
});


// ================== deleting rows =============
document.getElementById("data-entry-delete-toggle").addEventListener("click", function () {
  const ranges = table.getRanges(); // parsing total range
  if (!ranges.length) return; // in case no selected range

  const rows = ranges[0].getRows(); // parsing rows from selectable range
  for (const row of rows) {
    const data = row.getData(); //selecting data from tows
    const position = row.getPosition();   //getting positions from rows

    if (insertPositions.has(position)) { // in case insertPositions has position
      insertPositions.delete(position)
    }
    
    if (data.id) {  // if deleted row has id(it means table has data)
      deletedIds.add(data.id);  // adding to set of deleted existing records  
    }
    row.delete(); // deleting row
    rewriteLabIds();
  }
});

document.getElementById("data-entry-save-toggle").addEventListener("click", saveChanges);

// ===================== Save =================

async function saveChanges() {
  if (deletedIds.length || checkNewRows) {
    
  }
  else {

  }
};


document.getElementById("data-entry-test-toggle").addEventListener("click", function () {
  console.log(`checkNewRows : ${checkNewRows()}`);
});