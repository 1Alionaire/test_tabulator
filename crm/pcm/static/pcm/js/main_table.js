
// ==================== Open Filter Tab ====================
const filterPanel = document.getElementById("main-section-filter");

document.getElementById("main-menu-filter-toggle").addEventListener("click", function (e) {
    filterPanel.classList.toggle('invisible');
    filterPanel.classList.toggle('visible-flex');
});

function getLabId(cell) {
  return cell.getRow().getData().lab_id;
}

let table;

(async () => {
    const response = await fetch(URLS.tableOptionsGetURL);
    const statusOptions = await response.json();

     table = new Tabulator("#main-info", {
        rowHeader: {
            resizable: false, frozen: true, width: 40,
            hozAlign: "center", formatter: "rownum",
            cssClass: "range-header-col", editor: false
        },
        footerElement: '<span id="main-rows-loaded"></span>' +
          '<button type="button" id="main-load-more" class="tabulator-page">Load more</button>',
        height: "100%",
        layout:"fitColumns",
        columnDefaults: {
          headerHozAlign: "center",
          hozAlign: "center",
          vertAlign: "middle",
          editable: false,
        },
        columns:[
            {
              title: "id",
              field: "id",
              visible: false,
            },
            {
              title: "lab_id_sort",
              field: "lab_id_sort",
              visible: false,
              sorter: "string"
            },
            {
              title:"Lab ID",
              field: "pcm_project_id",
              width: 100,
              headerSort: false,
              formatter: "link",
              formatterParams: {
                urlPrefix: "detail/",
                target: "_blank",
                label: getLabId,
              },
            },
            {
              title:"Date",
              field:"date_registered",
              formatter:formatDateMDY,
              width:110,
              headerSort: false,
            },
            {
              title:"Time",
              field:"time_registered",
              formatter:formatTimeHM,
              width:80 ,
              headerSort: false,
            },
            {
              title: "Company",
              field: "company",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['company'].map(o => [o.value, o.label])),
              headerSort: false,
              width: 150,
            },
            {
              title:"Project Name",
              field:"project_name",
              width:400,
              headerSort: false,
            },
            {
              title:"Project Address",
              field:"project_address",
              width:400,
              headerSort: false,
            },
            {
              title:"Samples",
              field:"number_samples",
              width: 75,
              headerSort: false,
            },
            {
              title: "TurnAround<br>Time",
              field: "turn_around_time",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['turn_around_time'].map(o => [o.value, o.label])),
              width: 90,
              headerSort: false,
            },
            {
              title: "Status",
              field: "status",
              formatter: "lookup",
              formatterParams: Object.fromEntries(statusOptions['status'].map(o => [o.value, o.label])),
              width: 80,
              headerSort: false,
            },
            {
              title:"Technician",
              field:"technician",
              width:100,
              headerSort: false,
            },
            {
              title:"Comment",
              field:"comment",
              width:100,
              headerSort: false,
            },
          ],
      });

     table.on("tableBuilt", () => {
       document.getElementById("main-load-more").addEventListener("click", loadNextPage);
       loadFirstPage();
     });

     // infinite scroll: подгружаем следующую страницу, когда до низа осталось меньше SCROLL_LOAD_MARGIN
     table.on("scrollVertical", (top) => {
       const holder = table.element.querySelector(".tabulator-tableholder");
       if (top + holder.clientHeight >= holder.scrollHeight - SCROLL_LOAD_MARGIN) loadNextPage();
     });
  })();

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

async function loadFirstPage(query = currentQuery) {
  const generation = ++loadGeneration;
  currentQuery = query;
  const params = new URLSearchParams(query);
  params.set('page_size', PAGE_SIZE);
  try {
    const page = await fetchPage(`${URLS.PCMProjectGetURL}?${params}`);
    if (generation !== loadGeneration) return;
    nextPageURL = page.next;
    await table.setData(page.results);
    updatePageFooter();
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
}

function updatePageFooter() {
  document.getElementById("main-rows-loaded").textContent =
    `Loaded: ${table.getDataCount()}${nextPageURL ? '' : ' (all)'}`;
  document.getElementById("main-load-more").style.display = nextPageURL ? '' : 'none';
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

// =================== Refresh table ===================
document.getElementById("main-menu-refresh-toggle").addEventListener("click", function() {
  table.setData(URLS.PCMProjectGetURL);
  showToast("Refreshed", "success");
  loadFirstPage();
});


//  ==================== Filter =================
function fillSelect(selector, items) {
  const select = document.querySelector(selector);
  select.innerHTML = '<option value="">— all —</option>';
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item.value;
    opt.label = item.label;
    select.append(opt);
  }
}

async function initFilterPanel() {
  const response = await fetch(URLS.tableOptionsGetURL);
  const result = await response.json();
  fillSelect("#filter-input-company", result['company']);
  fillSelect("#filter-input-status", result['status']);
  fillSelect("#filter-input-turn-around-time", result['turn_around_time']);
};

initFilterPanel();
const form = document.getElementById('filter-form');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  loadTable();
});

document.getElementById('filter-reset').addEventListener('click', () => {
  applyDefaults();
  loadTable();
});

// единственный источник правды для значений по умолчанию
function defaultFilters() {
  const year = new Date().getFullYear();
  return {
    date_registered__gte: `${year}-01-01`,
    date_registered__lte: `${year}-12-31`,
  };
}

function applyDefaults() {
  // 1. чистим все поля
  for (const el of form.elements) {
    if (!el.name) continue;                       // кнопки пропускаем
    if (el.tagName === 'SELECT') {
      for (const opt of el.options) opt.selected = false;
    } else {
      el.value = '';
    }
  }
  // 2. раскладываем дефолты
  for (const [name, value] of Object.entries(defaultFilters())) {
    const field = form.elements[name];
    if (field) field.value = value;
  }
}

function loadTable() {
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(form)) {
    if (value) params.append(key, value);
  }
  loadFirstPage(params);
}