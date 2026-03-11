"""
极简双扣AI - 基于游戏规则的朴素策略
"""
import random
from game.rules import Rules

class SimpleAI:
    """极简AI - 严格遵循双扣规则"""
    
    def __init__(self, player):
        self.player = player
    
    def choose_action(self, game_state, legal_actions):
        if not legal_actions:
            return None
        
        trump_suit = game_state['trump_suit'] if isinstance(game_state, dict) else game_state.trump_suit
        first_cards = game_state.get('first_cards', []) if isinstance(game_state, dict) else (game_state.first_cards if game_state.first_cards else [])
        
        my_role = self.player.role if self.player else 'runner'
        
        if not first_cards:
            return self._first_action(legal_actions, trump_suit, my_role)
        
        return self._follow_action(legal_actions, first_cards, trump_suit, my_role)
    
    def _first_action(self, legal_actions, trump_suit, my_role):
        """首家出牌"""
        if my_role == 'runner':
            singles = [a for a in legal_actions if len(a) == 1]
            non_trump = [a for a in singles if not Rules.is_trump(a[0], trump_suit)]
            if non_trump:
                non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]))
                return non_trump[0]
            if singles:
                singles.sort(key=lambda x: Rules.get_trump_strength(x[0], trump_suit))
                return singles[0]
        
        return legal_actions[0]
    
    def _follow_action(self, legal_actions, first_cards, trump_suit, my_role):
        """跟牌"""
        first = first_cards[0]
        first_suit = None if first.is_joker else first.suit
        first_score = first.get_score()
        
        can_win = []
        for action in legal_actions:
            if len(action) == 1:
                if Rules.is_trump(action[0], trump_suit):
                    if Rules.is_trump(first, trump_suit):
                        if Rules.get_trump_strength(action[0], trump_suit) > Rules.get_trump_strength(first, trump_suit):
                            can_win.append(action)
                elif action[0].suit == first_suit and not Rules.is_trump(first, trump_suit):
                    if Rules.get_suit_strength(action[0]) > Rules.get_suit_strength(first):
                        can_win.append(action)
        
        if can_win:
            if my_role == 'scorer' and first_score > 0:
                can_win.sort(key=lambda x: self._get_strength(x[0], first_suit, trump_suit))
                return can_win[0]
            elif my_role == 'runner' and first_score > 0:
                return random.choice(can_win)
        
        return self._play_smallest(legal_actions, trump_suit, first_suit)
    
    def _play_smallest(self, legal_actions, trump_suit, first_suit):
        """出最小的牌"""
        singles = [a for a in legal_actions if len(a) == 1]
        
        if first_suit:
            same = [a for a in singles if a[0].suit == first_suit and not Rules.is_trump(a[0], trump_suit)]
            if same:
                same.sort(key=lambda x: Rules.get_suit_strength(x[0]))
                return same[0]
        
        non_trump = [a for a in singles if not Rules.is_trump(a[0], trump_suit)]
        if non_trump:
            non_trump.sort(key=lambda x: Rules.get_suit_strength(x[0]))
            return non_trump[0]
        
        singles.sort(key=lambda x: Rules.get_trump_strength(x[0], trump_suit))
        return singles[0]
    
    def _get_strength(self, card, first_suit, trump_suit):
        if Rules.is_trump(card, trump_suit):
            return 1000 + Rules.get_trump_strength(card, trump_suit)
        elif card.suit == first_suit:
            return 100 + Rules.get_suit_strength(card)
        return 0
