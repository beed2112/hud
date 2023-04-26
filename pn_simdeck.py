from deuces import Card
from random import shuffle

#Class representing a deck used for simulations. 
class SimDeck:
    DECK = []

    def __init__(self):
        self.shuffle()

    def shuffle(self):
        self.cards = SimDeck.GetFullDeck()
        shuffle(self.cards)

    def draw(self, n=1):
        if n == 1:
            return self.cards.pop(0)
        cards = []
        for i in range(n):
            cards.append(self.draw())
        return cards

    @staticmethod
    def GetFullDeck():
        if SimDeck.DECK:
            return list(SimDeck.DECK)

        #Create Deck
        for rank in Card.STR_RANKS:
            for suit,val in Card.CHAR_SUIT_TO_INT_SUIT.items():
                SimDeck.DECK.append(Card.new(rank + suit))

        return list(SimDeck.DECK)
