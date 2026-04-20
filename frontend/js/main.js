document.addEventListener('DOMContentLoaded', function() {
    // ====== ПРОВЕРКА АВТОРИЗАЦИИ ======
    const token = localStorage.getItem('accessToken');
    const currentUser = localStorage.getItem('currentUser');
    
    if (!token || !currentUser) {  
        window.location.href = 'index.html';
        return;
    }

    const user = JSON.parse(currentUser);
    console.log('Пользователь:', user.email);
    
    document.getElementById('userEmail').textContent = user.email;
    checkTwoFactorStatus();

    // ====== ВЫХОД ======
    document.getElementById('logoutBtn').addEventListener('click', function() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentUser');
        window.location.href = 'index.html';
    });

    loadTasks();

    // ====== НАСТРОЙКИ 2FA ======
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsPanel = document.getElementById('settingsPanel');
    const setup2faBtn = document.getElementById('setup2faBtn');
    const disable2faBtn = document.getElementById('disable2faBtn');
    const qrcodeContainer = document.getElementById('qrcodeContainer');
    const enable2faBtn = document.getElementById('enable2faBtn');
    const cancelSetupBtn = document.getElementById('cancelSetupBtn');
    const doneSetupBtn = document.getElementById('doneSetupBtn');
    const copyCodesBtn = document.getElementById('copyCodesBtn');
    
    let backupCodesList = [];

    settingsBtn.addEventListener('click', function() {
        settingsPanel.classList.toggle('hidden');
    });

    async function checkTwoFactorStatus() {
        try {
            const response = await fetch('http://localhost:8000/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const userData = await response.json();
            
            const statusSpan = document.getElementById('otpStatus');
            if (userData.otp_enabled) {
                statusSpan.innerHTML = '✅ Включена';
                statusSpan.style.color = 'green';
                setup2faBtn.classList.add('hidden');
                disable2faBtn.classList.remove('hidden');
            } else {
                statusSpan.innerHTML = '❌ Отключена';
                statusSpan.style.color = 'red';
                setup2faBtn.classList.remove('hidden');
                disable2faBtn.classList.add('hidden');
            }
        } catch (error) {
            console.error('Ошибка проверки статуса 2FA:', error);
        }
    }

    setup2faBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        try {
            const response = await fetch('http://localhost:8000/auth/2fa/setup', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const data = await response.json();
            qrcodeContainer.classList.remove('hidden');
            document.getElementById('qrcodeImage').src = `data:image/png;base64,${data.qr_code}`;
            setup2faBtn.classList.add('hidden');
            
        } catch (error) {
            alert('Ошибка настройки 2FA: ' + error.message);
        }
    });

    enable2faBtn.addEventListener('click', async function() {
        const code = document.getElementById('verifyCode').value.trim();
        if (!code || code.length !== 6) {
            alert('Введите 6-значный код');
            return;
        }
        
        try {
            const response = await fetch('http://localhost:8000/auth/2fa/enable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Неверный код');
            }
            
            const data = await response.json();
            backupCodesList = data.backup_codes;
            
            const codesDiv = document.getElementById('backupCodesList');
            codesDiv.innerHTML = '<ul>' + backupCodesList.map(c => `<li>${c}</li>`).join('') + '</ul>';
            
            document.getElementById('backupCodesContainer').classList.remove('hidden');
            enable2faBtn.classList.add('hidden');
            document.getElementById('verifyCode').value = '';
            await checkTwoFactorStatus();
            
        } catch (error) {
            alert(error.message);
        }
    });

    copyCodesBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(backupCodesList.join('\n')).then(() => {
            alert('Коды скопированы!');
        });
    });

    doneSetupBtn.addEventListener('click', function() {
        qrcodeContainer.classList.add('hidden');
        document.getElementById('backupCodesContainer').classList.add('hidden');
        settingsPanel.classList.add('hidden');
    });

    cancelSetupBtn.addEventListener('click', function() {
        qrcodeContainer.classList.add('hidden');
        setup2faBtn.classList.remove('hidden');
        document.getElementById('verifyCode').value = '';
    });

    disable2faBtn.addEventListener('click', async function() {
        const code = prompt('Введите код для отключения 2FA:');
        if (!code || code.length !== 6) {
            alert('Введите 6-значный код');
            return;
        }
        
        try {
            const response = await fetch('http://localhost:8000/auth/2fa/disable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ code })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Неверный код');
            }
            
            alert('2FA отключена');
            await checkTwoFactorStatus();
            
        } catch (error) {
            alert(error.message);
        }
    });

    // ====== МОДАЛЬНОЕ ОКНО ДОБАВЛЕНИЯ ЗАДАЧИ ======
    const addModal = document.getElementById('taskModal');
    const addBtn = document.getElementById('AddTaskBtn');
    const addForm = document.getElementById('taskForm');
    const closeAddBtn = document.querySelector('#taskModal .close');

    addBtn.addEventListener('click', function(e) {
        e.preventDefault();
        addModal.style.display = 'block';
    });


    closeAddBtn.addEventListener('click', function() {
        addModal.style.display = 'none';
    });

    addForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const taskTitle = document.getElementById('taskTitle').value.trim();
        const status = document.getElementById('taskStatus').value;
        const deadlineInput = document.getElementById('taskDeadline');
        const deadline = deadlineInput ? deadlineInput.value : null;

        console.log('Отправляемый дедлайн:', deadline);
        
        if (taskTitle === '') {
            alert('Задача не может быть пустой!');
            return;
        }

        const body = {
            title: taskTitle,
            status: status
        };

        if (deadline) {
            body.deadline = new Date(deadline).toISOString();  // ← Добавьте
        }

        console.log('ОТПРАВЛЯЕМЫЙ BODY:', JSON.stringify(body));

        fetch('http://localhost:8000/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        })
        .then(response => {
            if (response.ok) return response.json();
            else if (response.status === 401) {
                localStorage.clear();
                window.location.href = 'index.html';
                throw new Error('Сессия истекла');
            }
            throw new Error('Ошибка добавления');
        })
        .then(() => {
            addModal.style.display = 'none';
            document.getElementById('taskTitle').value = '';
            if (deadlineInput) deadlineInput.value = '';
            loadTasks();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert(error.message);
        });
    });

    // ====== МОДАЛЬНОЕ ОКНО РЕДАКТИРОВАНИЯ ЗАДАЧИ ======
    const editModal = document.getElementById('EditModal');
    const editForm = document.getElementById('editTaskForm');
    const editTitle = document.getElementById('editTaskTitle');
    const editStatus = document.getElementById('editTaskStatus');
    const closeEditBtn = document.querySelector('#EditModal .close-edit');
    const cancelEditBtn = document.querySelector('#EditModal .Cancel');

    closeEditBtn.addEventListener('click', function() {
        editModal.style.display = 'none';
    });

    cancelEditBtn.addEventListener('click', function() {
        editModal.style.display = 'none';
    });

    editForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const taskId = editForm.dataset.taskId;
        const newTitle = editTitle.value.trim();
        const newStatus = editStatus.value;

        const editDeadlineInput = document.getElementById('editTaskDeadline');
        const newDeadline = editDeadlineInput ? editDeadlineInput.value : null;
        
        if (!newTitle) {
            alert('Название не может быть пустым!');
            return;
        }

        const body = {
            title: newTitle,
            status: newStatus
        };

        if (newDeadline) {
            body.deadline = new Date(newDeadline).toISOString();
        } else {
            body.deadline = null; // Позволяет очистить дедлайн
        }
        
        console.log('PUT запрос на /tasks/' + taskId, { title: newTitle, status: newStatus });
        
        fetch(`http://localhost:8000/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        })
        .then(response => {
            if (response.ok) return response.json();
            else if (response.status === 401) {
                localStorage.clear();
                window.location.href = 'index.html';
                throw new Error('Сессия истекла');
            }
            throw new Error('Ошибка обновления');
        })
        .then(data => {
            console.log('Задача обновлена:', data);
            editModal.style.display = 'none';
            editForm.dataset.taskId = '';
            loadTasks();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert(error.message);
        });
    });

    window.addEventListener('click', function(e) {
        if (e.target === addModal) addModal.style.display = 'none';
        if (e.target === editModal) editModal.style.display = 'none';
    });

    // ====== ЗАГРУЗКА ЗАДАЧ ======
    function loadTasks() {
        fetch('http://localhost:8000/tasks/', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => {
            if (response.status === 401) {
                localStorage.clear();
                window.location.href = 'index.html';
                throw new Error('Сессия истекла');
            }
            return response.json();
        })
        .then(tasks => {
            document.getElementById('todo-list').innerHTML = '';
            document.getElementById('progress-list').innerHTML = '';
            document.getElementById('done-list').innerHTML = '';
            tasks.forEach(task => createTaskElement(task));
        })
        .catch(error => console.error('Ошибка загрузки:', error));
    }

    // ====== СОЗДАНИЕ ЭЛЕМЕНТА ЗАДАЧИ ======
    function createTaskElement(task) {
        const li = document.createElement('li');
        const taskText = document.createElement('span');
        const buttonContainer = document.createElement('div');
        const delBtn = document.createElement('button');
        const editBtn = document.createElement('button');

        taskText.textContent = task.title;
        taskText.className = 'task-text';

        if (task.deadline) {
            const deadlineSpan = document.createElement('span');
            deadlineSpan.className = 'task-deadline';
            
            const deadlineDate = new Date(task.deadline);
            const now = new Date();
            
            // Форматируем дату
            const formattedDate = deadlineDate.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            
            deadlineSpan.textContent = `📅 ${formattedDate}`;
            
            // Красный если просрочено и не выполнено
            if (deadlineDate < now && task.status !== 'done') {
                deadlineSpan.style.color = 'red';
                deadlineSpan.style.fontWeight = 'bold';
            }
            
            li.appendChild(deadlineSpan);
        }
        
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

        if (task.status === 'todo') {
            document.getElementById('todo-list').appendChild(li);
        } else if (task.status === 'in-progress') {
            document.getElementById('progress-list').appendChild(li);
        } else if (task.status === 'done') {
            document.getElementById('done-list').appendChild(li);
        }
        
        // Удаление
        delBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (!confirm('Удалить задачу "' + task.title + '"?')) return;
            
            fetch(`http://localhost:8000/tasks/${task.id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            })
            .then(response => {
                if (response.ok) li.remove();
                else if (response.status === 401) {
                    localStorage.clear();
                    window.location.href = 'index.html';
                }
            })
            .catch(error => console.error('Ошибка удаления:', error));
        });
        
        // Редактирование - ОТКРЫВАЕТ МОДАЛЬНОЕ ОКНО
        editBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Открываем редактирование задачи:', task.id, task.title);
            
            // Заполняем поля в модальном окне
            editTitle.value = task.title;
            editStatus.value = task.status;
            editForm.dataset.taskId = task.id;
            
            // Показываем модальное окно
            editModal.style.display = 'block';
        });
        
        // Drag & Drop
        li.draggable = true;
        li.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', task.id);
            li.classList.add('dragging');
        });
        li.addEventListener('dragend', function() {
            li.classList.remove('dragging');
        });
    }

    // ====== DRAG & DROP ======
    document.querySelectorAll('.task-list').forEach(column => {
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            column.classList.add('drag-over');
        });
        
        column.addEventListener('dragleave', function() {
            column.classList.remove('drag-over');
        });
        
        column.addEventListener('drop', function(e) {
            e.preventDefault();
            column.classList.remove('drag-over');
            
            const taskId = e.dataTransfer.getData('text/plain');
            let newStatus = column.id.replace('-list', '');
            if (newStatus === 'progress') newStatus = 'in-progress';
            const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
            
            if (!taskElement || taskElement.dataset.status === newStatus) return;
            
            fetch(`http://localhost:8000/tasks/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ status: newStatus })
            })
            .then(response => {
                if (response.ok) {
                    column.appendChild(taskElement);
                    taskElement.dataset.status = newStatus;
                } else if (response.status === 401) {
                    localStorage.clear();
                    window.location.href = 'index.html';
                }
            })
            .catch(error => console.error('Ошибка перемещения:', error));
        });
    });
});