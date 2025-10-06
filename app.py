from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Nds5Z42A3OshgzP9AyHE'
socketio = SocketIO(app)

chat_keys = {}
users_in_room = {} 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt_message():
    data = request.json
    room = data.get('room')
    message = data.get('message')
    if room in chat_keys:
        f = Fernet(chat_keys[room])
        encrypted_message = f.encrypt(message.encode('utf-8'))
        return jsonify({'encrypted': encrypted_message.decode('utf-8')})
    return jsonify({'error': 'Sala não encontrada'}), 404

@app.route('/decrypt', methods=['POST'])
def decrypt_message():
    data = request.json
    room = data.get('room')
    encrypted_message = data.get('encrypted_message')
    if room in chat_keys:
        f = Fernet(chat_keys[room])
        try:
            decrypted_message = f.decrypt(encrypted_message.encode('utf-8'))
            return jsonify({'decrypted': decrypted_message.decode('utf-8')})
        except Exception:
            return jsonify({'error': 'Falha ao descriptografar'}), 400
    return jsonify({'error': 'Sala não encontrada'}), 404


@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    
    users_in_room[request.sid] = {'username': username, 'room': room}
    
    join_room(room)
    
    if room not in chat_keys:
        key = Fernet.generate_key()
        chat_keys[room] = key
        print(f"Nova chave Fernet gerada para a sala '{room}'")
    
    emit('status', {'msg': f'{username} entrou na sala.'}, to=room)

@socketio.on('send_message')
def handle_send_message(data):
    encrypted_msg = data['message']
    
    user_info = users_in_room.get(request.sid)
    if user_info:
        room = user_info['room']
        username = user_info['username']
        emit('new_encrypted_message', {
            'encrypted_msg': encrypted_msg,
            'username': username 
        }, to=room)

@socketio.on('disconnect')
def on_disconnect():
    user_info = users_in_room.pop(request.sid, None)
    if user_info:
        room = user_info['room']
        username = user_info['username']
        emit('status', {'msg': f'{username} saiu da sala.'}, to=room)
        print(f"Usuário {username} desconectado.")

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)