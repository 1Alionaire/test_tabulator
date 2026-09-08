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
        editTriggerEvent: "click",
        ajaxURL: URLS.dataEntryGetURL,
        selectableRows:true, 
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


