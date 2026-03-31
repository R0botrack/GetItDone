from flask import Flask, request, jsonify, send_from_directory
import json
import os
import uuid
from supabase import create_client, Client

url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_ANON_KEY"
supabase: Client = create_client(url, key)



app = Flask(__name__, static_folder='static')
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return send_from_directory('static', 'login.html')

@app.route('/register')
def register_page():
    return send_from_directory('static', 'register.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory('static', 'dashboard.html')

@app.route('/list_view')
def list_page():
    return send_from_directory('static', 'list.html')

@app.route('/view_list')
def view_list_page():
    return send_from_directory('static', 'view_list.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/register', methods=['POST'])
def api_register():
    req = request.json
    username = req.get('username')
    password = req.get('password')

    # Check if user exists
    user_check = supabase.table("users").select("*").eq("username", username).execute()
    if user_check.data:
        return jsonify({"error": "Uporabnik s tem imenom že obstaja!"}), 400

    # Insert new user
    supabase.table("users").insert({
        "username": username, 
        "password": password, 
        "lists": {}
    }).execute()
    
    return jsonify({"message": "Registracija uspešna!"})

@app.route('/api/login', methods=['POST'])
def api_login():
    req = request.json
    username = req.get('username')
    password = req.get('password')

    user = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    
    if user.data:
        return jsonify({"message": "Prijava uspešna!"})
        
    return jsonify({"error": "Napačno uporabniško ime ali geslo!"}), 401

@app.route('/api/lists', methods=['GET', 'POST'])
def api_lists():
    data = load_data()
    username = request.headers.get('Username')
    
    if not username or username not in data:
        return jsonify({"error": "Neavtoriziran dostop!"}), 401

    if "lists" not in data[username]:
        data[username]["lists"] = {}

    if request.method == 'GET':
        return jsonify(data[username]["lists"])

    if request.method == 'POST':
        list_name = request.json.get('name')
        list_id = str(uuid.uuid4())
        data[username]["lists"][list_id] = {"name": list_name, "items": []}
        save_data(data)
        return jsonify({"message": "Seznam ustvarjen!", "list_id": list_id})

@app.route('/api/lists/<list_id>', methods=['GET', 'POST', 'DELETE'])
def api_list_items(list_id):
    data = load_data()
    username = request.headers.get('Username')
    
    if not username or username not in data:
        return jsonify({"error": "Neavtoriziran dostop!"}), 401

    user_lists = data[username].get("lists", {})
    if list_id not in user_lists:
        return jsonify({"error": "Seznam ne obstaja!"}), 404

    if request.method == 'GET':
        return jsonify(user_lists[list_id])
        
    if request.method == 'POST':
        items = request.json.get('items', [])
        user_lists[list_id]["items"] = items
        save_data(data)
        return jsonify({"message": "Elementi shranjeni!"})
        
    if request.method == 'DELETE':
        del user_lists[list_id]
        save_data(data)
        return jsonify({"message": "Seznam izbrisan!"})

if __name__ == '__main__':
    app.run(debug=True)