

(async () => { 
const optionsResponse = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await optionsResponse.json();

function checkTEMforPS(cell) {
  if (cell.getRow().getData().tem_na_or_ps != 'PS') return true
}

temTable = new Tabulator("#samples-tem-table", {
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
        ajaxURL: URLS.temGetURL,
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
              width: 40, 
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
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"Asbestos %", 
              field:"tem_asb_percent", 
              width: 80, 
            //   editor: weightEnterDownEditor, 
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
              width: 70, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Eccentricity<br>Adjusted", 
              field:"tem_eccentricity_adjusted", 
              width: 70, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Grid Pre<br>Acceptability", 
              field:"tem_grid_pre_acceptability", 
              width: 70, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Grid <br> Box", 
              field:"tem_grid_box", 
              width: 90, 
              editor: entryEnterDownEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"Grid Box<br> ID I", 
              field:"tem_grid_box_id_1", 
              width: 90, 
              editor: entryEnterDownEditor, 
              headerSort: false,
              editable: checkTEMforPS,
            },
            {
              title:"Grid Box<br> ID II", 
              field:"tem_grid_box_id_2", 
              width: 90, 
              editor: entryEnterDownEditor, 
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

    temTable.on("tableBuilt", () => bindTypeToEdit(temTable)); // bindTypeToEdit in plm_tem_analysis.js


    temTable.on("cellEdited", function(cell) {
        let currentRow = cell.getRow();
        const tableData = temTable.getRows();

        if (cell.getField() === 'asb_type') {
          if (cell.getValue() in [2, 3, 4, 5, 6, 7]) {
              // in case Chrysotile
            if (cell.getValue() == 2) {
                currentRow.update({morphology:1, 
                                    sign_of_elongation:1, 
                                    extinction_angle:1, 
                                    pleochroism_color:1, 
                                    birefringence:1});
            };
          };
        };

        if (cell.getField() === 'tem_asb_point') {
          if (currentRow.getData().asb_type in [2, 3, 4, 5, 6, 7]) {
              // in case Chrysotile
            if (cell.getValue() == 2) {
                currentRow.update({morphology:1, 
                                    sign_of_elongation:1, 
                                    extinction_angle:1, 
                                    pleochroism_color:1, 
                                    birefringence:1});
            };
          };
        };
    });

})();
