from flask import Flask, render_template, request, jsonify
import csv
import random 

app = Flask(__name__)
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
        return render_template('quiz.html', questions=questions)
    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404
    
@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user_answer = data['answer']
    correct_answer = data['correct_answer']
    
    is_correct = user_answer == correct_answer
    
    return jsonify({'correct': is_correct})

@app.route('/quizthree/<filename>')
def quizthree(filename):
    try:
        cards = load_cards_from_csv(filename)
        if not cards:
            return jsonify({"error": "No cards found in the deck"}), 400
        
        questions = []
        for card in cards:
            wrong_definitions = [c.definition for c in cards if c.term != card.term]
            definitions = [card.definition] + random.sample(wrong_definitions, 3)
            random.shuffle(definitions)
            
            questions.append({
                'term': card.term,
                'definitions': definitions,
                'correct_answer': card.definition
            })
        
        random.shuffle(questions)
        return render_template('quizthree.html', questions=questions)
    except FileNotFoundError:
        return jsonify({"error": "Deck not found"}), 404

@app.route('/check_matching_answer', methods=['POST'])
def check_matching_answer():
    data = request.get_json()
    user_answers = data['answers']
    filename = data['filename']
    score = 0

    cards = load_cards_from_csv(filename)
    if not cards:
        return jsonify({"error": "Deck not found"}), 404

    for term, user_answer in user_answers.items():
        correct_answer = None
        for card in cards:
            if card.term == term:
                correct_answer = card.definition
                break

        if user_answer == correct_answer:
            score += 1

    return jsonify({"score": score})

if __name__ == '__main__':
    app.run(debug=True)