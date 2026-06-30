import datetime, pickle, json, os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = 'messmind_secret_key_2024'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def local_path(filename):
    return os.path.join(BASE_DIR, filename)

stats = {
    "Breakfast": {"eating": 0, "skipping": 0},
    "Lunch": {"eating": 0, "skipping": 0},
    "Dinner": {"eating": 0, "skipping": 0}
}

prediction_history = []
USERS_FILE = local_path('users.json')

# Load or create users database
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

users_db = load_users()
print(f"Loaded users: {list(users_db.keys())}")

MENU = {
    0: {"Breakfast": "Gobhi Prantha + Curd", "Lunch": "Rajma Rice + Rotti", "Dinner": "Aloo Gobhi + Moong Dal", "Sweet": "Jimjam Biscuit"},
    1: {"Breakfast": "Aloo Prantha + Curd", "Lunch": "Black channe Rice + Rotti", "Dinner": "Sarso ka Saag + Chana Dal", "Sweet": "Munch"},
    2: {"Breakfast": "Macaroni/Sandwich", "Lunch": "Fried Rice + Mah Dal", "Dinner": "Paneer Bhurji + Moong Dal", "Sweet": "Chamcham"},
    3: {"Breakfast": "Methi Prantha + Curd", "Lunch": "Aloo Matar + Dahi + Rice", "Dinner": "Chana Masala + Curd", "Sweet": "Dairy milk"},
    4: {"Breakfast": "Bread Pakoda/Poha", "Lunch": "Channa Dal + Bhujiya + Rice", "Dinner": "Cheese Chilli + Moong Dal", "Sweet": "Jalebi"},
    5: {"Breakfast": "Aloo Prantha + Curd", "Lunch": "Dal Makhni + Rice", "Dinner": "Aloo Matar Gajar + Masar Dal", "Sweet": "Halwa"},
    6: {"Breakfast": "Paneer Pyaaz Prantha", "Lunch": "Pudi + White channe", "Dinner": "Aloo Sabji + Rice", "Sweet": "Dark Fantasy"}
}

# Model loading logic remains same
try:
    with open(local_path('mess_model.pkl'), 'rb') as f:
        m_data = pickle.load(f)
        model, le_meal = m_data['model'], m_data['le_meal']
