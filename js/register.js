document.addEventListener('DOMContentLoaded', function(){
    const form = document.getElementById('registerForm');
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const nickname = (document.getElementById('nickname')).value;
        const email = (document.getElementById('email')).value;
        const password1 = (document.getElementById('password1')).value;
        const password2 = (document.getElementById('password2')).value;

        console.log(nickname,email,password1,password2);

        const emailRegex = /^(([^<>()[\].,;:\s@"]+(\.[^<>()[\].,;:\s@"]+)*)|(".+"))@(([^<>()[\].,;:\s@"]+\.)+[^<>()[\].,;:\s@"]{2,})$/;
        const IsValid_email = emailRegex.test(email);

        // const passwordRegex = /(?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,}/;
        // const IsValid_password = passwordRegex.test(password1);

        if (nickname === ''){
            alert('Введите никнейм!')
            return;
        }
        if (!IsValid_email){
            alert('Мэйл хуйни')
            return;
        }
        // if (!IsValid_password){
        //     alert('пароль хуйни')
        //     return;
        // }
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
                            window.location.href = 'index.html';
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