let ASB_OIL_PARAMETERS = {2: {'delta':{19:'1.557', 20:'1.557',
                                        21:'1.556', 22:'1.556', 
                                        23: '1.555', 24: '1.555', 
                                        25: '1.554', 26: '1.554',
                                        27: '1.553'},
                                'alpha': {19:'1.552', 20:'1.552',
                                        21:'1.551', 22:'1.551', 
                                        23: '1.550', 24: '1.550', 
                                        25: '1.549', 26: '1.549', 
                                        27: '1.548'}}, 
                5: {'delta':{19:'1.626', 20:'1.626',
                                        21:'1.625', 22:'1.625', 
                                        23: '1.625', 24: '1.625', 
                                        25: '1.624', 26: '1.624', 
                                        27: '1.623'},
                                'alpha': {19:'1.611', 20:'1.611',
                                        21:'1.611', 22:'1.611', 
                                        23: '1.610', 24: '1.610', 
                                        25: '1.609', 26: '1.609', 
                                        27: '1.608'}}, 
                3: {'delta': {19:'1.700', 20:'1.700',
                                        21:'1.699',  22:'1.699',
                                        23: '1.698', 24: '1.698',
                                        25: '1.698', 26: '1.698', 
                                        27: '1.697'},
                                'alpha': {19:'1.682', 20:'1.682',
                                        21:'1.681', 22:'1.681',
                                        23: '1.680', 24: '1.680', 
                                        25: '1.679', 26: '1.679', 
                                        27: '1.678'}}}

// Оптические свойства по типу асбеста (значение select-редактора → дефолты)
const ASBESTOS_PARAMETERS = {
    2: {morphology: 1, sign_of_elongation: 1, extinction_angle: 1, pleochroism_color: 1, birefringence: 1}, // Chrysotile
    3: {morphology: 2, sign_of_elongation: 1, extinction_angle: 1, pleochroism_color: 1, birefringence: 2}, // Amosite
    4: {morphology: 2, sign_of_elongation: 2, extinction_angle: 1, pleochroism_color: 2, birefringence: 2}, // Crocidolite
    5: {morphology: 2, sign_of_elongation: 1, extinction_angle: 1, pleochroism_color: 1, birefringence: 2}, // Anthophyllite
    6: {morphology: 2, sign_of_elongation: 1, extinction_angle: 2, pleochroism_color: 1, birefringence: 2}, // Tremolite
    7: {morphology: 2, sign_of_elongation: 1, extinction_angle: 2, pleochroism_color: 1, birefringence: 2}, // Actinolite
};

