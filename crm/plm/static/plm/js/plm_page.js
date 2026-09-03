// ==================== Переключение вкладок ====================
console.log('Test');
const tabNav = document.querySelector('.control-panel');
tabNav.addEventListener('click', function(e) {
    const btn = e.target.closest('.panel-btn');
    if (!btn) return;
    const index = [...tabNav.children].indexOf(btn);
    tabNav.querySelectorAll('.panel-btn').forEach((b, j) => b.classList.toggle('active', j === index));
    document.querySelectorAll('.tab-content').forEach((p, j) => p.classList.toggle('active', j === index));

    // Перерисовать таблицу при показе вкладки
    // if (index === 1) dataEntryTable.redraw(true);
    // if (index === 2) weightTable.redraw(true);
});