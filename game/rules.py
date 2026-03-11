from game.card import Card

class Rules:
    @staticmethod
    def is_trump(card, trump_suit):
        """判断是否为主牌"""
        if card.is_joker:
            return True
        if card.suit == trump_suit:
            return True
        if card.rank in ['5', '3', '2']:
            return True
        return False
    
    @staticmethod
    def get_trump_strength(card, trump_suit):
        """获取主牌强度值"""
        # 主牌强度顺序：主花色5 > 大王 > 小王 > 其他花色5 > 主花色3 > 其他花色3 > 主花色2 > 其他花色2 > 主花色A > ...
        strength_order = [
            f"{trump_suit}5",
            "大王", "小王",
            "黑桃5", "红心5", "梅花5", "方块5",
            f"{trump_suit}3",
            "黑桃3", "红心3", "梅花3", "方块3",
            f"{trump_suit}2",
            "黑桃2", "红心2", "梅花2", "方块2",
            f"{trump_suit}A", f"{trump_suit}K", f"{trump_suit}Q", f"{trump_suit}J",
            f"{trump_suit}10", f"{trump_suit}9", f"{trump_suit}8", f"{trump_suit}7",
            f"{trump_suit}6", f"{trump_suit}4"
        ]
        
        card_str = str(card)
        if card_str in strength_order:
            return 1000 - strength_order.index(card_str)
        return 0
    
    @staticmethod
    def get_suit_strength(card):
        """获取副牌强度值"""
        if card.is_joker:
            return 0
        
        strength_order = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '4']
        if card.rank in strength_order:
            return 100 - strength_order.index(card.rank)
        return 0
    
    @staticmethod
    def compare_cards(cards_list, first_suit, trump_suit):
        """比较多个人出的牌，返回最大的牌的索引"""
        max_strength = -1
        max_index = 0
        
        for i, cards in enumerate(cards_list):
            strength = Rules._calculate_play_strength(cards, first_suit, trump_suit)
            if strength > max_strength:
                max_strength = strength
                max_index = i
        
        return max_index
    
    @staticmethod
    def _calculate_play_strength(cards, first_suit, trump_suit):
        """计算出牌的强度"""
        if len(cards) == 1:
            return Rules._calculate_single_strength(cards[0], first_suit, trump_suit)
        else:  # 对子
            return Rules._calculate_pair_strength(cards, first_suit, trump_suit)
    
    @staticmethod
    def _calculate_single_strength(card, first_suit, trump_suit):
        """计算单张牌的强度"""
        if Rules.is_trump(card, trump_suit):
            return Rules.get_trump_strength(card, trump_suit)
        elif card.suit == first_suit:
            return Rules.get_suit_strength(card)
        else:
            return 0  # 其他花色的副牌
    
    @staticmethod
    def _calculate_pair_strength(cards, first_suit, trump_suit):
        """计算对子的强度"""
        if len(cards) != 2:
            return 0
        
        # 检查是否是对子
        if not Rules.is_valid_pair(cards):
            # 不是对子，按两张单牌处理
            strength1 = Rules._calculate_single_strength(cards[0], first_suit, trump_suit)
            strength2 = Rules._calculate_single_strength(cards[1], first_suit, trump_suit)
            return min(strength1, strength2)  # 两张单牌取最小值
        
        # 是对子
        card = cards[0]
        if Rules.is_trump(card, trump_suit):
            return 2000 + Rules.get_trump_strength(card, trump_suit)
        elif card.suit == first_suit:
            return 1000 + Rules.get_suit_strength(card)
        else:
            return 0  # 其他花色的副牌对
    
    @staticmethod
    def is_valid_pair(cards):
        """判断是否为合法对子"""
        if len(cards) != 2:
            return False
        
        card1, card2 = cards
        # 两张大王或两张小王
        if card1.is_joker and card2.is_joker:
            return card1.rank == card2.rank
        # 同花色同点数
        return card1.suit == card2.suit and card1.rank == card2.rank
    
    @staticmethod
    def get_legal_actions(hand, first_cards, trump_suit):
        """获取所有合法的出牌"""
        if not first_cards:  # 首家出牌
            return Rules._get_first_player_actions(hand)
        else:  # 跟牌
            return Rules._get_following_actions(hand, first_cards, trump_suit)
    
    @staticmethod
    def _get_first_player_actions(hand):
        """首家可以出任意单张或对子"""
        actions = []
        
        # 所有单张
        for card in hand:
            actions.append([card])
        
        # 所有对子
        seen = set()
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                card1, card2 = hand[i], hand[j]
                if Rules.is_valid_pair([card1, card2]):
                    action = sorted([card1, card2], key=lambda x: str(x))
                    action_tuple = tuple(action)
                    if action_tuple not in seen:
                        actions.append(action)
                        seen.add(action_tuple)
        
        return actions
    
    @staticmethod
    def _get_following_actions(hand, first_cards, trump_suit):
        """根据首家出牌生成合法的跟牌"""
        actions = []
        is_pair = len(first_cards) == 2
        first_suit = first_cards[0].suit if not first_cards[0].is_joker else None
        
        if is_pair:
            # 跟对子
            actions.extend(Rules._get_pair_responses(hand, first_cards, trump_suit, first_suit))
        else:
            # 跟单张
            actions.extend(Rules._get_single_responses(hand, first_cards, trump_suit, first_suit))
        
        return actions
    
    @staticmethod
    def _get_single_responses(hand, first_cards, trump_suit, first_suit):
        """生成单张跟牌"""
        actions = []
        first_card = first_cards[0]
        first_is_trump = Rules.is_trump(first_card, trump_suit)
        
        if first_is_trump:
            trump_cards = [card for card in hand if Rules.is_trump(card, trump_suit)]
            if trump_cards:
                for card in trump_cards:
                    actions.append([card])
            else:
                for card in hand:
                    actions.append([card])
        else:
            same_suit_cards = [card for card in hand if card.suit == first_suit and not Rules.is_trump(card, trump_suit)]
            
            if same_suit_cards:
                for card in same_suit_cards:
                    actions.append([card])
            else:
                for card in hand:
                    actions.append([card])
        
        return actions
    
    @staticmethod
    def _get_pair_responses(hand, first_cards, trump_suit, first_suit):
        """生成对子跟牌"""
        actions = []
        first_is_trump = Rules.is_trump(first_cards[0], trump_suit)
        
        if first_is_trump:
            trump_pairs = []
            seen = set()
            for i in range(len(hand)):
                for j in range(i + 1, len(hand)):
                    card1, card2 = hand[i], hand[j]
                    if Rules.is_valid_pair([card1, card2]) and Rules.is_trump(card1, trump_suit):
                        pair = sorted([card1, card2], key=lambda x: str(x))
                        pair_tuple = tuple(pair)
                        if pair_tuple not in seen:
                            trump_pairs.append(pair)
                            seen.add(pair_tuple)
            
            if trump_pairs:
                actions.extend(trump_pairs)
            else:
                trump_cards = [card for card in hand if Rules.is_trump(card, trump_suit)]
                if len(trump_cards) >= 2:
                    trump_cards.sort(key=lambda x: Rules.get_trump_strength(x, trump_suit), reverse=True)
                    actions.append(trump_cards[:2])
                elif len(trump_cards) == 1:
                    for card in hand:
                        if card != trump_cards[0]:
                            actions.append([trump_cards[0], card])
                else:
                    for i in range(len(hand)):
                        for j in range(i + 1, len(hand)):
                            actions.append([hand[i], hand[j]])
        else:
            same_suit_pairs = []
            seen = set()
            
            for i in range(len(hand)):
                for j in range(i + 1, len(hand)):
                    card1, card2 = hand[i], hand[j]
                    if Rules.is_valid_pair([card1, card2]) and card1.suit == first_suit and not Rules.is_trump(card1, trump_suit):
                        pair = sorted([card1, card2], key=lambda x: str(x))
                        pair_tuple = tuple(pair)
                        if pair_tuple not in seen:
                            same_suit_pairs.append(pair)
                            seen.add(pair_tuple)
            
            if same_suit_pairs:
                actions.extend(same_suit_pairs)
            else:
                same_suit_cards = [card for card in hand if card.suit == first_suit and not Rules.is_trump(card, trump_suit)]
                
                if len(same_suit_cards) >= 2:
                    same_suit_cards.sort(key=lambda x: Rules.get_suit_strength(x), reverse=True)
                    actions.append(same_suit_cards[:2])
                elif len(same_suit_cards) == 1:
                    for card in hand:
                        if card != same_suit_cards[0]:
                            actions.append([same_suit_cards[0], card])
                else:
                    for i in range(len(hand)):
                        for j in range(i + 1, len(hand)):
                            actions.append([hand[i], hand[j]])
        
        return actions
    
    @staticmethod
    def calculate_round_score(cards_list):
        """计算本轮得分"""
        score = 0
        for cards in cards_list:
            for card in cards:
                score += card.get_score()
        return score