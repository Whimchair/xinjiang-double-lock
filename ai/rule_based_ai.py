import random
from game.rules import Rules

class RuleBasedAI:
    """改进后的规则AI - 更智能的贪心策略"""
    
    def __init__(self, player):
        self.player = player
    
    def choose_action(self, game_state, legal_actions):
        """选择出牌动作"""
        if not legal_actions:
            return None
        
        if isinstance(game_state, dict):
            trump_suit = game_state['trump_suit']
            first_cards = game_state.get('first_cards', [])
        else:
            trump_suit = game_state.trump_suit
            first_cards = game_state.first_cards if game_state.first_cards else []
        
        my_role = self.player.role if self.player else 'runner'
        
        if not first_cards:
            return self._choose_first_action(legal_actions, trump_suit, my_role)
        
        return self._choose_follow_action(legal_actions, first_cards, trump_suit, my_role)
    
    def _choose_first_action(self, legal_actions, trump_suit, my_role):
        """首家出牌策略 - 改进版"""
        
        if my_role == 'scorer':
            return self._scorer_first_action(legal_actions, trump_suit)
        else:
            return self._runner_first_action(legal_actions, trump_suit)
    
    def _scorer_first_action(self, legal_actions, trump_suit):
        """得分组首家出牌"""
        # 优先出副牌中较大的牌（避免被他人接管）
        # 或者出分牌引诱对方
        
        score_cards = []
        non_trump = []
        
        for action in legal_actions:
            if len(action) == 1:
                if action[0].get_score() > 0:
                    score_cards.append(action)
                elif not Rules.is_trump(action[0], trump_suit):
                    non_trump.append(action)
        
        if score_cards:
            return random.choice(score_cards)
        
        if non_trump:
            # 出中等大小的副牌
            non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]), reverse=True)
            return non_trump[len(non_trump)//2]
        
        # 只能出主牌时，出最小的
        return self._choose_smallest_trump(legal_actions, trump_suit)
    
    def _runner_first_action(self, legal_actions, trump_suit):
        """跑分组首家出牌"""
        # 出小副牌，让对家拿分，或者出大牌控制
        
        non_trump = [a for a in legal_actions if len(a) == 1 and not Rules.is_trump(a[0], trump_suit)]
        
        if non_trump:
            # 出最小的副牌
            non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]))
            return non_trump[0]
        
        # 出最小的牌
        return self._choose_smallest_card(legal_actions, trump_suit)
    
    def _choose_follow_action(self, legal_actions, first_cards, trump_suit, my_role):
        """跟牌策略 - 改进版"""
        
        first_is_pair = len(first_cards) == 2
        round_score = self._estimate_round_score(first_cards)
        
        if my_role == 'scorer':
            return self._scorer_follow_action(legal_actions, first_cards, trump_suit, round_score)
        else:
            return self._runner_follow_action(legal_actions, first_cards, trump_suit, round_score)
    
    def _scorer_follow_action(self, legal_actions, first_cards, trump_suit, round_score):
        """得分组跟牌"""
        
        if round_score > 0:
            winning = self._get_winning_actions(legal_actions, first_cards, trump_suit)
            if winning:
                return self._choose_smallest_winner(winning, first_cards, trump_suit)
        
        return self._choose_smallest_card(legal_actions, trump_suit)
    
    def _runner_follow_action(self, legal_actions, first_cards, trump_suit, round_score):
        """跑分组跟牌"""
        
        if round_score > 0:
            winning = self._get_winning_actions(legal_actions, first_cards, trump_suit)
            if winning:
                # 阻止对方拿分
                return random.choice(winning)
        
        # 尽量出小牌
        return self._choose_smallest_card(legal_actions, trump_suit)
    
    def _get_winning_actions(self, legal_actions, first_cards, trump_suit):
        """找出所有能赢的出牌"""
        first_suit = first_cards[0].suit if not first_cards[0].is_joker else None
        first_strength = self._calculate_strength(first_cards[0], first_suit, trump_suit)
        
        winning = []
        for action in legal_actions:
            action_strength = self._calculate_strength(action[0], first_suit, trump_suit)
            if action_strength > first_strength:
                winning.append(action)
        
        return winning
    
    def _calculate_strength(self, card, first_suit, trump_suit):
        """计算单张牌强度"""
        if Rules.is_trump(card, trump_suit):
            return Rules.get_trump_strength(card, trump_suit)
        elif card.suit == first_suit:
            return Rules.get_suit_strength(card)
        else:
            return 0
    
    def _choose_smallest_winner(self, winning_actions, first_cards, trump_suit):
        """选择最小的赢牌"""
        first_suit = first_cards[0].suit if not first_cards[0].is_joker else None
        
        winning_actions.sort(key=lambda x: self._calculate_strength(x[0], first_suit, trump_suit))
        return winning_actions[0]
    
    def _choose_smallest_card(self, legal_actions, trump_suit):
        """选择最小的牌"""
        if not legal_actions:
            return None
        
        # 优先出副牌
        non_trump = [a for a in legal_actions if len(a) == 1 and not Rules.is_trump(a[0], trump_suit)]
        
        if non_trump:
            non_trump.sort(key=lambda x: self._calculate_strength(x[0], None, trump_suit))
            return non_trump[0]
        
        # 只能出主牌
        legal_actions.sort(key=lambda x: self._calculate_strength(x[0], None, trump_suit))
        return legal_actions[0]
    
    def _choose_smallest_trump(self, legal_actions, trump_suit):
        """选择最小的主牌"""
        legal_actions.sort(key=lambda x: Rules.get_trump_strength(x[0], trump_suit))
        return legal_actions[0]
    
    def _estimate_round_score(self, first_cards):
        """估算当前轮的得分"""
        score = 0
        for card in first_cards:
            score += card.get_score()
        return score
