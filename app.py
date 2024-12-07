from flask import Flask, render_template, request, jsonify
import csv

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


@app.route('/')
def home():
    return render_template('main.html')  
@app.route('/cont')
def about():
    return render_template('cont.html')  

@app.route('/about')
def third():
    return render_template('aboutus.html')  

@app.route('/add_card', methods = ['POST'])
#def get_data():
    #if request.method == 'POST':
        #data = request.get_json()
        #name = data['name']
        #created = data['created']
        #cards = data['cards']
       # deck = Deck(name, created)
       ## for card in cards:
            #deck.add_card(Card(card['term'], card['definition']))
    #print(deck.cards)
    #return 'value updated'
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
if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(debug=True)