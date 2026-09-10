

let weightTable;

(async () => { 

weightTable = new Tabulator("#samples-weight-table", {
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
        ajaxURL: URLS.weightGetURL,
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
              field:"sample__row_number", 
              width: 80, 
              headerSort: false,
              visible: false
            },
            {
              title:"Client ID", 
              field:"client_sample", 
              width: 150, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Crucible", 
              field:"w_crucible", 
              width: 120, 
              editor:"number", 
              headerSort: false,
            },

            {
              title:"Crucible with sample", 
              field:"w_crucible_with_sample", 
              width: 120, 
              editor:"input", 
              headerSort: false,
              
            },
            {
              title:"Sample Weight", 
              field:"w_sample", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Sample Ashed", 
              field:"w_sample_ashed", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Organic", 
              field:"org", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Petri", 
              field:"w_petri", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Petri with Sample", 
              field:"w_petri_with_sample", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"Residue", 
              field:"residue", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
            {
              title:"CACO3", 
              field:"caco3", 
              width: 120, 
              editor:"input", 
              headerSort: false,
            },
          ],
      });
})();