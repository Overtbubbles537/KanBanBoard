document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const emailInput = document.getElementById('email');
        const email = emailInput.value;

        const passwordInput =  document.getElementById('password');
        const password = passwordInput.value;

        console.log('Email:', email);
        console.log('Пароль:', password);
        console.log('Форма отправлена, перезагрузка отменена!')
        fetch('http://localhost:3001/users')
            .then(function(response) {
                return response.json();
            })
            .then(function(users){
                const foundUser = users.find(function(user){
                    return user.email === email && user.password === password;
                })
                if (foundUser) {
                    localStorage.setItem('currentUser', JSON.stringify(foundUser));
                    alert('Успешно!');
                    window.location.href = 'main.html';          
                } else {
                    alert('Неверный email или пароль')
                }
            })
            .catch(function(error){
                console.error('Ошибка при запросе', error);
            });
    })  
});