except Exception as e:
    print(f"Error loading model: {e}")
    model, le_meal = None, None

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('user_role') == 'student':
            return redirect(url_for('student_portal'))
        else:
            return redirect(url_for('manager_dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_id' in session:
        if session.get('user_role') == 'student':
            return redirect(url_for('student_portal'))
        else:
            return redirect(url_for('manager_dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    global users_db
    data = request.json
    full_name = data.get('full_name', '').strip()
    user_id = data.get('user_id', '').strip()
    password = data.get('password', '').strip()
    user_role = data.get('user_role', 'student').strip()
    
    print(f"Registration attempt - User ID: {user_id}, Role: {user_role}")
    
    # Validation
    if not full_name:
        return jsonify({'success': False, 'message': 'Full name cannot be empty'}), 400
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID cannot be empty'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': 'Password cannot be empty'}), 400
    
    if len(password) < 4:
        return jsonify({'success': False, 'message': 'Password must be at least 4 characters'}), 400
    
    # Reload to get latest users
    users_db = load_users()
    
    if user_id in users_db:
        return jsonify({'success': False, 'message': 'User ID already exists. Please choose a different one'}), 400
    
    # Store user
    users_db[user_id] = {
        'full_name': full_name,
        'password': generate_password_hash(password),
        'role': user_role
    }
    
    if save_users(users_db):
        print(f"Registration successful - User ID: {user_id}")
        return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
    else:
        return jsonify({'success': False, 'message': 'Error saving user. Please try again.'}), 500

@app.route('/auth_login', methods=['POST'])
def auth_login():
    global users_db
    data = request.json
    user_id = data.get('user_id', '').strip()
    password = data.get('password', '').strip()
    
    print(f"Login attempt - User ID: {user_id}")
    
    # Strict validation
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID cannot be empty'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': 'Password cannot be empty'}), 400
    
    # Reload users to get latest data
    users_db = load_users()
    print(f"Available users in DB: {list(users_db.keys())}")
    
    if user_id not in users_db:
        print(f"User not found: {user_id}")
        return jsonify({'success': False, 'message': 'Invalid User ID or Password'}), 401
    
    user = users_db[user_id]
    
    if not check_password_hash(user['password'], password):
        print(f"Password mismatch for user: {user_id}")
        return jsonify({'success': False, 'message': 'Invalid User ID or Password'}), 401
    
    # Set session
    session['user_id'] = user_id
    session['user_role'] = user['role']
    session['full_name'] = user['full_name']
    session.permanent = True
    
    print(f"Login successful - User ID: {user_id}, Role: {user['role']}")
    
    return jsonify({
        'success': True,
        'redirect': url_for('student_portal') if user['role'] == 'student' else url_for('manager_dashboard')
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/student')
def student_portal():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    day_idx = datetime.datetime.now().weekday()
    return render_template('student.html', menu=MENU.get(day_idx, MENU[0]), full_name=session.get('full_name'))

@app.route('/manager')
def manager_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'manager':
        return redirect(url_for('login'))
    total_live = sum(m["eating"] for m in stats.values())
    return render_template('index.html', live=total_live, full_menu=MENU, full_name=session.get('full_name'))
@app.route('/manager_polls')
def manager_polls():
    if 'user_id' not in session or session.get('user_role') != 'manager':
        return redirect(url_for('login'))

    return render_template('manager_polls.html', full_name=session.get('full_name'))

@app.route('/manager_donate')
def manager_donate():
    if 'user_id' not in session or session.get('user_role') != 'manager':
        return redirect(url_for('login'))

    return render_template('manager_donate.html', full_name=session.get('full_name'))

@app.route('/manager_notifications')
def manager_notifications():
    if 'user_id' not in session or session.get('user_role') != 'manager':
        return redirect(url_for('login'))

    return render_template('manager_notifications.html', full_name=session.get('full_name'))

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or le_meal is None:
        return jsonify({'message': 'Prediction model is unavailable. Please restart the server and verify mess_model.pkl exists.'}), 500

    req = request.json or {}
    try:
        meal = req.get('meal')
        day = int(req.get('day', 0))
        pop = int(req.get('pop', 0))

        if meal not in stats:
            raise ValueError('Invalid meal selection')

        m_enc = le_meal.transform([meal])[0]
        feat = [[day, m_enc, 0, 0, pop]]
        res = int(model.predict(feat)[0] * 1.05)
        res = max(0, res)
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'message': f'Unable to compute prediction: {e}'}), 400
    
    entry = {
        "time": datetime.datetime.now().strftime("%I:%M %p"),
        "meal": meal,
        "predicted": res,
        "verified": stats[meal]["eating"]
    }
    prediction_history.append(entry)
    return jsonify({'plates': res, 'verified': stats[meal]["eating"], 'history': prediction_history})

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    data = request.json
    meal, status = data.get('meal'), data.get('status')
    if meal in stats:
        stats[meal][status] += 1
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route('/menu')
def menu_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html', full_menu=MENU, full_name=session.get('full_name'), user_role=session.get('user_role'))

# Complaints and Feedback
COMPLAINTS_FILE = local_path('complaints.json')

