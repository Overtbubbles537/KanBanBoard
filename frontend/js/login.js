document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        fetch('http://localhost:8000/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Неверный email или пароль');
            }
        })
        .then(data => {
            // Сохраняем токен и пользователя
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            window.location.href = 'main.html';
        })
        .catch(error => {
            alert(error.message);
        });
    });
});