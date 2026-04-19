document.addEventListener('DOMContentLoaded', function(){
    const form = document.getElementById('registerForm');
    
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const nickname = document.getElementById('nickname').value;
        const email = document.getElementById('email').value;
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;

        // Валидация
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Неверный email');
            return;
        }

        if (password1.length < 6) {
            alert('Пароль должен быть минимум 6 символов');
            return;
        }

        if (password1 !== password2) {
            alert('Пароли не совпадают');
            return;
        }

        // Отправляем POST запрос
        fetch('http://localhost:8000/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: nickname,
                email: email,
                password: password1
            })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else if (response.status === 400) {
                throw new Error('Пользователь с таким email уже существует');
            } else {
                throw new Error('Ошибка регистрации');
            }
        })
        .then(data => {
            alert('Регистрация успешна! Теперь войдите.');
            window.location.href = 'index.html';
        })
        .catch(error => {
            alert(error.message);
        });
    });
});