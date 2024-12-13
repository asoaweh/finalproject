from flask import Flask, render_template, request, jsonify, session, redirect, url_for #all needed to successfully implement backend quiz logic
import csv
import random 

app = Flask(__name__)
app.secret_key = 'your_secret_key'
class Card: 
    "classes card and deck created to store terms and definitions for the flashcards"
    def __init__(self, term, definition): 
        self.term = term
        self.definition = definition 

    def __repr__(self):
        return f'[Term: {self.term}, Definition: {self.definition}]'
    
class Deck: 
    def __init__(self, name, created): 
        self.name = name 
        self.created = created
        self.cards = [] 

    def add_card(self, card):
        self.cards.append(card) # to add cards to a deck

    def to_csv(self, filename):
        "created to save the decks created"  
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Term', 'Definition'])
            for card in self.cards:
                writer.writerow([card.term, card.definition]) # saving the cards as terms and definitions

def load_cards_from_csv(filename):
    "to read the contents of the decks"
    cards = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            cards.append(Card(row['Term'], row['Definition']))
    return cards

@app.route('/') # Mapping the URLs to its html component
def home():
    "mapping the home url to main.html"
    return render_template('main.html')  
@app.route('/cont')
def about():
    "mapping the /cont url to cont.html"
    return render_template('cont.html')  

@app.route('/about')
def third():
    "mapping the /about url to aboutus.html"
    return render_template('aboutus.html')  

@app.route('/add_card', methods=['POST']) # creating a deck and adding its card objects to it
def get_data():
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        created = data['created']
        cards = data['cards']

        deck = Deck(name, created)
        for card in cards:
            deck.add_card(Card(card['term'], card['definition']))

        csv_filename = f"{deck.name}_{deck.created}.csv".replace(" ", "_").replace(":", "_").replace("/", "_")

        deck.to_csv(csv_filename) # the deck is saved as a csv file

        print(f"Deck saved to {csv_filename}")
        print(deck.cards)

        return jsonify({"message": "deck successfully saved to CSV", "file": csv_filename})# Implementing methods to save decks created by user
    return jsonify({"error": "invalid"}), 400
    
@app.route('/quiz/<filename>') # Backend logic for true or false quiz
def quiz(filename):
    "the backend logic for the first quiz that will be mapped to its html component"
    try:
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck."}), 400 # sending an error if the content from the csv file isn't found
        
        questions = []
        for card in cards:
            questions.append({
                'term': card.term,
                'definition': card.definition,
                'correct_answer': True  # adding the correct answer to the question so the answer is true
            })
            wrong_definitions = [c.definition for c in cards if c.term != card.term]
            if wrong_definitions:
                questions.append({
                    'term': card.term,
                    'definition': random.choice(wrong_definitions),
                    'correct_answer': False  # adding the wrong definitions to a wrong answer so the user chooses false
                })
        
        random.shuffle(questions) # randomizing the questions each time
        session['current_level'] = 1 # first level of the quizzes
        return render_template('quiz.html', questions=questions)# mapping quiz.py to quiz.html
    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404 # showing an error if the csv file isn't found


@app.route('/check_answer', methods=['POST'])
def check_answer():
    "route to check the answers from the quiz"
    try:
        data = request.get_json()
        user_answer = data.get('answer')
        correct_answer = data.get('correct_answer')
        
        is_correct = user_answer == correct_answer
        
        if is_correct:
            session['score'] = session.get('score', 0) + 1
            if 'current_level' not in session:
                session['current_level'] = 1 # adding scores if the user answered correctly
        
        return jsonify({
            'correct': is_correct,
            'score': session.get('score', 0),
            'current_level': session.get('current_level', 1)
        }) # turns the data into a JSON response which is sent to the user about the score and if they answered correctly
    
    except Exception as e:
        print(f"Error in check_answer: {str(e)}")
        return jsonify({"error": "Server error"}), 500 #return an error in the server

