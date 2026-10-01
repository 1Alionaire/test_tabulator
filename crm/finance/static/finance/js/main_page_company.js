// ==================== CSRF-токен ====================
function getCookie(name) {
  let value = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return value ? value.pop() : "";
}
const csrftoken = getCookie("csrftoken");

function getLabId(cell) {
  return cell.getRow().getData().lab_id;
}

const deletedIds = new Set();
let table;
const ORIGINALS = new Map();

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
    ajaxURL: URLS.companyPriceGetURL,
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
})();

// =================== Refresh table ===================
document
  .getElementById("main-menu-refresh-toggle")
  .addEventListener("click", function () {
    const changes = collectChanges(); // collecting all changes
    const hasChanges =
      changes.updated.length ||
      changes.created.length ||
      changes.deleted.length; //put all possible changes in const
    if (hasChanges && !confirm("Unsaved changes will be lost. Continue?")) {
      //asking user for continue if we have changes
      return;
    }
    table.setData(URLS.mainProjectGetURL);
  });

  // =================== Create new row ===================
document.getElementById("main-menu-create-toggle").addEventListener("click", function () {
  table.addRow({ _isNew: true }, true);
});

document.getElementById("main-menu-save-toggle").addEventListener("click", saveChanges);

// =================== Save ===================
function collectChanges() {
  const updatedData = {};
  const createdData = {};
  
  for (const cell of table.getEditedCells()) {  // going through all edited cells
    const data = cell.getRow()?.getData();  //parse data from whole row?
    console.log(data);
    if (!data || !data.name) continue; // if we dont have data -> continue

    const companyName = String(data.name);          // единый тип ключа
    const systemId = String(data.id); 

    if (isEmpty(systemId)) {
      if (companyName in createdData) {
        createdData[companyName].fields[cell.getField()] = cell.getValue();
        }
      else {
        entry = {lab_id: companyName, fields: {}, version: ORIGINALS.get(companyName)};
        createdData[companyName] = entry;
        createdData[companyName].fields[cell.getField()] = cell.getValue();
      }
    }
    else {
      if (systemId in updatedData) {
        updatedData[systemId].fields[cell.getField()] = cell.getValue();
      }
      else {
        entry = {id: systemId, fields: {}, version: ORIGINALS.get(systemId)};
        updatedData[systemId] = entry;
        updatedData[systemId].fields[cell.getField()] = cell.getValue();
      }
    };
  }

    const result = {
      updated: Object.values(updatedData),
      created: Object.values(createdData),
      deleted: [...deletedIds]
    };
  return result;
}

async function saveChanges() {
  const changes = collectChanges();
  if (!changes.updated.length && !changes.created.length && !changes.deleted.length) {
    console.log('no changes?');
    return;
  }

  if (changes.deleted.length && !confirm("Projects will be deleted. Continue?")) return

  try {
    const res = await fetch(URLS.companyPriceUpdateURL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
      body: JSON.stringify(changes),
    });

    if (!res.ok) {
      await showResponseError(res);
      return;                                   // флаги не снимаем — правки живы
    }

    table.getEditedCells().forEach(cell => {
      cell.clearEdited();
      cell.getElement().classList.remove("dirty");
    });

    const resultJSON = await res.json();

    let resultMessage = ''
    if (resultJSON.updated) {resultMessage += `Updated: ${resultJSON.updated}`};
    if (resultJSON.created) {resultMessage += `Created: ${resultJSON.created}`};
    if (resultJSON.deleted) {resultMessage += `Deleted: ${resultJSON.deleted}`};
    console.log(resultMessage)
    showToast(`Table Saved: ${resultMessage}`, "success");


  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
    console.log(e)
  } finally {
    deletedIds.clear();
    table.setData();
  }
};