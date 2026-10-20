const all_grid_ids = {A1 : "B1", C1 : "D1", E1 : "A2", B2 : "C2", D2 : "E2", 
                    A3 : "B3", C3 : "D3", E3 : "A4", B4 : "C4", D4 : "E4", 
                    A5 : "B5", C5 : "D5", E5 : "A6", B6 : "C6", D6 : "E6", 
                    A7 : "B7", C7 : "D7", E7 : "A8", B8 : "C8", D8 : "E8", 
                    A9 : "B9", C9 : "D9", E9 : "A10", B10 : "C10", D10 : "E10"}

let temTable;

(async () => { 
const optionsResponse = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await optionsResponse.json();

function checkTEMforPS(cell) {
  if (cell.getRow().getData().tem_na_or_ps != 'PS') return true
}

function fillTEMAsbResultSamplesSameHA (table, homo_area, type) {
    for (row of table ) {
        if (row.getData().homo_area  == homo_area) {
            if (type == 'fill') {
                row.update({tem_na_or_ps:'PS'})
            } else {
                row.update({tem_na_or_ps:''})
            };
        };
    };
}

temTable = new Tabulator("#samples-tem-table", {
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
        ajaxURL: URLS.temGetURL,
        selectableRange: true,
        selectableRangeColumns: true,
        selectableRangeRows: true,
        selectableRangeClearCells: true,
        editorEmptyValue: null,
        selectableRangeClearCellsValue: null,

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
              title:"IS QC", 
              field:"is_tem_qc_sample", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"IS Blank", 
              field:"is_blank", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample", 
              width: 80, 
              editable: false,
              headerSort: false,
            },
            {
              title:"LAB ID", 
              field:"lab_sample", 
              width: 130, 
              editable: false,
              headerSort: false,
            },
            {
              title:"Layer", 
              field:"layer", 
              width: 55, 
              editable: false,
              headerSort: false,
            },
            {
              title:"HA", 
              field:"homo_area", 
              width: 80, 
              editable: false,
              headerSort: false,
            },
            {
              title:"Residue", 
              field:"weight__residue", 
              width: 80, 
              editable: false,
              headerSort: false,
            }, 
            {
              title:"Asbestos<br>Type", 
              field:"tem_asb_type", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleAsbestosType'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: checkTEMforPS,
              editorParams: { values: tableOptions['sampleAsbestosType'] },
            },
            {
              title:"Visual<br>Estimation", 
              field:"tem_asb_point", 
              width: 90, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"Asbestos %", 
              field:"tem_asb_percent", 
              width: 100, 
              editable: false,
              headerSort: false,
            },

            {
              title:"Method", 
              field:"method", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleMethod'].map(o => [o.value, o.label])),
              headerSort: false,
              editable: false,
              editorParams: { values: tableOptions['sampleMethod'] },
            },
            {
              title:"Microscope<br>Alignment", 
              field:"tem_microscope_alignment", 
              width: 95, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Eccentricity<br>Adjusted", 
              field:"tem_eccentricity_adjusted", 
              width: 100, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Grid Pre<br>Acceptability", 
              field:"tem_grid_pre_acceptability", 
              width: 110, 
              editor: tabulatorTextEditor, 
              headerSort: false,
            },
            {
              title:"Grid <br> Box", 
              field:"tem_grid_box", 
              width: 90, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"Grid Box<br> ID I", 
              field:"tem_grid_box_id_1", 
              width: 90, 
              formatterParams: {'A1' : 'A1', 'C1':'C1'},
              editor: "list",
              headerSort: false,
              editable: checkTEMforPS,
              editorParams: {values: Object.keys(all_grid_ids),
                clearable:true,
              },
            },
            {
              title:"Grid Box<br> ID II", 
              field:"tem_grid_box_id_2", 
              width: 90, 
              editor: tabulatorTextEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"NA or PS", 
              field:"tem_na_or_ps", 
              width: 80, 
              editable: false,
              headerSort: false,
            },
          ],
      });

    temTable.on("tableBuilt", () => bindTypeToEdit(temTable)); 


    temTable.on("cellEdited", function(cell) {
        let currentRow = cell.getRow();
        const tableData = temTable.getRows();

        if (cell.getField() === 'tem_asb_point') {
          if ([2, 3, 4, 5, 6, 7].includes(currentRow.getData().tem_asb_type)) {
            result = Math.round((+(cell.getValue()) * (Number(currentRow.getData().weight__residue)) / 100 ) * 100) / 100;
            if (isFinite(result)) {
                currentRow.update({tem_asb_percent:result});
            }
            else {
                currentRow.update({tem_asb_percent:0});
            }
          };

          if (Number(currentRow.getData().tem_asb_percent) < 1) {
              let var_homogenity = cell.getRow().getData().homo_area;
              let getCurrentPosition = cell.getRow().getPosition() 
              fillTEMAsbResultSamplesSameHA(tableData.slice(getCurrentPosition), var_homogenity, 'delete');
          } else {
              let var_homogenity = cell.getRow().getData().homo_area;
              let getCurrentPosition = cell.getRow().getPosition() 
              fillTEMAsbResultSamplesSameHA(tableData.slice(getCurrentPosition), var_homogenity, 'fill');
          }
        };

        if (cell.getField() === 'tem_grid_box_id_1') {
          currentRow.update({tem_grid_box_id_2:all_grid_ids[cell.getValue()]});
        }
    });

})();

document.getElementById("tem-save-toggle").addEventListener("click", temSaveChanges);

async function temSaveChanges() {
    try {
      const response = await fetch(URLS.analysisUpdateURL, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(temTable.getData()),
      });

      if (!response.ok) {
        await showResponseError(response);
        return;                                   // флаги не снимаем — правки живы
      }

      showToast(`Table Saved `, "success");
    }
    catch (e) {
      showToast(`Error: ${e.message}`, "error");
    } finally {
      // entryDeletedIds.clear();
    };
};
