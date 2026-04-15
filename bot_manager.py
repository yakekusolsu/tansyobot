pip install flask flask-socketio eventlet
import sys
import subprocess
import threading
import time
import os
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO

# --- 設定 ---
# Renderなどの環境変数からポートを取得（デフォルト5000）
WEB_PORT = int(os.environ.get("PORT", 5000))
# Botのスクリプトファイル名
BOT_FILENAME = "my_bot.py"

# --- ダッシュボードのHTMLテンプレート ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord Bot 24h Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; }
        .log-container { background-color: #000; height: 500px; overflow-y: auto; font-family: 'Courier New', Courier, monospace; }
        .status-online { color: #22c55e; border-color: #22c55e; }
        .status-offline { color: #ef4444; border-color: #ef4444; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-5xl mx-auto">
        <header class="mb-6 flex flex-col md:flex-row justify-between items-center gap-4 border-b border-slate-700 pb-6">
            <div>
                <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    Discord Bot Manager
                </h1>
                <p class="text-slate-500 text-sm">Cloud 24h Hosting Mode</p>
            </div>
            <div id="status-badge" class="px-6 py-2 rounded-full border-2 bg-slate-900 font-bold transition-all">
                Status: <span id="status-text">確認中...</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="md:col-span-2 bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
                <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span>🎮</span> コントロールパネル
                </h2>
                <div class="flex gap-4">
                    <button id="start-btn" class="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg active:scale-95">起動</button>
                    <button id="stop-btn" class="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg active:scale-95">停止</button>
                </div>
            </div>
            
            <div class="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
                <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span>📄</span> 設定
                </h2>
                <div class="text-sm space-y-2">
                    <div class="flex justify-between"><span class="text-slate-400">Target:</span> <span class="font-mono text-blue-400">{{ bot_filename }}</span></div>
                    <div class="flex justify-between"><span class="text-slate-400">Port:</span> <span class="font-mono">{{ port }}</span></div>
                </div>
            </div>
        </div>

        <div class="bg-slate-900 rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
            <div class="bg-slate-800 px-6 py-3 border-b border-slate-700 flex justify-between items-center">
                <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest">Live Console Logs</h3>
                <button id="clear-log" class="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-slate-300">ログ消去</button>
            </div>
            <div id="log-output" class="log-container p-6 text-sm leading-relaxed text-green-400">
                <div>[SYSTEM] ダッシュボードが読み込まれました。</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        const logOutput = document.getElementById('log-output');
        const statusText = document.getElementById('status-text');
        const statusBadge = document.getElementById('status-badge');
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');

        function updateStatusUI(active) {
            if (active) {
                statusText.textContent = "稼働中 (ONLINE)";
                statusBadge.className = "px-6 py-2 rounded-full border-2 bg-slate-900 font-bold status-online shadow-[0_0_15px_rgba(34,197,94,0.3)]";
                startBtn.disabled = true;
                startBtn.classList.add('opacity-50', 'grayscale');
            } else {
                statusText.textContent = "停止中 (OFFLINE)";
                statusBadge.className = "px-6 py-2 rounded-full border-2 bg-slate-900 font-bold status-offline";
                startBtn.disabled = false;
                startBtn.classList.remove('opacity-50', 'grayscale');
            }
        }

        socket.on('log_message', (data) => {
            const div = document.createElement('div');
            div.className = "mb-1 border-l-2 border-slate-700 pl-2";
            div.innerHTML = `<span class="text-slate-500 text-xs">[${new Date().toLocaleTimeString()}]</span> ${data.msg}`;
            logOutput.appendChild(div);
            logOutput.scrollTop = logOutput.scrollHeight;
        });

        socket.on('status_update', (data) => {
            updateStatusUI(data.active);
        });

        startBtn.onclick = () => fetch('/start', {method: 'POST'});
        stopBtn.onclick = () => fetch('/stop', {method: 'POST'});
        document.getElementById('clear-log').onclick = () => logOutput.innerHTML = '';
    </script>
</body>
</html>
"""

class BotManager:
    def __init__(self):
        self.process = None
        self.should_run = False
        self.thread = None

    def start_bot(self):
        if self.process is None:
            self.should_run = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop_bot(self):
        self.should_run = False
        if self.process:
            self.process.terminate()
            self.process = None

    def _run_loop(self):
        while self.should_run:
            socketio.emit('log_message', {'msg': '<span class="text-blue-400">--- Botプロセスを開始します ---</span>'})
            self.process = subprocess.Popen(
                [sys.executable, BOT_FILENAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if not self.should_run: break
                socketio.emit('log_message', {'msg': line.strip()})
            
            self.process.wait()
            if self.should_run:
                socketio.emit('log_message', {'msg': '<span class="text-yellow-500">警告: Botが終了しました。5秒後に再起動します...</span>'})
                time.sleep(5)
        
        socketio.emit('log_message', {'msg': '<span class="text-red-400">--- Botを完全に停止しました ---</span>'})
        socketio.emit('status_update', {'active': False})

manager = BotManager()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, bot_filename=BOT_FILENAME, port=WEB_PORT)

@app.route('/start', methods=['POST'])
def start():
    manager.start_bot()
    socketio.emit('status_update', {'active': True})
    return jsonify(success=True)

@app.route('/stop', methods=['POST'])
def stop():
    manager.stop_bot()
    socketio.emit('status_update', {'active': False})
    return jsonify(success=True)

if __name__ == '__main__':
    # 実行対象のBotファイルがない場合のダミー作成
    if not os.path.exists(BOT_FILENAME):
        with open(BOT_FILENAME, "w", encoding="utf-8") as f:
            f.write("import time\nprint('Discord Bot Starting...')\nwhile True:\n    print('Bot is active and watching...')\n    time.sleep(30)")
    
    # サーバー起動
    socketio.run(app, host='0.0.0.0', port=WEB_PORT)