let nobTable;

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
        height: '100%',
        
        width: "100%", 
        layout:"fitColumns",
        editTriggerEvent: "dblclick",
        ajaxURL: URLS.nobGetURL,
        selectableRange: true,
        selectableRangeColumns: true,
        selectableRangeRows: true,
        selectableRangeClearCells: true,
        selectableRangeClearCellsValue: null,   // Delete/Backspace по диапазону
        editorEmptyValue: null,      

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
              width: 55, 
              editable: false,
              headerSort: false,
            },
            {
              title:"Color", 
              field:"color", 
              width: 130, 
              editor: tabulatorTextEditor, 
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
              width: 100, 
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
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"RI ┴", 
              field:"ri_delta_oil", 
              width: 80, 
              editor: tabulatorNumberEditor, 
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
              width: 105, 
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
              width: 110, 
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
              width: 95, 
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
              editor: tabulatorNumberEditor, 
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
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 2", 
              field:"asb_point_2", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 3", 
              field:"asb_point_3", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 4", 
              field:"asb_point_4", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 5", 
              field:"asb_point_5", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 6", 
              field:"asb_point_6", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 7", 
              field:"asb_point_7", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            },
            {
              title:"Point 8", 
              field:"asb_point_8", 
              width: 80, 
              editor: tabulatorNumberEditor, 
              headerSort: false,
            }, 
            {
              title:"Asbestos %", 
              field:"asb_percent", 
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
                currentRow.update({field:50});
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
                                    ri_alpha_oil:null,
                                    ri_delta_oil:null,
                                    morphology:null, 
                                    sign_of_elongation:null, 
                                    extinction_angle:null, 
                                    pleochroism_color:null, 
                                    birefringence:null, 
                                    asb_percent:0,
                                    asb_point_1:50, 
                                    asb_point_2:50, 
                                    asb_point_3:50, 
                                    asb_point_4:50, 
                                    asb_point_5:50, 
                                    asb_point_6:50,
                                    asb_point_7:50,
                                    asb_point_8:50});
            };


            if (cell.getValue() in [2, 3, 4, 5, 6, 7]) {
                // in case Chrysotile
                temperature = cell.getRow().getData().analysis_temperature;
                const defaults = ASBESTOS_PARAMETERS[cell.getValue()];
                currentRow.update({ri_alpha_oil: ASB_OIL_PARAMETERS[cell.getValue()]['alpha'][temperature]})
                currentRow.update({ri_delta_oil: ASB_OIL_PARAMETERS[cell.getValue()]['delta'][temperature]})
                if (defaults) {
                    currentRow.update({...defaults});
                }
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

        if (cell.getField() == 'asb_point_5' || cell.getField() == 'asb_point_6' || cell.getField() == 'asb_point_7' || cell.getField() == 'asb_point_8') {
          if (currentRow.getData().asb_type in [2, 3, 4, 5, 6, 7]) {
            let count_points = 0
            if (currentRow.getData().asb_point_5 != 50) count_points += 1
            if (currentRow.getData().asb_point_6 != 50) count_points += 1
            if (currentRow.getData().asb_point_7 != 50) count_points += 1
            if (currentRow.getData().asb_point_8 != 50) count_points += 1
            let asbestoCulcResult = Math.round((count_points / 4) * 100) / 100;
            if (isFinite(asbestoCulcResult)) {
                currentRow.update({asb_percent:asbestoCulcResult});
            }
            else {
                currentRow.update({asb_percent:0});
            }
          };
        };
    });

})();

document.getElementById("nob-save-toggle").addEventListener("click", nobSaveChanges);
async function nobSaveChanges() {
    try {
      const response = await fetch(URLS.analysisUpdateURL, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrftoken},
        body: JSON.stringify(nobTable.getData()),
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
      entryDeletedIds.clear();
    };
};

document.querySelector('.plm-analysis-temperature-select').addEventListener("change", function(e) {
  newTemperature = e.target.value
  const tableData = nobTable.getRows();
  console.log(`newTemperature : ${newTemperature}`);
  for (row of tableData ) {
    row.update({analysis_temperature:+newTemperature})
  };
});

// ========================== Parse Temperature from server ====================
fetch(URLS.temperatureGetURL)
    .then(r => r.json())
    .then(temperature => {
        document.querySelector(".plm-analysis-temperature-select").value = +temperature;
    });
    
// ========================== Parse project dates from server ====================
(async () => {
  const response = await fetch(URLS.projectDateGetURL);
  const data = await response.json();

  if (data.date_collect) {
    document.getElementById("data-entry-date-collected").value = data.date_collect;
  }
  if (data.date_analyze) {
    document.getElementById("nob-date-analysis").value = data.date_analyze;
  }
  if (data.date_review) {
    document.getElementById("nob-date-review").value = data.date_review;
  }
})();

// ========================== Update project dates ====================
document.getElementById("data-entry-date-collected-btn-confirm").addEventListener('click', () => plmProjectDateUpdate('date_collect'));
document.getElementById("nob-date-analysis-btn-confirm").addEventListener('click', () => plmProjectDateUpdate('date_analyze'));
document.getElementById("nob-date-review-btn-confirm").addEventListener('click', () => plmProjectDateUpdate('date_review'));