@app.route('/quiztwo/<filename>')
def quiztwo(filename):
    "backend logic for the second quiz which users input definitions based on terms presented"
    try:
        if 'current_level' not in session:
            session['current_level'] = 1
            return redirect(url_for('quiz', filename=filename)) # to make the user has completed the first quiz or else they are redirected
        
        session['current_level'] = 2
        session['questions_answered'] = 0  # Reset counter for level 2
        
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck"}), 400

        questions = []
        for card in cards:
            questions.append({
                'term': card.term,
                'definition': card.definition # setting terms and definitions
            })

        session['total_questions'] = len(questions)  # Store total number of questions
        return render_template('quiztwo.html', questions=questions, filename=filename)# matching the html component to its backend logic

    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    "processes the answers submitted"
    data = request.get_json()
    
    if not data or 'user_answer' not in data or 'term' not in data:
        return jsonify({"error": "Missing data"}), 400

    user_answer = data['user_answer']
    term = data['term']
    filename = data.get('filename')
    
    cards = load_cards_from_csv(filename)
    if not cards:
        return jsonify({"error": "Deck not found"}), 404
    
    correct_answer = None
    for card in cards:
        if card.term == term: 
            correct_answer = card.definition  
            break # a loop that is broken when the user's term matches the card's term
    
    if user_answer.strip().lower() == correct_answer.strip().lower(): #making the code insensitive to if a capital letter is used
        session['score'] = session.get('score', 0) + 1 #checking the user's answer and giving points based on their performance
        session['questions_answered'] = session.get('questions_answered', 0) + 1 
        # Check if all questions for level 2 are answered
        if (session.get('current_level') == 2 and 
            session.get('questions_answered', 0) >= session.get('total_questions', 0)):
            session['level2_completed'] = True
            return jsonify({
                "correct": True, 
                "score": session['score'], 
                "next_question": False,
                "level_completed": True
            })
            
        return jsonify({
            "correct": True, 
            "score": session['score'], 
            "next_question": True,
            "level_completed": False
        })
    else:
        return jsonify({
            "correct": False, 
            "score": session['score'], 
            "next_question": False,
            "level_completed": False
        })


@app.route('/check_progress', methods=['GET'])
def check_progress():
    "track and return the user's progress"
    if session.get('questions_answered', 0) >= session.get('total_questions', 0):
        return jsonify({
            "quiz_complete": True, 
            "score": session.get('score', 0),
            "level_completed": session.get('level2_completed', False)
        })
    return jsonify({
        "quiz_complete": False,
        "level_completed": False
    })


@app.route('/quizthree/<filename>')
def quizthree(filename):
    "backend logic for the third quiz which is to map terms to definitions"
    try:
        # Check if level 2 was completed
        if not session.get('level2_completed', False):
            return redirect(url_for('quiztwo', filename=filename))

        # Load cards
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck"}), 400

        # Prepare the first question
        first_card = cards[0]
        other_terms = [card.term for card in cards[1:]]  # Get other terms for options
        
        # Create options list with 3 random wrong terms plus the correct term
        options = random.sample(other_terms, min(3, len(other_terms)))
        options.append(first_card.term)
        random.shuffle(options)

        # Store remaining cards in session for later use
        session['remaining_cards'] = [(card.term, card.definition) for card in cards[1:]]
        session['total_questions'] = len(cards)

        # Create the question object
        question = {
            'definition': first_card.definition,
            'options': options,
            'correct_term': first_card.term
        }

        print("Debug - Question:", question)  # Debug print

        return render_template('quizthree.html', 
                             question=question,  
                             question_number=1) 

    except Exception as e:
        print(f"Error in quizthree route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_next_question/<filename>')
def get_next_question(filename):
    "helps move on to the next question. makes sure questions are asked one at a time"
    try:
        remaining_cards = session.get('remaining_cards', [])
        total_questions = session.get('total_questions', 0)
        
        if not remaining_cards:
            return jsonify({
                "completed": True,
                "total_questions": total_questions
            })

        # Get next card and update remaining cards
        next_term, next_definition = remaining_cards[0]
        session['remaining_cards'] = remaining_cards[1:]
        
        # Get all terms from the file for options
        cards = load_cards_from_csv(filename)
        other_terms = [card.term for card in cards if card.term != next_term]
        options = random.sample(other_terms, min(3, len(other_terms)))
        options.append(next_term)
        random.shuffle(options)
        
        return jsonify({
            "completed": False,
            "definition": next_definition,
            "options": options,
            "correct_term": next_term
        })
        
    except Exception as e:
        print(f"Error in get_next_question: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

@app.route('/submit_quiz_score', methods=['POST'])
def submit_quiz_score():
    data = request.get_json()
    # Handle score submission here
    session['level3_completed'] = True
    return jsonify({"success": True})




@app.route('/check_matching_answer', methods=['POST'])
def check_matching_answer():
    "checking the answers submitted"
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data received"}), 400
        
    filename = data.get('filename')
    final_score = data.get('final_score')
    total_questions = data.get('total_questions')
    
    if None in (filename, final_score, total_questions):
        return jsonify({"error": "Missing required data"}), 400

    # Update session to mark level 3 as completed
    session['level3_completed'] = True
    
    return jsonify({
        "score": final_score,
        "total_questions": total_questions,
        "message": "Quiz completed successfully"
    }) # returns the score and the number of questions answered

if __name__ == '__main__':
    app.run(debug=True) # enables debugging