// Переключение темы
const themeSwitcher = document.querySelector('.theme-switcher');
const themeIcon = document.getElementById('theme-icon');
const body = document.body;

let currentTheme = 'light';

themeSwitcher.addEventListener('click', function() {
    // Переключаем между тремя темами: light, dark, system
    if (currentTheme === 'light') {
        currentTheme = 'dark';
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
    } else if (currentTheme === 'dark') {
        currentTheme = 'system';
        body.classList.remove('dark-theme');
        body.classList.add('system-theme');
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-adjust');
    } else {
        currentTheme = 'light';
        body.classList.remove('system-theme');
        body.classList.add('light-theme');
        themeIcon.classList.remove('fa-adjust');
        themeIcon.classList.add('fa-moon');
    }
    
    // Сохраняем выбор темы в localStorage
    localStorage.setItem('theme', currentTheme);
});

// Проверяем сохранённую тему при загрузке
if (localStorage.getItem('theme')) {
    currentTheme = localStorage.getItem('theme');
    
    if (currentTheme === 'dark') {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
    } else if (currentTheme === 'system') {
        body.classList.remove('light-theme');
        body.classList.add('system-theme');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-adjust');
    }
}

// Проверяем системные настройки темы
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

if (prefersDarkScheme.matches && currentTheme === 'system') {
    body.classList.add('system-theme');
} else if (currentTheme === 'system') {
    body.classList.remove('system-theme');
}
