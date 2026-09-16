let nobAnalysisTable;

function fillAsbResultSamplesSameHA (table, homo_area, type) {
    for (row of table ) {
        if (row.getData().homo_area  == homo_area) {
            if (type == 'fill') {
                row.update({asb_type:8})
            } else {
                row.update({asb_type:1})
            };
        };
    };
}

function fillTEMPSSamplesSameHA (table, homo_area, type) {
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

(async () => { 
const optionsResponse = await fetch(URLS.tableOptionsGetURL);
const tableOptions = await optionsResponse.json();

nobTable = new Tabulator("#samples-nob-table", {
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
        ajaxURL: URLS.nobGetURL,
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
              title:"NA or PS for TEM", 
              field:"tem_na_or_ps", 
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
              title:"Color", 
              field:"color", 
              width: 130, 
              editor: entryEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Texture", 
              field:"texture", 
              width: 130, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleTexture'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleTexture'] },
            },
            {
              title:"HA", 
              field:"homo_area", 
              width: 80, 
              editable: false,
              headerSort: false,
            },
            {
              title:"Morphology", 
              field:"morphology", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleMorphology'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleMorphology'] },
            },
            {
              title:"RI II", 
              field:"ri_alpha_oil", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"RI ┴", 
              field:"ri_delta_oil", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Sign of<br>Elong", 
              field:"sign_of_elongation", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleSignElong'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleSignElong'] },
            },
            {
              title:"Extinc<br>Angle", 
              field:"extinction_angle", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleExtincAngle'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleExtincAngle'] },
            },
                        {
              title:"Pleochroism<br>Color", 
              field:"pleochroism_color", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['samplePleochColor'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['samplePleochColor'] },
            },
            {
              title:"Birefringence", 
              field:"birefringence", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleBirefringence'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleBirefringence'] },
            },
            {
              title:"Other Fiber", 
              field:"other_fiber", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleOtherFiber'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleOtherFiber'] },
            },
            {
              title:"Property", 
              field:"other_fiber_property", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleOtherFiberProperty'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleOtherFiberProperty'] },
            },
            {
              title:"Other<br>Fiber%", 
              field:"other_fiber_percent", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Asbestos<br>Type", 
              field:"asb_type", 
              width: 80, 
              formatter: "lookup",
              formatterParams: Object.fromEntries(tableOptions['sampleAsbestosType'].map(o => [o.value, o.label])),
              editor: "list",
              headerSort: false,
              editable: true,
              editorParams: { values: tableOptions['sampleAsbestosType'] },
            },
            {
              title:"Point 1", 
              field:"asb_point_1", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 2", 
              field:"asb_point_2", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 3", 
              field:"asb_point_3", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 4", 
              field:"asb_point_4", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 5", 
              field:"asb_point_5", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 6", 
              field:"asb_point_6", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 7", 
              field:"asb_point_7", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            },
            {
              title:"Point 8", 
              field:"asb_point_8", 
              width: 80, 
              editor: weightEnterDownEditor, 
              headerSort: false,
            }, 
            {
              title:"Asbestos %", 
              field:"asb_percent", 
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
              title:"Residue", 
              field:"weight__residue", 
              width: 80, 
              editable: false,
              headerSort: false,
            }, 
          ],
      });

    nobTable.on("tableBuilt", () => bindTypeToEdit(nobTable)); // bindTypeToEdit in plm_nob_analysis.js

    nobTable.on("cellEditing", function(cell) {
        let currentRow = cell.getRow();
        if (cell.getField() == 'asb_point_1' || cell.getField() == 'asb_point_2' || cell.getField() == 'asb_point_3' || cell.getField() == 'asb_point_4' 
        || cell.getField() == 'asb_point_5' || cell.getField() == 'asb_point_6' || cell.getField() == 'asb_point_7' || cell.getField() == 'asb_point_8')  {
            if (cell.getValue() == null) {
                let field = cell.getField();
                currentRow.update({field:0});
            };
        };
    });

    nobTable.on("cellEdited", function(cell) {
        let currentRow = cell.getRow();
        const tableData = nobTable.getRows();

        if (cell.getField() === 'other_fiber') {
            if (cell.getValue() == null) {currentRow.update({other_fiber_property:null})};
            if (cell.getValue() == 1) {currentRow.update({other_fiber_property:1})};
            if (cell.getValue() == 2) {currentRow.update({other_fiber_property:2})};
            if (cell.getValue() == 3) {currentRow.update({other_fiber_property:4})};
            if (cell.getValue() == 4) {currentRow.update({other_fiber_property:3})};
        };

        if (cell.getField() === 'asb_type') {
            if (cell.getValue() == null || cell.getValue() == 1  ) {
                let var_homogenity = cell.getRow().getData().homo_area;
                let getCurrentPosition = cell.getRow().getPosition();

                fillAsbResultSamplesSameHA(tableData.slice(getCurrentPosition), var_homogenity, 'delete');
                fillTEMPSSamplesSameHA(tableData, var_homogenity, 'delete' )
                currentRow.update({asb_type:1,
                                    morphology:null, 
                                    sign_of_elongation:null, 
                                    extinction_angle:null, 
                                    pleochroism_color:null, 
                                    birefringence:null, 
                                    asb_percent:0,
                                    asb_point_1:0, 
                                    asb_point_2:0, 
                                    asb_point_3:0, 
                                    asb_point_4:0, 
                                    asb_point_5:0, 
                                    asb_point_6:0,
                                    asb_point_7:0,
                                    asb_point_8:0});
            };


            if (cell.getValue() in [2, 3, 4, 5, 6, 7]) {
                // in case Chrysotile
                if (cell.getValue() == 2) {
                    currentRow.update({morphology:1, 
                                        sign_of_elongation:1, 
                                        extinction_angle:1, 
                                        pleochroism_color:1, 
                                        birefringence:1});
                };
                // in case Amosite
                if (cell.getValue() == 3) {
                    currentRow.update({morphology:2, 
                                        sign_of_elongation:1, 
                                        extinction_angle:1, 
                                        pleochroism_color:1, 
                                        birefringence:2});
                };
                // in case Crocidolite
                if (cell.getValue() == 4) {
                    currentRow.update({morphology:2, 
                                        sign_of_elongation:2, 
                                        extinction_angle:1, 
                                        pleochroism_color:2, 
                                        birefringence:2});
                };
                // in case Anthophillite
                if (cell.getValue() == 5) {
                    currentRow.update({morphology:2, 
                                        sign_of_elongation:1, 
                                        extinction_angle:1, 
                                        pleochroism_color:1, 
                                        birefringence:2});
                };
                // in case Tremolite
                if (cell.getValue() == 6) {
                    currentRow.update({morphology:2, 
                                        sign_of_elongation:1, 
                                        extinction_angle:2, 
                                        pleochroism_color:1, 
                                        birefringence:2});
                };
                // in case Actinolite
                if (cell.getValue() == 7) {
                    currentRow.update({morphology:2, 
                                        sign_of_elongation:1, 
                                        extinction_angle:2, 
                                        pleochroism_color:1, 
                                        birefringence:2});
                };           
            };
        };

        if (cell.getField() == 'asb_point_1' || cell.getField() == 'asb_point_2' || cell.getField() == 'asb_point_3' || cell.getField() == 'asb_point_4') {
            if (currentRow.getData().asb_type in [2, 3, 4, 5, 6, 7]) {
                let totalPoints = Number(currentRow.getData().asb_point_1) + Number(currentRow.getData().asb_point_2) + Number(currentRow.getData().asb_point_3) + Number(currentRow.getData().asb_point_4);
                if (currentRow.getData().method == 1) {
                    let asbestoCulcResult = Math.round((400 / totalPoints) * 100) / 100;
                    if (isFinite(asbestoCulcResult)) {
                        currentRow.update({asb_percent:asbestoCulcResult});
                    }
                    else {
                        currentRow.update({asb_percent:0});
                    }
                } else { // * 100 * Number(currentRow.getData().weight__residue)
                    let asbestoCulcResult = Math.round((400 / totalPoints) * Number(currentRow.getData().weight__residue) ) / 100;
                    
                    if (isFinite(asbestoCulcResult)) {
                        currentRow.update({asb_percent:asbestoCulcResult});
                    }
                    else {
                        currentRow.update({asb_percent:0});
                    }
                }

                if (Number(currentRow.getData().asb_percent) < 1) {
                    let var_homogenity = cell.getRow().getData().homo_area;
                    let getCurrentPosition = cell.getRow().getPosition() 
                    fillAsbResultSamplesSameHA(tableData.slice(getCurrentPosition), var_homogenity, 'delete');
                    fillTEMPSSamplesSameHA(tableData, var_homogenity, 'delete' )
                } else {
                    let var_homogenity = cell.getRow().getData().homo_area;
                    let getCurrentPosition = cell.getRow().getPosition() 
                    fillAsbResultSamplesSameHA(tableData.slice(getCurrentPosition), var_homogenity, 'fill');
                    fillTEMPSSamplesSameHA(tableData, var_homogenity, 'fill' )
                }

            };
        };
        
    });
})();


document.getElementById("nob-save-toggle").addEventListener("click", nobSaveChanges);

async function nobSaveChanges() {
    try {
      const response = await fetch(URLS.nobUpdateURL, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(nobTable.getData()),
      });

      if (response.status === 422) {
        showErrors((await response.json()).errors);
        return;                                   // флаги не снимаем — правки живы
      }
      if (!response.ok) {
        console.error("STATUS:", response.status, "BODY:", await response.text());
        return;
      }
    }
    catch (e) {
      console.log(e);
    } finally {
      entryDeletedIds.clear();
    };
};
