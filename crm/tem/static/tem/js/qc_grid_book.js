// ==================== Generate table ====================
const ORIGINALS = new Map();
let table;

(async () => { 
     table = new Tabulator("#main-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        history:true, // history for undo/redo
        height: "100%", // height
        width: "100%",  // width 
        layout:"fitColumns", // layout 
        editTriggerEvent: "click", // edit trigger for editing
        ajaxURL: URLS.temQCGridBoxGetURL, // URL for request 
        pagination:"local", // pagination
        paginationSize: 400, 
        paginationSizeSelector:[100, 200, 300], 
        selectableRows:true,  
        columnDefaults: {
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle",
        },
        columns:[
          {
              title: "id", 
              field: "id", 
              visible: false, 
            },
            {
              title: "position",  
              field: "position", 
              visible: false, 
              sorter: "string"
            },
            {
              title:"year", 
              field:"year", 
              width: 80, 
              editable: false, 
              headerSort: false,
              
            },
            {
              title:"Grid Box", 
              field:"grid_box", 
              editable: false, 
              width:120, 
            },
            {
              title:"Grid ID I", 
              field:"grid_id_1", 
              editable: false, 
              width:120, 
            },
            {
              title:"Grid ID II", 
              field:"grid_id_2", 
              editable: false, 
              width:120, 
            },
            {
              title:"Project", 
              field:"plm_tem_project__project__lab_id", 
              editable: false, 
              width:120, 
            },
            {
              title:"Sample", 
              field:"plm_tem_sample__lab_sample", 
              editable: false, 
              width:120, 
            },
          ],
      });
  })();
