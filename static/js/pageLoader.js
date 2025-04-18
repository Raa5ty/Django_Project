
// Переключение между страницами с подгрузкой контента
const sidebarLinks = document.querySelectorAll('.sidebar-link');

// Функция для обновления активного класса
function updateActiveLink() {
    const path = window.location.pathname;
    sidebarLinks.forEach(link => {
        // Убираем активный класс у всех
        link.classList.remove('active');
        // Добавляем active классу той ссылки, чей путь соответствует текущему URL
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });
}
// Функция для загрузки контента страницы
function fetchPageContent(url) {
    fetch(url)
        .then(response => response.text()) // Получаем HTML-код страницы
        .then(html => {
            // Вытаскиваем только содержимое <body> (без <head>, <html>)
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const newContent = doc.querySelector('.main-content').innerHTML;
            // Обновляем контент в текущей странице
            document.querySelector('.main-content').innerHTML = newContent;
            // Обновляем URL в адресной строке без перезагрузки страницы
            history.pushState(null, '', url);
            // Обновляем активную ссылку в боковом меню
            updateActiveLink();
        })
        .catch(error => console.error('Ошибка загрузки:', error));
}
// Вызовем эту функцию при загрузке страницы и при подгрузке нового контента
updateActiveLink();


sidebarLinks.forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();

        // Удаляем активный класс у всех ссылок
        sidebarLinks.forEach(item => item.classList.remove('active'));
        this.classList.add('active');

        // Получаем URL из атрибута href
        const url = this.getAttribute('href');

        // Используем функцию для загрузки контента страницы
        fetchPageContent(url);
    });
});

// Обработчик для кнопок "Назад" и "Вперёд"
window.addEventListener('popstate', function () {
    const path = window.location.pathname;
    fetchPageContent(path);
});