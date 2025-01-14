document.addEventListener('DOMContentLoaded', function () {
    const installerSelect = document.getElementById('installer'); // Заменено executor → installer
    const installerInfo = document.getElementById('installer-info'); // Заменено executor-info → installer-info
    const montageDateInput = document.getElementById('montage_date');
    let calendar; // Переменная для хранения экземпляра календаря

    // Загружаем информацию об исполнителе при выборе
    installerSelect.addEventListener('change', function () {
        const installerId = this.value; // Заменено executorId → installerId
        if (!installerId) {
            installerInfo.textContent = 'Информация об исполнителе будет загружена...';
            return;
        }

        // AJAX-запрос на получение информации об исполнителе
        fetch(`/installer/info?installer_id=${installerId}`) // Заменено executor_id → installer_id
            .then(response => response.json())
            .then(data => {
                installerInfo.textContent = `Имя: ${data.name}, Роль: ${data.role}, Занятость: ${data.tasks} задач.`;
                loadCalendar(installerId); // Заменено executorId → installerId
            })
            .catch(error => {
                console.error('Ошибка при загрузке информации об исполнителе:', error);
                installerInfo.textContent = 'Ошибка при загрузке информации.';
            });
    });

    // Инициализация календаря
    function loadCalendar(installerId) { // Заменено executorId → installerId
        const calendarEl = document.getElementById('calendar');
        if (calendar) {
            calendar.destroy(); // Уничтожаем существующий экземпляр
        }
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            events: `/calendar/data?mode=installer&installer_id=${installerId}`, // Заменено mode=executor → mode=installer
            dateClick: function (info) {
                montageDateInput.value = info.dateStr; // Устанавливаем дату при клике
            }
        });
        calendar.render();
    }
});
