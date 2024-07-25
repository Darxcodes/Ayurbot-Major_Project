from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import train
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'

openai.api_key = "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"

# Database setup for user authentication
def setup_auth_database():
    conn_auth = sqlite3.connect('users_auth.db', check_same_thread=False)
    c_auth = conn_auth.cursor()
    c_auth.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn_auth.commit()
    conn_auth.close()

# Database setup for storing user conversations
def setup_conv_database():
    conn_conv = sqlite3.connect('conversations.db', check_same_thread=False)
    c_conv = conn_conv.cursor()
    c_conv.execute('''CREATE TABLE IF NOT EXISTS conversations
                (id INTEGER PRIMARY KEY, username TEXT, message TEXT)''')
    conn_conv.commit()
    conn_conv.close()

# Check if user is logged in
def is_logged_in():
    return session.get('logged_in', False)

# Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect('users_auth.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# Register user
def register_user(username, password):
    conn = sqlite3.connect('users_auth.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user:
        conn.close()
        return False
    else:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True

# Store conversation in database
def store_conversation(username, message):
    conn_conv = sqlite3.connect('conversations.db', check_same_thread=False)
    c_conv = conn_conv.cursor()
    c_conv.execute("INSERT INTO conversations (username, message) VALUES (?, ?)", (username, message))
    conn_conv.commit()
    conn_conv.close()

# Medical Chatbot class
class MedicalChatbot:
    def __init__(self):
        self.input_data = {}
        self.step = 0
        self.conversation_history = []
        self.conversation_id = 1  # Initialize with an arbitrary conversation ID

    # Reply to user message
    def reply(self, message, username):
        try:
            # Store conversation in database
            store_conversation(username, message)
            self.conversation_history.append({"role": "user", "content": message})
            
            if self.step == 0:
                if "hello" in message.lower() or "hi" in message.lower() or "hai" in message.lower():
                    self.step = 1
                    return "How may I help you?"
                else:
                    return "I'm sorry, I didn't understand that. Please start by saying 'hello'."
            elif self.step == 1:
                if "sick" in message.lower() or "ill" in message.lower():
                    self.step = 2
                    return "Okay, let's see what's going on. What's your age?"
                else:
                    return "I'm sorry, I didn't understand that. Please tell me if you're feeling sick or ill."
            elif self.step == 2:
                try:
                    self.input_data["age"] = int(message)
                    self.step = 3
                    return "Thank you for providing your age. What's your gender?"
                except ValueError:
                    return "Invalid age. Please enter a valid integer."
            elif self.step == 3:
                if message.lower() in ["male", "female"]:
                    self.input_data["gender"] = message.lower()
                    self.step = 4
                    return f"Got it. Now, please tell me your symptoms."
                else:
                    return "Invalid gender. Please enter 'male' or 'female'."
            elif self.step == 4:
                symptoms = [symptom.strip().replace(" ", "_") for symptom in message.split(",")]
                self.input_data["symptoms"] = ', '.join(symptoms)
                for symptom in symptoms:
                    self.input_data[symptom] = 1
                self.step = 5
                return f"Your symptoms are: {', '.join(symptoms)}. What is the severity level (LOW/NORMAL/HIGH)?"
            elif self.step == 5:
                if message.upper() in ["LOW", "NORMAL", "HIGH"]:
                    self.input_data["severity"] = message.upper()
                    if len(self.input_data["symptoms"].split(', ')) < 4:
                        prompt = f"I am a {self.input_data['gender']} of age {self.input_data['age']} suffering from {self.input_data['severity']} severity of {self.input_data['symptoms']}. Identify the disease and ayurvedic treatment,I want the response in the following format:'You are diagnosed with the disease_name and i recommend this treatment_name in maximum of 3 sentences"
                        return self.chat_with_openai(prompt)
                    else:
                        prompt = f"I am a {self.input_data['gender']} of age {self.input_data['age']} suffering from {self.input_data['severity']} severity of {self.input_data['symptoms']}. Identify the disease and ayurvedic treatment,I want the response in the following format:'You are diagnosed with the disease_name and i recommend this treatment_name in maximum of 3 sentences"
                        try:
                            prognosis, drug_recommendation = train.predict_prognosis_and_recommend_drug(self.input_data)
                            self.step = 0
                            return f"Okay, let's see. According to the details you've provided, you might have {prognosis}. The recommended treatment is {drug_recommendation}."
                        except ValueError as e:
                            return self.chat_with_openai(prompt)
                else:
                    return "Invalid severity level. Please enter 'LOW', 'NORMAL', or 'HIGH'."
        except Exception as e:
            return str(e)
        
    def chat_with_openai(self, prompt):
        try:
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}] + self.conversation_history,
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return str(e)

# Instantiate Medical Chatbot
chatbot = MedicalChatbot()

# Index route
@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for('register'))
    return render_template("index.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        # Check login credentials
        if authenticate_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Invalid login. Please try again.'
    return render_template('login.html')

# Logout route
@app.route("/logout")
def logout():
    session['logged_in'] = False
    session.pop('username', None)
    return redirect(url_for('login'))

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data["message"]
        username = session['username']
        response = chatbot.reply(message, username)
        return jsonify({"message": response})
    except Exception as e:
        return str(e)

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password):
            return 'User registered successfully!'
        else:
            return 'Username already exists. Please choose a different username.'
    return render_template('register.html')

if __name__ == "__main__":
    setup_auth_database()
    setup_conv_database()
    app.run(debug=True)
