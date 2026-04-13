document.addEventListener('DOMContentLoaded', function(){

    // Проверка вошедшего юзера
    const currentUser = localStorage.getItem('currentUser');
    if (!currentUser){  
        window.location.href = 'index.html';
        return;
    }
    // Выход с доски
    document.getElementById('logoutBtn').addEventListener('click', function() {
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
    });

    const user = JSON.parse(currentUser);
    console.log('Пользователь', user.email);

    loadTasks(user);
    // Работа с модальным окном
    const modal = document.getElementById('taskModal');
    const addBtn = document.getElementById('AddTaskBtn');
    const closeBtn = document.querySelector('.close');

    // Открыть модальное окно
    addBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
    });

    // Закрыть по крестику
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Закрыть по клику вне окна
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    // Добавление задачи
    const form = document.getElementById('taskForm');
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const Task = document.getElementById('taskTitle').value;
        const status = document.getElementById('taskStatus').value;
        
        if(Task === ''){
            alert('Задача не может быть пустой!');
            return;
        }

        fetch('http://localhost:3001/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: Task,
                status: status,
                userId: user.id,
            })
        })
        .then(function(response){
            if(response.ok){
                return response.json();
            } else {
                throw new Error('Ошибка при добавлении задачи!');
            }
        })
        .then(function(){
            alert('Задача успешно добавлена!')
            modal.style.display = 'none';
            loadTasks(user);
        })
        .catch(function(error){
            console.error('Ошибка', error);
        })
    });
});

// функция загрузки данных пользователя на страницу
function loadTasks(user){
    fetch('http://localhost:3001/tasks')
        .then(function(response){
            return response.json();
        })
        .then(function(tasks) {
            const userTasks = tasks.filter(task => task.userId == user.id);
            console.log('Задачи пользователя:', userTasks);
            document.getElementById('todo-list').innerHTML = '';
            document.getElementById('progress-list').innerHTML = '';
            document.getElementById('done-list').innerHTML = '';
            userTasks.forEach(function(task){
                const li = document.createElement('li');
                const DelBtn = document.createElement('button');
                const EditBtn = document.createElement('button');

                DelBtn.className = 'DelBtn';
                DelBtn.textContent = '❌';

                EditBtn.className = 'EditBtn'
                EditBtn.textContent = '✏️';

                li.className = 'task-card';
                li.textContent = task.title;

                li.appendChild(DelBtn);
                li.appendChild(EditBtn);

                if (task.status === 'todo'){
                    document.getElementById('todo-list').appendChild(li);
                } else if (task.status === 'in-progress'){
                    document.getElementById('progress-list').appendChild(li);
                } else if (task.status == 'done'){
                    document.getElementById('done-list').appendChild(li);
                }
                
                // Удаление задачи
                DelBtn.addEventListener('click', function(e){
                    e.preventDefault();
                    fetch(`http://localhost:3001/tasks/${task.id}`,{
                        method: 'DELETE',
                    })
                    .then(function(response){
                        if(response.ok){
                            alert('Задача удалена!');
                            loadTasks(user);
                        } else {
                            throw new Error('Ошибка удаления задачи!');
                        }
                    })
                    .catch(function(error){
                        console.log('Ошибка',error);
                    })
                })
            })
        })
        .catch(function(error){
            console.error('Ошибка вывода задач!',error);
        })
}