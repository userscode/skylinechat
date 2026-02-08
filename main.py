import os
import uuid
from flask import Flask, render_template_string, request, jsonify, session

# --- КОНФИГУРАЦИЯ ---
app = Flask(__name__)
# В облаке лучше использовать переменную окружения для ключа, если она есть
app.secret_key = os.environ.get("SECRET_KEY", str(uuid.uuid4()))

# Структура данных (ВНИМАНИЕ: Очищается при перезагрузке сервера на Render)
users = {}  # { username: { password, avatar } }
chats = {
    "global": [
        {"username": "Skyline Bot", "text": "Добро пожаловать в общий чат на Render!", "avatar": "🚀"}
    ]
}

# --- HTML ШАБЛОН ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Skyline Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; transition: background-color 0.3s; height: 100vh; margin: 0; overflow: hidden; }
        
        .theme-light { background-color: #f8fafc; color: #1e293b; }
        .theme-dark { background-color: #0f172a; color: #f1f5f9; }
        .theme-dark .bg-white { background-color: #1e293b; border-color: #334155; color: white; }
        .theme-dark .sidebar { background-color: #1e293b; border-right-color: #334155; }
        .theme-dark .other-message { background-color: #334155; color: white; border: none; }
        .theme-dark .sidebar-item:hover { background-color: #334155; }
        .theme-dark input { background-color: #1e293b; border-color: #475569; color: white; }

        .chat-area { flex-grow: 1; overflow-y: auto; scrollbar-width: thin; }
        .sidebar { width: 260px; flex-shrink: 0; transition: transform 0.3s ease; }
        
        @media (max-width: 768px) {
            .sidebar { position: absolute; z-index: 50; height: 100%; transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
        }

        .message-bubble { border-radius: 18px; padding: 10px 16px; max-width: 85%; word-wrap: break-word; }
        .my-message { background-color: #3b82f6; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
        .other-message { background-color: white; color: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #e2e8f0; }
        
        .big-emoji { font-size: 3.5rem; background: transparent !important; box-shadow: none !important; padding: 0 !important; }
        .avatar-img { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
        .avatar-emoji { font-size: 1.2rem; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        
        .sidebar-item { cursor: pointer; transition: background 0.2s; border-radius: 8px; margin-bottom: 4px; }
    </style>
</head>
<body class="theme-light">

    <div id="auth-screen" class="w-full h-full flex items-center justify-center p-4">
        <div class="w-full max-w-md p-8 bg-white rounded-3xl shadow-2xl border border-slate-100">
            <div class="text-center mb-6">
                <h1 class="text-3xl font-extrabold tracking-tight text-blue-600">Skyline Chat</h1>
                <p id="auth-title" class="text-slate-500 mt-2 text-sm">Версия для Render</p>
            </div>
            <div class="space-y-4">
                <div id="avatar-selection" class="hidden space-y-2">
                    <input type="text" id="avatar-input" placeholder="Emoji или URL аватарки" 
                           class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <input type="text" id="auth-user" placeholder="Имя пользователя" class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500">
                <input type="password" id="auth-pass" placeholder="Пароль" class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500">
                <div id="auth-error" class="text-red-500 text-xs hidden text-center font-medium"></div>
                <button onclick="handleAuth()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg">Войти</button>
                <button onclick="toggleAuthMode()" id="toggle-btn" class="w-full text-blue-600 text-xs font-semibold hover:underline">Создать аккаунт</button>
            </div>
        </div>
    </div>

    <div id="chat-screen" class="hidden flex h-full w-full">
        <aside id="sidebar" class="sidebar bg-white border-r border-slate-200 flex flex-col p-4">
            <div class="flex items-center justify-between mb-6">
                <h3 class="font-bold text-lg text-blue-600 tracking-tight">Skyline</h3>
                <button onclick="toggleSidebar()" class="md:hidden text-slate-400">✕</button>
            </div>
            
            <div class="flex-grow overflow-y-auto">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Чаты</p>
                <div id="chats-list" class="mb-6">
                    <div onclick="switchChat('global')" class="sidebar-item p-3 flex items-center gap-3 bg-blue-50 text-blue-700 font-medium">
                        <span>🌍</span> <span>Общий</span>
                    </div>
                </div>

                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">В сети</p>
                <div id="users-list"></div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center gap-2">
                <button onclick="toggleTheme()" class="flex-1 p-2 bg-slate-100 rounded-lg text-xs">🌓</button>
                <button onclick="createNewChat()" class="flex-1 p-2 bg-blue-600 text-white rounded-lg text-xs font-bold">Чат +</button>
            </div>
        </aside>

        <main class="flex-grow flex flex-col relative h-full">
            <header class="bg-white border-b border-slate-200 p-4 flex justify-between items-center shadow-sm">
                <div class="flex items-center gap-3">
                    <button onclick="toggleSidebar()" class="md:hidden p-2 bg-slate-100 rounded-lg">☰</button>
                    <div id="header-avatar" class="w-9 h-9 overflow-hidden rounded-full bg-blue-50 flex items-center justify-center"></div>
                    <div>
                        <h2 class="font-bold text-slate-900 leading-none text-sm" id="display-name">User</h2>
                        <span class="text-[10px] text-blue-500 font-medium" id="chat-label">Общий чат</span>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="copyInvite()" class="hidden sm:block p-2 text-slate-400 hover:text-blue-600">🔗</button>
                    <button onclick="location.reload()" class="p-2 text-red-400 text-xs font-bold">ВЫХОД</button>
                </div>
            </header>

            <div id="chat-box" class="chat-area p-4 space-y-4 flex flex-col"></div>

            <footer class="bg-white border-t border-slate-200 p-3">
                <div class="max-w-4xl mx-auto flex items-center gap-2">
                    <input type="text" id="msg-input" placeholder="Сообщение..." 
                           class="flex-1 p-3 bg-slate-100 border-none rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                    <button onclick="sendMsg()" class="bg-blue-600 text-white p-3 rounded-2xl shadow-md active:scale-95 transition-transform">
                        ➤
                    </button>
                </div>
            </footer>
        </main>
    </div>

    <script>
        let isRegister = false;
        let currentUser = "";
        let currentAvatar = "👤";
        let currentChatId = "global";
        let isDarkMode = false;
        let sidebarOpen = false;

        function toggleSidebar() {
            sidebarOpen = !sidebarOpen;
            document.getElementById('sidebar').classList.toggle('open', sidebarOpen);
        }

        function toggleTheme() {
            isDarkMode = !isDarkMode;
            document.body.className = isDarkMode ? 'theme-dark' : 'theme-light';
        }

        function switchChat(id) {
            currentChatId = id;
            document.getElementById('chat-label').innerText = id === 'global' ? "Общий чат" : "Чат: " + id;
            if (window.innerWidth < 768) toggleSidebar();
            updateChat(true);
        }

        function createNewChat() {
            const newId = Math.random().toString(36).substring(2, 9);
            const url = window.location.origin + window.location.pathname + "?chat=" + newId;
            prompt("Ссылка на новый чат (скопируйте):", url);
            window.location.href = url;
        }

        function copyInvite() {
            const el = document.createElement('textarea');
            el.value = window.location.href;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert("Ссылка скопирована!");
        }

        function toggleAuthMode() {
            isRegister = !isRegister;
            document.getElementById('auth-title').innerText = isRegister ? "Регистрация" : "Вход";
            document.getElementById('toggle-btn').innerText = isRegister ? "Войти" : "Создать аккаунт";
            document.getElementById('avatar-selection').classList.toggle('hidden', !isRegister);
        }

        async function handleAuth() {
            const username = document.getElementById('auth-user').value.trim();
            const password = document.getElementById('auth-pass').value.trim();
            const avatar = document.getElementById('avatar-input').value.trim() || "👤";
            
            if(!username || !password) return;

            const endpoint = isRegister ? '/register' : '/login';
            const resp = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, password, avatar })
            });

            const data = await resp.json();
            if (data.status === 'ok') {
                currentUser = username;
                currentAvatar = data.avatar;
                showChat();
            } else {
                const err = document.getElementById('auth-error');
                err.innerText = data.message;
                err.classList.remove('hidden');
            }
        }

        function renderAvatar(avatarStr, sizeClass = "") {
            if (avatarStr && avatarStr.startsWith('http')) {
                return `<img src="${avatarStr}" class="avatar-img ${sizeClass}" onerror="this.outerHTML='👤'">`;
            }
            return `<div class="avatar-emoji ${sizeClass}">${avatarStr || '👤'}</div>`;
        }

        async function showChat() {
            document.getElementById('auth-screen').classList.add('hidden');
            document.getElementById('chat-screen').classList.remove('hidden');
            document.getElementById('display-name').innerText = currentUser;
            document.getElementById('header-avatar').innerHTML = renderAvatar(currentAvatar);
            
            const params = new URLSearchParams(window.location.search);
            const chatFromUrl = params.get('chat');
            if (chatFromUrl) currentChatId = chatFromUrl;

            updateChat();
            updateUsers();
            setInterval(updateChat, 2000);
            setInterval(updateUsers, 5000);
        }

        async function updateUsers() {
            try {
                const resp = await fetch('/users');
                const data = await resp.json();
                const list = document.getElementById('users-list');
                list.innerHTML = '';
                data.forEach(u => {
                    const div = document.createElement('div');
                    div.className = "sidebar-item p-2 flex items-center gap-3 hover:bg-slate-50";
                    div.innerHTML = `${renderAvatar(u.avatar)} <span class="text-sm font-medium">${u.username}</span>`;
                    list.appendChild(div);
                });
            } catch(e) {}
        }

        async function sendMsg() {
            const input = document.getElementById('msg-input');
            const text = input.value.trim();
            if (!text) return;

            await fetch('/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text, chat_id: currentChatId })
            });
            input.value = '';
            updateChat();
        }

        let lastMsgCount = 0;
        async function updateChat(force = false) {
            try {
                const resp = await fetch(`/messages?chat_id=${currentChatId}`);
                const data = await resp.json();
                if (data.length !== lastMsgCount || force) {
                    const box = document.getElementById('chat-box');
                    box.innerHTML = '';
                    data.forEach(m => {
                        const isMe = m.username === currentUser;
                        const row = document.createElement('div');
                        row.className = `flex gap-2 w-full ${isMe ? 'flex-row-reverse' : 'flex-row'} items-end`;
                        const isBigEmoji = /^(\\u00a9|\\u00ae|[\\u2000-\\u3300]|\\ud83c[\\ud000-\\udfff]|\\ud83d[\\ud000-\\udfff]|\\ud83e[\\ud000-\\udfff])$/u.test(m.text.trim());
                        
                        row.innerHTML = `
                            ${renderAvatar(m.avatar)}
                            <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'} max-w-[80%]">
                                <span class="text-[8px] font-bold text-slate-400 px-1 uppercase mb-0.5">${m.username}</span>
                                <div class="message-bubble ${isMe ? 'my-message' : 'other-message'} ${isBigEmoji ? 'big-emoji' : ''}">
                                    <p class="${isBigEmoji ? '' : 'text-sm'}">${m.text}</p>
                                </div>
                            </div>
                        `;
                        box.appendChild(row);
                    });
                    box.scrollTop = box.scrollHeight;
                    lastMsgCount = data.length;
                }
            } catch(e) {}
        }

        document.getElementById('msg-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMsg();
        });
    </script>
</body>
</html>
"""

# --- BACKEND ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    u, p, av = data.get('username'), data.get('password'), data.get('avatar', '👤')
    if u in users: return jsonify({"status": "error", "message": "Имя занято"})
    users[u] = {"password": p, "avatar": av}
    session['user'] = u
    session['avatar'] = av
    return jsonify({"status": "ok", "avatar": av})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u, p = data.get('username'), data.get('password')
    user_data = users.get(u)
    if user_data and user_data['password'] == p:
        session['user'] = u
        session['avatar'] = user_data['avatar']
        return jsonify({"status": "ok", "avatar": user_data['avatar']})
    return jsonify({"status": "error", "message": "Неверные данные"})

@app.route('/users')
def get_users():
    user_list = [{"username": u, "avatar": info['avatar']} for u, info in users.items()]
    return jsonify(user_list)

@app.route('/messages')
def get_messages():
    chat_id = request.args.get('chat_id', 'global')
    return jsonify(chats.get(chat_id, []))

@app.route('/send', methods=['POST'])
def send():
    user = session.get('user')
    avatar = session.get('avatar', '👤')
    if not user: return jsonify({"status": "error"}), 403
    data = request.json
    text = data.get('text')
    chat_id = data.get('chat_id', 'global')
    if chat_id not in chats: chats[chat_id] = []
    if text:
        chats[chat_id].append({"username": user, "text": text, "avatar": avatar})
        if len(chats[chat_id]) > 100: chats[chat_id].pop(0)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Render передает PORT через переменную окружения
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
