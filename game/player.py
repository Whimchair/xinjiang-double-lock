class Player:
    def __init__(self, name=None, ai=None):
        self.name = name or f"玩家{id(self) % 100}"
        self.hand = []  # 手牌
        self.team = None  # 队伍 (0或1)
        self.role = None  # 角色: scorer或runner
        self.is_dealer = False
        self.ai = ai  # AI控制器
    
    def __repr__(self):
        return f"{self.name}(队{self.team})"
    
    def has_pair(self):
        """检查是否有对子"""
        card_counts = {}
        for card in self.hand:
            key = (card.suit, card.rank)
            card_counts[key] = card_counts.get(key, 0) + 1
            if card_counts[key] == 2:
                return True
        return False
    
    def check_new_card_pair(self, new_card):
        """
        检查新发的牌是否与手牌中的牌形成对子
        返回: (是否有对子, 对子的花色, 对子的点数)
        """
        for card in self.hand:
            if card is not new_card and card.suit == new_card.suit and card.rank == new_card.rank:
                return (True, card.suit, card.rank)
        return (False, None, None)
    
    def get_pairs(self):
        """获取所有对子"""
        card_counts = {}
        pairs = []
        
        for card in self.hand:
            key = (card.suit, card.rank)
            card_counts[key] = card_counts.get(key, 0) + 1
        
        for (suit, rank), count in card_counts.items():
            if count >= 2:
                pairs.append((suit, rank))
        
        return pairs
    
    def remove_cards(self, cards):
        """从手牌中移除指定的牌"""
        for card in cards:
            if card in self.hand:
                self.hand.remove(card)
    
    def add_cards(self, cards):
        """向手牌中添加牌"""
        self.hand.extend(cards)
    
    def get_hand_strength(self, trump_suit):
        """评估手牌强度"""
        # 简单的强度评估
        strength = 0
        for card in self.hand:
            if self._is_trump(card, trump_suit):
                strength += 2
            else:
                strength += 1
        return strength
    
    def _is_trump(self, card, trump_suit):
        """判断是否为主牌"""
        if card.is_joker:
            return True
        if card.suit == trump_suit:
            return True
        if card.rank in ['5', '3', '2']:
            return True
        return False