from flask import Flask,render_template, request, redirect, url_for, session
import google.generativeai as genai
import os
from dotenv import load_dotenv
import markdown
from chatfuctions import chatfunction
from datetime import datetime

app = Flask(__name__)

load_dotenv()
api_key = os.getenv('GENINI_API_KEY')
CODE_CHAT_MODEL = os.getenv('CODE_CHAT_MODEL')
flask_secret = os.getenv('FLASK_SECRET')
app.secret_key = flask_secret

chimp_img = os.path.join("static", "chimp.jpg")
user_img = os.path.join("static", "user.jpg")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

now = datetime.now() # current date and time
date_time = now.strftime("%d/%m/%Y, %H:%M:%S")

questions = {
    "1": {"text": "Does the Customer have internet?", "yes": "2", "no": "3"},
    "2": {"text": "Other issue.", "end": True},
    "3": {"text": "Are the lights on the router?", "yes": "4", "no": "5"},
    "4": {"text": "Is the CD light on SOLID?", "yes": "7", "no": "8"},
    "5": {"text": "Reboot router. Are the lights now on?", "yes": "4", "no": "6"},
    "6": {"text": "Raise to RC - Check 4G", "end": True},
    "7": {"text": "Can you ping the 'Default Gateway'?", "yes": "9", "no": "9"},
    "8": {"text": "DSL Check router and OR Socket, Reboot Router, CD Light Solid?", "yes": "7", "no": "6"},
    "9": {"text": "Escalate if there are still issues.", "end": True}
}

@app.route("/")
def initial_laod():
    return render_template("index.html", date_time=date_time)

@app.route("/index")
def home():
    return render_template("index.html", date_time=date_time)

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/get")
def get_bot_response():  
    user_text = request.args.get('msg')
    if not user_text:
        return "error - No message provided"
    parts = user_text.split()
    if len(parts) < 2:
        return "Going to need more information to understand your request"
    funct_choice = user_text.split(" ", 1)[0]
    meaagseprompt = user_text.split(" ", 1)[1]
    response_text = chatfunction(funct_choice, meaagseprompt)
    html_response = markdown.markdown(response_text)
    return html_response

@app.route('/router')
def router():
    # Start from the first question if session state is not initialized
    if 'current_question' not in session:
        session['current_question'] = "1"
        session['history'] = []

    question_id = session['current_question']
    question_data = questions[question_id]
    
    return render_template('router.html', question_data=question_data, question_id=question_id, history=session['history'])

@app.route('/answer', methods=['POST'])
def answer():
    # Get the user's answer from the form
    user_input = request.form['answer']
    question_id = session['current_question']
    question_data = questions[question_id]

    # Save the answer in history
    session['history'].append((question_data["text"], user_input))

    # Determine the next question or end the flow
    if not question_data.get("end"):
        next_question = question_data[user_input.lower()]
        session['current_question'] = next_question
    else:
        # End of the diagnostic flow
        session['current_question'] = None

    return redirect(url_for('router'))

@app.route('/reset')
def reset():
    # Clear the session state to reset the tool
    session.pop('current_question', None)
    session.pop('history', None)
    return redirect(url_for('router'))

if __name__ == "__main__":
    app.run()
    