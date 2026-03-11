import random
from game.card import Card

class Deck:
    def __init__(self):
        self.cards = self._create_deck()
    
    def _create_deck(self):
        suits = ['黑桃', '红心', '梅花', '方块']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        deck = []
        # 两副牌
        for _ in range(2):
            for suit in suits:
                for rank in ranks:
                    deck.append(Card(suit, rank))
            # 加入大小王（两副）
            deck.append(Card('Joker', '大王'))
            deck.append(Card('Joker', '小王'))
        
        return deck
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal(self, players):
        """发牌给4个玩家"""
        hands = [[], [], [], []]
        
        for i, card in enumerate(self.cards):
            hands[i % 4].append(card)
        
        for i, hand in enumerate(hands):
            players[i].hand = hand
        
        return hands
    
    def deal_one_by_one(self, players):
        """
        逐张发牌，每发一张牌返回一次
        返回: (玩家索引, 发出的牌, 当前轮次)
        """
        for i, card in enumerate(self.cards):
            player_index = i % 4
            players[player_index].hand.append(card)
            round_num = i // 4 + 1  # 当前第几轮
            yield (player_index, card, round_num)
    
    def get_card_count(self):
        return len(self.cards)