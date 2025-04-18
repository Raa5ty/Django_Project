// Обработка кнопки перехода к форме
const startTestButton = document.getElementById('start-test-button');

if (startTestButton) {
    const url = startTestButton.dataset.url;
    startTestButton.addEventListener('click', function () {
        fetchPageContent(url);
    });
}


// Обработка формы
const startTestBtn = document.getElementById('start-test-btn');

startTestBtn.addEventListener('click', function() {
    // В реальном приложении здесь была бы валидация и отправка формы
    alert('Анкета сохранена! Вы будете перенаправлены на страницу тестирования.');
    
    // Переключаемся на страницу тестирования
    sidebarLinks.forEach(item => {
        item.classList.remove('active');
    });
    
    document.querySelector('.sidebar-link[data-page="testing"]').classList.add('active');
    
    pages.forEach(page => {
        page.style.display = 'none';
    });
    
    document.getElementById('testing-page').style.display = 'block';
});
