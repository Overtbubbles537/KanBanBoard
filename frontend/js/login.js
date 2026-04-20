document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const passwordSection = document.getElementById('passwordSection');
    const twoFactorSection = document.getElementById('twoFactorSection');
    const loginButton = document.getElementById('loginButton');
    const verifyButton = document.getElementById('verifyButton');
    const backButton = document.getElementById('backButton');
    const errorMessage = document.getElementById('errorMessage');
    
    let userEmail = '';
    let userPassword = '';
    
    // Показать этап 2FA
    function showTwoFactorStep(show) {
        if (show) {
            passwordSection.style.display = 'none';
            twoFactorSection.classList.remove('hidden');
            loginButton.classList.add('hidden');
            verifyButton.classList.remove('hidden');
            backButton.classList.remove('hidden');
            errorMessage.textContent = '';
        } else {
            passwordSection.style.display = 'block';
            twoFactorSection.classList.add('hidden');
            loginButton.classList.remove('hidden');
            verifyButton.classList.add('hidden');
            backButton.classList.add('hidden');
            document.getElementById('twoFactorCode').value = '';
        }
    }
    
    // Показать ошибку
    function showError(message) {
        errorMessage.textContent = message;
    }
    
    // Этап 1: Отправка email и пароля
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Если мы на этапе 2FA, не обрабатываем submit
        if (!twoFactorSection.classList.contains('hidden')) {
            return;
        }
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            showError('Введите email и пароль');
            return;
        }
        
        userEmail = email;
        userPassword = password;
        
        showError('');
        loginButton.textContent = 'Проверка...';
        loginButton.disabled = true;
        
        fetch('http://localhost:8000/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            loginButton.textContent = 'Войти';
            loginButton.disabled = false;
            
            if (data.requires_2fa) {
                // Требуется код 2FA
                showTwoFactorStep(true);
                document.getElementById('twoFactorCode').focus();
            } else if (data.access_token) {
                // Успешный вход без 2FA
                localStorage.setItem('accessToken', data.access_token);
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                window.location.href = 'main.html';
            } else {
                showError(data.detail || 'Ошибка входа');
            }
        })
        .catch(error => {
            loginButton.textContent = 'Войти';
            loginButton.disabled = false;
            console.error('Ошибка:', error);
            showError('Неверный email или пароль');
        });
    });
    
    // Этап 2: Проверка 2FA кода
    verifyButton.addEventListener('click', function() {
        const code = document.getElementById('twoFactorCode').value.trim();
        
        if (!code || code.length < 6) {
            showError('Введите 6-значный код');
            return;
        }
        
        verifyButton.textContent = 'Проверка...';
        verifyButton.disabled = true;
        showError('');
        
        fetch('http://localhost:8000/auth/login/2fa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: userEmail,
                password: userPassword,
                code: code
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.access_token) {
                localStorage.setItem('accessToken', data.access_token);
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                window.location.href = 'main.html';
            } else {
                verifyButton.textContent = 'Проверить код';
                verifyButton.disabled = false;
                showError(data.detail || 'Неверный код');
                document.getElementById('twoFactorCode').value = '';
            }
        })
        .catch(error => {
            verifyButton.textContent = 'Проверить код';
            verifyButton.disabled = false;
            console.error('Ошибка:', error);
            showError('Ошибка проверки кода');
        });
    });
    
    // Кнопка "Назад" — вернуться к вводу пароля
    backButton.addEventListener('click', function() {
        showTwoFactorStep(false);
        loginButton.disabled = false;
        showError('');
    });
});