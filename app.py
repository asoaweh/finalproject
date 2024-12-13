from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import csv
import random 

app = Flask(__name__)
app.secret_key = 'your_secret_key'
class Card: 
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
        self.cards.append(card)

    def to_csv(self, filename):  
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Term', 'Definition'])
            for card in self.cards:
                writer.writerow([card.term, card.definition])

def load_cards_from_csv(filename):
    cards = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            cards.append(Card(row['Term'], row['Definition']))
    return cards

@app.route('/')
def home():
    return render_template('main.html')  
@app.route('/cont')
def about():
    return render_template('cont.html')  

@app.route('/about')
def third():
    return render_template('aboutus.html')  

@app.route('/add_card', methods=['POST'])
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

        deck.to_csv(csv_filename)

        print(f"Deck saved to {csv_filename}")
        print(deck.cards)

        return jsonify({"message": "deck successfully saved to CSV", "file": csv_filename})
    return jsonify({"error": "invalid"}), 400
    
@app.route('/quiz/<filename>')
def quiz(filename):
    try:
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck."}), 400
        
        questions = []
        for card in cards:
            questions.append({
                'term': card.term,
                'definition': card.definition,
                'correct_answer': True  
            })
            wrong_definitions = [c.definition for c in cards if c.term != card.term]
            if wrong_definitions:
                questions.append({
                    'term': card.term,
                    'definition': random.choice(wrong_definitions),
                    'correct_answer': False  
                })
        
        random.shuffle(questions)
        session['current_level'] = 1
        return render_template('quiz.html', questions=questions)
    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404


@app.route('/check_answer', methods=['POST'])
def check_answer():
    try:
        data = request.get_json()
        user_answer = data.get('answer')
        correct_answer = data.get('correct_answer')
        
        is_correct = user_answer == correct_answer
        
        if is_correct:
            session['score'] = session.get('score', 0) + 1
            if 'current_level' not in session:
                session['current_level'] = 1
        
        return jsonify({
            'correct': is_correct,
            'score': session.get('score', 0),
            'current_level': session.get('current_level', 1)
        })
    
    except Exception as e:
        print(f"Error in check_answer: {str(e)}")
        return jsonify({"error": "Server error"}), 500

@app.route('/quiztwo/<filename>')
def quiztwo(filename):
    try:
        if 'current_level' not in session:
            session['current_level'] = 1
            return redirect(url_for('quiz', filename=filename))
        
        session['current_level'] = 2
        session['questions_answered'] = 0  # Reset counter for level 2
        
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck"}), 400

        questions = []
        for card in cards:
            questions.append({
                'term': card.term,
                'definition': card.definition
            })

        session['total_questions'] = len(questions)  # Store total number of questions
        return render_template('quiztwo.html', questions=questions, filename=filename)

    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
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
            break
    
    if user_answer.strip().lower() == correct_answer.strip().lower():
        session['score'] = session.get('score', 0) + 1
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
                             question=question,  # Changed from current_question to question
                             question_number=1)  # Changed from current_question_index to question_number

    except Exception as e:
        print(f"Error in quizthree route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_next_question/<filename>')
def get_next_question(filename):
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
    })

if __name__ == '__main__':
    app.run(debug=True)