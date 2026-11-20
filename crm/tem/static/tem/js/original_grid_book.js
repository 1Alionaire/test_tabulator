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
        // ajaxURL: URLS.temOriginalGridBoxGetURL, // URL for request
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
              editor: tabulatorTextEditor,
              width:120, 
            },
            {
              title:"Sample", 
              field:"plm_tem_sample__lab_sample", 
              editor: tabulatorTextEditor,
              width:120, 
            },
          ],
      });

     table.on("tableBuilt", () => {
       // document.getElementById("main-load-more").addEventListener("click", loadNextPage);
       loadFirstPage();
     });
  })();

// ==================== Cursor pagination ====================
// API отдаёт {next, previous, results}; next — готовый URL следующей страницы (курсор + фильтры)
const PAGE_SIZE = 200;
const SCROLL_LOAD_MARGIN = 300;
let currentQuery = '';   // фильтры текущего набора данных
let nextPageURL = null;  // null — последняя страница уже загружена
let pageLoading = false;
let loadGeneration = 0;  // ответы на запросы до смены фильтров отбрасываем


async function fetchPage(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`load failed (${res.status})`);
  return res.json();
}

function updatePageFooter() {
  document.getElementById("main-rows-loaded").textContent =
    `Loaded: ${table.getDataCount()}${nextPageURL ? '' : ' (all)'}`;
  document.getElementById("main-load-more").style.display = nextPageURL ? '' : 'none';
}

async function loadFirstPage(query = currentQuery) {
  const generation = ++loadGeneration;
  currentQuery = query;
  const params = new URLSearchParams(query);
  params.set('page_size', PAGE_SIZE);
  try {
    const page = await fetchPage(`${URLS.temOriginalGridBoxGetURL}?${params}`);
    if (generation !== loadGeneration) return;
    nextPageURL = page.next;
    await table.setData(page.results);
    updatePageFooter();
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
}

async function loadNextPage() {
  if (!nextPageURL || pageLoading) return;
  pageLoading = true;
  const generation = loadGeneration;
  try {
    const page = await fetchPage(nextPageURL);
    if (generation !== loadGeneration) return;
    nextPageURL = page.next;
    // строка могла сместиться между запросами (сменили lab_id) — дубли не добавляем
    const loadedIds = new Set(table.getData().map(r => r.id));
    const rows = page.results.filter(r => !loadedIds.has(r.id));
    if (rows.length) {
      // addData, а не setData — несохранённые правки в уже загруженных строках остаются
      await table.addData(rows, false);
      // addData пишет каждую строку в историю — без очистки Undo удалял бы подгруженные строки
      table.clearHistory();
    }
    updatePageFooter();
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  } finally {
    pageLoading = false;
  }
}
