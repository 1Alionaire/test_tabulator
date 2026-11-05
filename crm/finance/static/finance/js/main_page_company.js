// ==================== CSRF-токен ====================
function getCookie(name) {
  let value = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return value ? value.pop() : "";
}
const csrftoken = getCookie("csrftoken");

const deletedIds = new Set();
let table;
const ORIGINALS = new Map();

const entryDirtyRows = new Set();
// const entryDeletedIds = new Set();   // ids of saved rows deleted in the table
const updatedData = new Map();

function markRowDirty(row) {
  entryDirtyRows.add(row.getData());
}

function markDirty(row, field) {
  const id = row.getData().id;
  if (!updatedData.has(id)) updatedData.set(id, {});
  updatedData.get(id)[field] = row.getData()[field];
}

const ENTRY_SAVE_FIELDS = ['name', 'slug', 'representative', 'pcm_price',
                        'plm_price', 'nob_price', 'tem_price', 'air_tem_price',
                        'lead_wipe_price', 'lead_air_price', 'vermi_price', 'mold_price'];


(async () => {
  table = new Tabulator("#company-main-info", {
    rowHeader: {
      resizable: false,
      frozen: true,
      width: 40,
      hozAlign: "center",
      formatter: "rownum",
      cssClass: "range-header-col",
      editor: false,
    },
    history:true, // history for undo/redo
    height: "100%",
    width: "100%",
    layout: "fitColumns",
    editTriggerEvent: "click",
    ajaxURL: URLS.companyPriceURL,
    pagination: "local",
    paginationSize: 200,
    paginationSizeSelector: [100, 200, 300],
    selectableRows:true,  
    columnDefaults: {
      headerHozAlign: "center",
      hozAlign: "center",
      vertAlign: "middle",
    },
    columns: [
      {
        title: "id",
        field: "id",
        visible: false,
      },
      {
        title: "slug",
        field: "slug",
        visible: false,
      },
      {
        title:"Company Name",  
        field:"name", 
        width:400, 
        editor: tabulatorTextEditor, 
        headerSort: false,
      },
      {
        title:"PCM Price",  
        field:"pcm_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"PLM Price",  
        field:"plm_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"NOB Price",  
        field:"nob_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"Prep. Price",  
        field:"prep_nob_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"TEM Price",  
        field:"tem_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"Air-TEM Price",  
        field:"air_tem_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"LEAD-Wipe Price",  
        field:"lead_wipe_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"LEAD-Air Price",  
        field:"lead_air_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"Vermi Price",  
        field:"vermi_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
      {
        title:"Mold Price",  
        field:"mold_price", 
        width:100, 
        editor: tabulatorNumberEditor, 
        headerSort: false,
      },
    ],
  });

  table.on("cellEdited", (cell) => { // in case cell edited
        markRowDirty(cell.getRow()); // add to dirty Rows
        if (cell.getRow().getData().id) { // if sample exists
          markDirty(cell.getRow(), cell.getField()); // mark cell dirty
        }
      });
})();

// =================== Detecting changes ===================
// saved rows deleted in the table and still gone (undo brings a deleted row back)
function getDeletedIds() {
  const presentIds = new Set(table.getRows().map(row => row.getData().id));
  return [...deletedIds].filter(id => !presentIds.has(id));
}

function entryHasChanges() {
  const rows = table.getRows().map(row => row.getData());
  return rows.some(data => !data.id || entryDirtyRows.has(data)) || getDeletedIds().length > 0;
}

function entryPayloadRow(data) {
  const row = {id: data.id};
  for (const field of ENTRY_SAVE_FIELDS) row[field] = data[field];
  return row;
}

// =================== Refresh table ===================
document
  .getElementById("main-menu-refresh-toggle")
  .addEventListener("click", function () {
  if (entryHasChanges() && !confirm("Unsaved changes will be lost. Continue?")) {
    return;
  }
  entryDirtyRows.clear();
  deletedIds.clear();
  updatedData.clear()
  showToast("Refreshed", "success");
    table.setData(URLS.companyPriceURL);
  });

  // =================== Create new row ===================
document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

document.getElementById("main-menu-save-toggle").addEventListener("click", saveChanges);

// =================== Save ===================
async function saveChanges() {
  const rows = table.getRows().map(row => row.getData());

  const payload = {
    updated: Array.from(updatedData, ([id, fields]) => ({
      id: Number(id), ...fields,
    })), //take json with updated data
    created: rows.filter(data => !data.id).map(entryPayloadRow), // take new samples
    deleted: [...deletedIds] // take only in the end deleted samples, they are not influence whole table
  };

  if (!payload.updated.length && !payload.created.length && !payload.deleted.length) {
    showToast("No changes to save", "info");
    return;
  }

  try {
    const res = await fetch(URLS.companyPriceURL, {
      method: "PATCH",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      await showResponseError(res);
      return;                                   // флаги не снимаем — правки живы
    }
    entryDirtyRows.clear();
    deletedIds.clear();
    updatedData.clear()

    const resultJSON = await res.json();

    let resultMessage = ''
    if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
    if (resultJSON.created) {resultMessage += `Created: ${resultJSON.created}`};
    if (resultJSON.deleted) {resultMessage += `Deleted: ${resultJSON.deleted}`};
    console.log(resultMessage)
    showToast(`Table Saved: ${resultMessage}`, "success");

  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  } finally {
    deletedIds.clear();
    table.setData(URLS.companyPriceURL);
  }
};

// ================== deleting rows =============

document.getElementById("main-menu-delete-toggle").addEventListener("click", function () {
  const rows = table.getSelectedRows();
  for (const row of rows ) {

    table.deleteRow(row.getIndex());
    deletedIds.add(row.getData().id);
    
  }
});

document.getElementById("main-menu-undo-toggle").addEventListener("click", function() {
  table.undo();
  deletedIds.clear();
    });

document.getElementById("main-menu-redo-toggle").addEventListener("click", function() {
  table.redo();
    });