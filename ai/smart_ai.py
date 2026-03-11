"""
智能双扣AI - 基于完整策略
"""
import random
from game.rules import Rules

class SmartAI:
    """智能AI - 考虑全局策略"""
    
    def __init__(self, player):
        self.player = player
    
    def choose_action(self, game_state, legal_actions):
        if not legal_actions:
            return None
        
        if isinstance(game_state, dict):
            trump_suit = game_state['trump_suit']
            first_cards = game_state.get('first_cards', [])
        else:
            trump_suit = game_state.trump_suit
            first_cards = game_state.first_cards if game_state.first_cards else []
        
        my_role = self.player.role if self.player else 'runner'
        my_team = self.player.team if self.player else 0
        hand = self.player.hand if self.player else []
        
        if not first_cards:
            return self._first_play(legal_actions, trump_suit, my_role, hand)
        
        return self._follow_play(legal_actions, first_cards, trump_suit, my_role, my_team, hand)
    
    def _first_play(self, legal_actions, trump_suit, my_role, hand):
        """首家出牌策略"""
        if my_role == 'scorer':
            return self._scorer_first(legal_actions, trump_suit, hand)
        else:
            return self._runner_first(legal_actions, trump_suit, hand)
    
    def _scorer_first(self, legal_actions, trump_suit, hand):
        """得分组首家"""
        singles = [a for a in legal_actions if len(a) == 1]
        
        score_cards = [a for a in singles if a[0].get_score() > 0]
        if score_cards:
            return random.choice(score_cards)
        
        non_trump = [a for a in singles if not Rules.is_trump(a[0], trump_suit)]
        if non_trump:
            non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]), reverse=True)
            idx = min(len(non_trump) // 2, len(non_trump) - 1)
            return non_trump[idx]
        
        return self._smallest_action(legal_actions, trump_suit)
    
    def _runner_first(self, legal_actions, trump_suit, hand):
        """跑分组首家 - 出小牌让对家拿分"""
        singles = [a for a in legal_actions if len(a) == 1]
        
        non_trump = [a for a in singles if not Rules.is_trump(a[0], trump_suit)]
        if non_trump:
            non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]))
            return non_trump[0]
        
        return self._smallest_action(legal_actions, trump_suit)
    
    def _follow_play(self, legal_actions, first_cards, trump_suit, my_role, my_team, hand):
        """跟牌策略"""
        first_score = sum(c.get_score() for c in first_cards)
        first_suit = first_cards[0].suit if not first_cards[0].is_joker else None
        first_is_trump = Rules.is_trump(first_cards[0], trump_suit)
        
        if my_role == 'scorer':
            return self._scorer_follow(legal_actions, first_cards, first_suit, first_is_trump, 
                                       first_score, trump_suit, hand)
        else:
            return self._runner_follow(legal_actions, first_cards, first_suit, first_is_trump,
                                       first_score, trump_suit, hand)
    
    def _scorer_follow(self, legal_actions, first_cards, first_suit, first_is_trump, 
                       first_score, trump_suit, hand):
        """得分组跟牌"""
        if first_score > 0:
            can_win = self._can_win(legal_actions, first_cards, trump_suit)
            if can_win:
                return self._smallest_winner(can_win, first_suit, trump_suit)
        
        return self._smallest_action(legal_actions, trump_suit, first_suit)
    
    def _runner_follow(self, legal_actions, first_cards, first_suit, first_is_trump,
                      first_score, trump_suit, hand):
        """跑分组跟牌"""
        if first_is_trump:
            trump_actions = [a for a in legal_actions if len(a) == 1 and Rules.is_trump(a[0], trump_suit)]
            if trump_actions:
                if first_score > 0:
                    can_win = [a for a in trump_actions if self._can_win_single(a[0], first_cards[0], trump_suit)]
                    if can_win:
                        return random.choice(can_win)
                return self._smallest_action(legal_actions, trump_suit, first_suit)
        
        if first_score > 0:
            can_win = self._can_win(legal_actions, first_cards, trump_suit)
            if can_win:
                return random.choice(can_win)
        
        return self._smallest_action(legal_actions, trump_suit, first_suit)
    
    def _can_win(self, legal_actions, first_cards, trump_suit):
        """找出能赢的牌"""
        if not first_cards:
            return legal_actions
        
        first = first_cards[0]
        first_suit = None if first.is_joker else first.suit
        first_strength = self._get_strength(first, first_suit, trump_suit)
        
        winners = []
        for action in legal_actions:
            if len(action) == 1:
                s = self._get_strength(action[0], first_suit, trump_suit)
                if s > first_strength:
                    winners.append(action)
        
        return winners
    
    def _can_win_single(self, action_card, first_card, trump_suit):
        first_suit = None if first_card.is_joker else first_card.suit
        my_strength = self._get_strength(action_card, first_suit, trump_suit)
        first_strength = self._get_strength(first_card, first_suit, trump_suit)
        return my_strength > first_strength
    
    def _get_strength(self, card, first_suit, trump_suit):
        if Rules.is_trump(card, trump_suit):
            return 1000 + Rules.get_trump_strength(card, trump_suit)
        elif card.suit == first_suit:
            return 100 + Rules.get_suit_strength(card)
        else:
            return 0
    
    def _smallest_winner(self, winners, first_suit, trump_suit):
        if not winners:
            return None
        winners.sort(key=lambda x: self._get_strength(x[0], first_suit, trump_suit))
        return winners[0]
    
    def _smallest_action(self, legal_actions, trump_suit, first_suit=None):
        """选择最小的牌"""
        if not legal_actions:
            return None
        
        singles = [a for a in legal_actions if len(a) == 1]
        
        if first_suit:
            same_suit = [a for a in singles if a[0].suit == first_suit and not Rules.is_trump(a[0], trump_suit)]
            if same_suit:
                same_suit.sort(key=lambda x: self._get_strength(x[0], first_suit, trump_suit))
                return same_suit[0]
        
        non_trump = [a for a in singles if not Rules.is_trump(a[0], trump_suit)]
        if non_trump:
            non_trump.sort(key=lambda x: self._get_strength(x[0], None, trump_suit))
            return non_trump[0]
        
        singles.sort(key=lambda x: self._get_strength(x[0], None, trump_suit))
        return singles[0]
