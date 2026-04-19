document.addEventListener('DOMContentLoaded', function(){

    // Проверка авторизации (теперь проверяем токен)
    const token = localStorage.getItem('accessToken');
    const currentUser = localStorage.getItem('currentUser');
    
    if (!token || !currentUser){  
        window.location.href = 'index.html';
        return;
    }

    const user = JSON.parse(currentUser);
    console.log('Пользователь', user.email);

    // Выход с доски
    document.getElementById('logoutBtn').addEventListener('click', function() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
    });

    loadTasks();
    
    // Работа с модальным окном
    const modal = document.getElementById('taskModal');
    const addBtn = document.getElementById('AddTaskBtn');
    const closeBtn = document.querySelector('.close');

    addBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Добавление задачи
    const form = document.getElementById('taskForm');
    form.addEventListener('submit', function(event){
        event.preventDefault();

        const taskTitle = document.getElementById('taskTitle').value;
        const status = document.getElementById('taskStatus').value;
        
        if(taskTitle === ''){
            alert('Задача не может быть пустой!');
            return;
        }

        const token = localStorage.getItem('accessToken');

        fetch('http://localhost:8000/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                title: taskTitle,
                status: status
                // userId больше не отправляем — сервер берёт из токена
            })
        })
        .then(function(response){
            if(response.ok){
                return response.json();
            } else if (response.status === 401) {
                // Токен истёк
                localStorage.removeItem('accessToken');
                localStorage.removeItem('currentUser');
                window.location.href = 'index.html';
                throw new Error('Сессия истекла');
            } else {
                throw new Error('Ошибка при добавлении задачи!');
            }
        })
        .then(function(){
            alert('Задача успешно добавлена!');
            modal.style.display = 'none';
            document.getElementById('taskTitle').value = '';
            loadTasks();
        })
        .catch(function(error){
            console.error('Ошибка', error);
            alert(error.message);
        });
    });
});

// функция загрузки задач
function loadTasks(){
    const token = localStorage.getItem('accessToken');
    
    fetch('http://localhost:8000/tasks/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(function(response){
        if (response.status === 401) {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('currentUser');
            window.location.href = 'index.html';
            throw new Error('Сессия истекла');
        }
        return response.json();
    })
    .then(function(tasks) {
        console.log('Задачи пользователя:', tasks);
        
        // Очищаем списки
        document.getElementById('todo-list').innerHTML = '';
        document.getElementById('progress-list').innerHTML = '';
        document.getElementById('done-list').innerHTML = '';
        
        tasks.forEach(function(task){
            const li = document.createElement('li');
            const taskText = document.createElement('span');
            const buttonContainer = document.createElement('div');
            const delBtn = document.createElement('button');
            const editBtn = document.createElement('button');

            taskText.textContent = task.title;
            taskText.className = 'task-text';
            
            delBtn.className = 'DelBtn';
            delBtn.textContent = '❌';
            delBtn.title = 'Удалить';

            editBtn.className = 'EditBtn';
            editBtn.textContent = '✏️';
            editBtn.title = 'Редактировать';

            buttonContainer.className = 'task-buttons';
            buttonContainer.appendChild(editBtn);
            buttonContainer.appendChild(delBtn);

            li.className = 'task-card';
            li.dataset.taskId = task.id;
            li.dataset.status = task.status;
            
            li.appendChild(taskText);
            li.appendChild(buttonContainer);

            // Распределяем по колонкам
            if (task.status === 'todo'){
                document.getElementById('todo-list').appendChild(li);
            } else if (task.status === 'in-progress'){
                document.getElementById('progress-list').appendChild(li);
            } else if (task.status === 'done'){
                document.getElementById('done-list').appendChild(li);
            }
            
            // Удаление задачи
            delBtn.addEventListener('click', function(e){
                e.preventDefault();
                e.stopPropagation();
                
                if (!confirm('Удалить задачу?')) return;
                
                const token = localStorage.getItem('accessToken');
                
                fetch(`http://localhost:8000/tasks/${task.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                })
                .then(function(response){
                    if(response.ok){
                        loadTasks();
                    } else if (response.status === 401) {
                        localStorage.removeItem('accessToken');
                        localStorage.removeItem('currentUser');
                        window.location.href = 'index.html';
                    } else {
                        throw new Error('Ошибка удаления задачи!');
                    }
                })
                .catch(function(error){
                    console.error('Ошибка', error);
                    alert('Не удалось удалить задачу');
                });
            });
            
            // Редактирование задачи (заготовка)
            editBtn.addEventListener('click', function(e){
                e.preventDefault();
                e.stopPropagation();
                
                const newTitle = prompt('Введите новое название:', task.title);
                if (!newTitle || newTitle === task.title) return;
                
                const token = localStorage.getItem('accessToken');
                
                fetch(`http://localhost:8000/tasks/${task.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        title: newTitle
                    })
                })
                .then(function(response){
                    if(response.ok){
                        loadTasks();
                    } else {
                        throw new Error('Ошибка обновления!');
                    }
                })
                .catch(function(error){
                    console.error('Ошибка', error);
                    alert('Не удалось обновить задачу');
                });
            });
        });
    })
    .catch(function(error){
        console.error('Ошибка вывода задач!', error);
    });
}