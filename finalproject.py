class Card: 
    def __init__(self, question, answer): 
        self.question = question 
        self.answer = answer 
    
class Deck: 
    def __init__(self, name): 
        self.name = name 
        self.cards = [] 

    def add_cards(self, card):
        self.cards.append(card)