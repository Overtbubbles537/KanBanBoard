document.addEventListener('DOMContentLoaded', function(){
    const form = document.getElementById('registerForm');
    form.addEventListener('submit', function(event){
        event.preventDefault();
        console.log('preventDefault вызван, форма НЕ должна отправиться');

        const nickname = (document.getElementById('nickname')).value;
        const email = (document.getElementById('email')).value;
        const password1 = (document.getElementById('password1')).value;
        const password2 = (document.getElementById('password2')).value;

        console.log(nickname,email,password1,password2);

        // const passwordRegex = /(?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,}/;
        // const IsValid = passwordRegex.test(password1);
        
        // if (!IsValid){
        //     alert('Ты петух')
        //     return 0
        // }
        if (email === '') {
            alert('Введите email!');
            return;
        }  
        if (nickname === ''){
            alert('Введите никнейм!')
        }
        if (password1 === '') {
            alert('Введите пароль!');
            return;
        }
        if (password1 !== password2){
            alert('Пароли не совпадают!');
            return 0
        } else {
            fetch('http://localhost:3001/users')
                .then(function(response){
                    return response.json();
                })
                .then(function(users){
                    const ExistUser = users.find(function(user){
                        return user.email === email;
                    })
                    if (ExistUser){
                        alert('Пользователь с таким email уже существует!')
                        return 0
                    } else {
                        fetch('http://localhost:3001/users', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                username: nickname,
                                email: email,
                                password: password1,
                            })
                        })
                        .then(function(response){
                            if (response.ok) {
                                return response.json();
                            } else {
                                throw new Error('Ошибка при регистрации');
                            }
                        })
                        .then(function() {
                            alert('Регистрация успешна!');
                            window.location.assign('index.html');
                        })
                        .catch(function(error) {
                            console.error('Ошибка:', error);
                            alert('Не удалось зарегистрироваться');
                        });
                    }
                })
                .catch(function(error){
                    console.error('Ошибка при запросе',error);
                })
        }
    })
})