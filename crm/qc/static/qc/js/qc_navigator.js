const root = document.querySelector('#qc-nav');
const container = root.querySelector('#nav-buttons');
const title = root.querySelector('#nav-title');
const backBtn = root.querySelector('#nav-back');
const rows = JSON.parse(document.querySelector('#nav-data').textContent);

const levels = [
  { key: 'analyst',       title: 'Analyst' },
  { key: 'qc_type',       title: 'QC Type' },
  { key: 'analysis_type', title: 'Type Sample' },
  { key: 'year',          title: 'Year' },
  { key: 'month',         title: 'Month',
    format: m => new Date(2000, m - 1).toLocaleString('en', { month: 'long' }) },
];

const selected = {};   // например {analyst: 3, qc_type: 1}
let current = 0;       // индекс текущего уровня

function matchingRows() {
  return rows.filter(row =>
    Object.entries(selected).every(([key, value]) => row[key] === value)
  );
}

function render() {
  const level = levels[current];
  const options = new Map();   // значение -> подпись, Map сам убирает дубликаты

  for (const row of matchingRows()) {
    const value = row[level.key];
    const label = level.format ? level.format(value) : (row[`${level.key}_label`] ?? value);
    options.set(value, label);
  }

  title.textContent = level.title;
  backBtn.hidden = current === 0;
  container.innerHTML = '';

  for (const [value, label] of options) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = label;
    btn.classList.add("menu-btn");
    btn.addEventListener('click', () => choose(level.key, value));
    container.append(btn);
  }
}

function choose(key, value) {
  selected[key] = value;

  if (current === levels.length - 1) {
    const params = new URLSearchParams(selected);
    window.location.href = `${root.dataset.tableUrl}?${params}`;
    return;
  }
  current++;
  render();
}

backBtn.addEventListener('click', () => {
  current--;
  delete selected[levels[current].key];
  render();
});

render();