document.addEventListener('DOMContentLoaded', function(){
    const currentUser = localStorage.getItem('currentUser');
    if (!currentUser){
        window.location.href = 'index.html';
        return;
    }

    document.getElementById('logoutBtn').addEventListener('click', function() {
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
    });

    const user = JSON.parse(currentUser);
    console.log('Пользователь', user.email);

    loadTasks(user);
});

function loadTasks(user){
    fetch('http://localhost:3001/tasks')
        .then(function(response){
            return response.json();
        })
        .then(function(tasks) {
            // console.log('Тип user.id:', typeof user.id);
            // console.log('Тип userId в задаче:', typeof tasks[0]?.userId);
            // console.log('Значение user.id:', user.id);
            // console.log('Значение userId в задаче:', tasks[0]?.userId);
            const userTasks = tasks.filter(task => task.userId == user.id);
            console.log('Задачи пользователя:', userTasks);
            document.getElementById('todo-list').innerHTML = '';
            document.getElementById('progress-list').innerHTML = '';
            document.getElementById('done-list').innerHTML = '';
            userTasks.forEach(function(task){
                const li = document.createElement('li');
                li.className = 'task-card';
                li.textContent = task.title;

                if (task.status === 'todo'){
                    document.getElementById('todo-list').appendChild(li);
                } else if (task.status === 'in-progress'){
                    document.getElementById('progress-list').appendChild(li);
                } else if (task.status == 'done'){
                    document.getElementById('done-list').appendChild(li);
                }
            })
        })
        .catch(function(error){
            console.error('Ошибка вывода задач!',error);
        })
}