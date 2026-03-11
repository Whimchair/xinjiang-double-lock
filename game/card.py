class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # 黑桃, 红心, 梅花, 方块, Joker
        self.rank = rank  # 2-10, J, Q, K, A, 大王, 小王
    
    def __repr__(self):
        if self.suit == 'Joker':
            return self.rank
        return f"{self.suit}{self.rank}"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self):
        return hash((self.suit, self.rank))

    @property
    def is_joker(self):
        return self.suit == 'Joker'

    @property
    def is_score_card(self):
        return self.rank in ['5', '10', 'K']

    def get_score(self):
        if self.rank == 'K' or self.rank == '10':
            return 10
        elif self.rank == '5':
            return 5
        return 0