def load_complaints():
    try:
        if os.path.exists(COMPLAINTS_FILE):
            with open(COMPLAINTS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except:
        return []

def save_complaints(complaints):
    try:
        with open(COMPLAINTS_FILE, 'w') as f:
            json.dump(complaints, f, indent=2)
        return True
    except:
        return False

# Messages System
MESSAGES_FILE = local_path('messages.json')

def load_messages():
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except:
        return []

def save_messages(messages):
    try:
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
        return True
    except:
        return False

@app.route('/complaints')
def complaints_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('complaints.html', full_name=session.get('full_name'), user_role=session.get('user_role'))

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.json
    complaint_type = data.get('type', '').strip()
    description = data.get('description', '').strip()
    
    if not complaint_type or not description:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    complaints = load_complaints()
    complaint = {
        'user_id': session['user_id'],
        'user_name': session['full_name'],
        'type': complaint_type,
        'description': description,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    complaints.append(complaint)
    
    if save_complaints(complaints):
        return jsonify({'success': True, 'message': 'Complaint submitted successfully'})
    return jsonify({'success': False, 'message': 'Error saving complaint'}), 500

@app.route('/get_complaints')
def get_complaints():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    complaints = load_complaints()
    return jsonify({'success': True, 'complaints': complaints})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session or session.get('user_role') != 'manager':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400
    
    messages = load_messages()
    message = {
        'id': len(messages) + 1,
        'sender': session['full_name'],
        'message': message_text,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    messages.append(message)
    
    if save_messages(messages):
        return jsonify({'success': True, 'message': 'Message sent successfully'})
    return jsonify({'success': False, 'message': 'Error sending message'}), 500

@app.route('/get_messages')
def get_messages():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    messages = load_messages()
    # Return latest 10 messages
    recent_messages = sorted(messages, key=lambda x: x['timestamp'], reverse=True)[:10]
    return jsonify({'success': True, 'messages': recent_messages})

# Polls for Dish Voting
POLLS_FILE = 'polls.json'

def load_polls():
    try:
        if os.path.exists(POLLS_FILE):
            with open(POLLS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return {}
    except:
        return {}

def save_polls(polls):
    try:
        with open(POLLS_FILE, 'w') as f:
            json.dump(polls, f, indent=2)
        return True
    except:
        return False

@app.route('/polls')
def polls_page():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    return render_template('polls.html', full_name=session.get('full_name'))

@app.route('/get_polls')
def get_polls():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    polls = load_polls()
    user_votes = load_user_votes()
    
    return jsonify({
        'success': True,
        'polls': polls,
        'user_votes': user_votes.get(session['user_id'], {})
    })

VOTES_FILE = 'votes.json'

def load_user_votes():
    try:
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return {}
    except:
        return {}

def save_user_votes(votes):
    try:
        with open(VOTES_FILE, 'w') as f:
            json.dump(votes, f, indent=2)
        return True
    except:
        return False

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json(silent=True) or {}
    dish_name = data.get('dish_name', '').strip()
    
    if not dish_name:
        return jsonify({'success': False, 'message': 'Dish name required'}), 400
    
    polls = load_polls()
    user_votes = load_user_votes()
    user_id = session['user_id']

    # 🔴 NEW: Track if dish is newly suggested
    is_new = False
    if dish_name not in polls:
        polls[dish_name] = {'votes': 0, 'voters': []}
        is_new = True
    
    # Initialize user votes if not exists
    if user_id not in user_votes:
        user_votes[user_id] = {}
    
    # Check if user already voted
    if dish_name in user_votes[user_id]:
        return jsonify({'success': False, 'message': 'You already voted for this dish'}), 400
    
    # Add vote
    polls[dish_name]['votes'] += 1
    polls[dish_name]['voters'].append(user_id)
    user_votes[user_id][dish_name] = True
    
    save_polls(polls)
    save_user_votes(user_votes)

    # 🔴 NEW: SAVE ACTIVITY (THIS IS THE MAIN FEATURE)
    activity = load_poll_activity()

    activity.append({
        'dish': dish_name,
        'action': 'suggested' if is_new else 'voted',
        'student': session.get('full_name'),
        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_poll_activity(activity)

    return jsonify({'success': True, 'message': 'Vote submitted successfully'})
@app.route('/get_poll_results')
def get_poll_results():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    polls = load_polls()
    # Sort by votes
    sorted_polls = sorted(polls.items(), key=lambda x: x[1]['votes'], reverse=True)
    
    return jsonify({
        'success': True,
        'results': [{'dish': dish, 'votes': data['votes']} for dish, data in sorted_polls]
    })

POLL_ACTIVITY_FILE = 'poll_activity.json'

def load_poll_activity():
    try:
        if os.path.exists(POLL_ACTIVITY_FILE):
            with open(POLL_ACTIVITY_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except:
        return []

def save_poll_activity(data):
    try:
        with open(POLL_ACTIVITY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False
    
@app.route('/get_poll_activity')
def get_poll_activity():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    activity = load_poll_activity()

    # latest first
    activity = sorted(activity, key=lambda x: x['time'], reverse=True)

    return jsonify({
        'success': True,
        'data': activity[:20]
    })

if __name__ == '__main__':
    app.run(debug=True)