async function plmProjectDateUpdate(selectTypeDate) {
  let payload;
  if (selectTypeDate == 'date_collect') {
    payload = JSON.stringify({'date_collect': document.getElementById("data-entry-date-collected").value})
  }
  else if (selectTypeDate == 'date_analyze') {
    payload = JSON.stringify({'date_analyze': document.getElementById("nob-date-analysis").value})
  }
  else if (selectTypeDate == 'date_review') {
    payload = JSON.stringify({'date_review': document.getElementById("nob-date-review").value})
  }
    return fetch(URLS.projectDateUpdateURL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
        body: payload,
    })
    .then(r => r.json())
    .then(result => {
        if (result.status === "ok") {
            showToast(`Dates saved`, "success");
        } else {
            showToast(`Error saving. Try again`, "error");
        }
    })
    .catch(console.log('No Success'));
}


function isEmpty(value) {
  return value === null || value === undefined || String(value).trim() === "";
}

const overlays = document.querySelectorAll(".table-overlay");
document.querySelectorAll(".take-btn").forEach(btn => {
  btn.addEventListener("click", analystTakeProject);
});


async function checkProjectAnalyst() {
  try {
    const res = await fetch(URLS.projectAnalystGetURL);
    if (!res.ok) throw new Error(res.status);

    const data = await res.json();
    overlays.forEach(function (element) {
      element.hidden = !isEmpty(data.analyst);
    });
    document.getElementById("nob-analyst-username").textContent = data.analyst;
  } catch {
    console.error("checkProjectAnalyst:", err);
  }
};

async function analystTakeProject(selectTypeDate) {
  try {
    const res = await fetch(URLS.projectAnalystUpdateURL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Не удалось взять проект", "error");
      return;
    }
    overlays.forEach(function (element) {
      element.hidden = !isEmpty(data.analyst);
    })
    checkProjectAnalyst();
    //nob-analyst-username
    showToast("The project has been picked up for work", "success");
  } catch {
    showToast("Error", "error");
  } 
};

checkProjectAnalyst();

// ========================== Parse project dates from server ====================
(async () => {
  const response = await fetch(URLS.projectReviewerListGetURL);
  const data = await response.json();

  const select = document.getElementById("nob-analysis-reviewer-list");
  const { current, ...users } = data;

  const frag = document.createDocumentFragment();

  const placeholder = new Option("— choose —", "");
  placeholder.disabled = true;
  placeholder.selected = current == null;
  frag.append(placeholder);

  let matched = false;

  for (const [id, username] of Object.entries(users)) {
    const opt = new Option(username, id);
    if (username === current) {
      opt.selected = true;
      matched = true;
    }
    frag.append(opt);
  }

  // текущий ревьюер есть, но его нет в списке — добавляем, иначе выбор потеряется
  if (current != null && !matched) {
    const opt = new Option(`${current}`, "");
    opt.selected = true;
    frag.append(opt);
  }

  select.innerHTML = "";
  select.append(frag);
})();

document.getElementById("nob-choose-reviewer-btn-confirm").addEventListener('click', () => updateProjectReviewer());

async function updateProjectReviewer() {
    return fetch(URLS.projectReviewerUpdateRL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({'reviewed_by': document.getElementById("nob-analysis-reviewer-list").value}),
    })
    .then(r => r.json())
    .then(result => {
        if (result.status === "ok") {
          showToast(`Reviewer updated`, "success");
        } else {
          showToast(`Error. Try again later`, "error");
        }
    })
    .catch(showToast(`Error. Try again later`, "error"));
};


document.getElementById("nob-qc-generate-toggle").addEventListener("click", async (e) => {
  e.target.disabled = true;
  try {
    const res = await fetch(URLS.qcGenerateSamplesURL, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    nobTable.replaceData();          // перезапросить таблицу с сервера
    showToast("QC Samples generated", "success");
  } catch (err) {
    console.error(err);
    showToast(err.message, "error");
  } finally {
    e.target.disabled = false;
  }
});
