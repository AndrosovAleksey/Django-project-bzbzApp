document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('asset-search');
    const stockFigi = document.getElementById('stock_figi');
    const bondFigi = document.getElementById('bond_figi');

    // Обработка клика на элемент списка
    document.querySelectorAll('.asset-item').forEach(item => {
        item.addEventListener('click', function () {
            const type = this.dataset.type;
            const value = this.dataset.value;
            const text = this.textContent.trim(); // Удаляем пробелы

            // Обновляем поле ввода и скрытые поля
            searchInput.value = text; // Без пробелов
            if (type === 'stock') {
                stockFigi.value = value;
                bondFigi.value = ''; // Очищаем другое поле
            } else {
                bondFigi.value = value;
                stockFigi.value = ''; // Очищаем другое поле
            }

            // Скрываем выпадающий список
            bootstrap.Dropdown.getInstance(searchInput).hide();
        });
    });

    // Фильтрация при вводе текста
    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase().trim(); // Удаляем пробелы
        document.querySelectorAll('.asset-item').forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });
});