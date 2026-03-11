import copy
import random
from game.card import Card
from game.rules import Rules

class GameState:
    """可复制的游戏状态，用于MCTS模拟"""
    
    def __init__(self, hands, trump_suit, current_player, played_cards, 
                 first_cards, scores, team_scorer, roles):
        self.hands = hands
        self.trump_suit = trump_suit
        self.current_player = current_player
        self.played_cards = played_cards
        self.first_cards = first_cards
        self.scores = scores
        self.team_scorer = team_scorer
        self.roles = roles
    
    @classmethod
    def from_game(cls, game):
        """从Game对象创建GameState"""
        hands = [[Card(c.suit, c.rank) for c in p.hand] for p in game.players]
        trump_suit = game.trump_suit
        current_player = game.current_player_index
        played_cards = []
        first_cards = []
        scores = game.scores.copy()
        team_scorer = game.team_scorer
        roles = [p.role for p in game.players]
        
        return cls(hands, trump_suit, current_player, played_cards, 
                   first_cards, scores, team_scorer, roles)
    
    def clone(self):
        """深拷贝当前状态"""
        return GameState(
            hands=[hand.copy() for hand in self.hands],
            trump_suit=self.trump_suit,
            current_player=self.current_player,
            played_cards=[cards.copy() for cards in self.played_cards],
            first_cards=self.first_cards.copy() if self.first_cards else [],
            scores=self.scores.copy(),
            team_scorer=self.team_scorer,
            roles=self.roles.copy()
        )
    
    def get_legal_actions(self):
        """获取当前玩家的合法出牌"""
        hand = self.hands[self.current_player]
        return Rules.get_legal_actions(hand, self.first_cards, self.trump_suit)
    
    def apply_action(self, action):
        """应用一个动作，更新状态"""
        hand = self.hands[self.current_player]
        
        for card in action:
            for i, c in enumerate(hand):
                if c.suit == card.suit and c.rank == card.rank:
                    hand.pop(i)
                    break
        
        if not self.first_cards:
            self.first_cards = action.copy()
        
        self.played_cards.append(action)
        
        if len(self.played_cards) == 4:
            self._resolve_round()
        else:
            self.current_player = (self.current_player + 1) % 4
    
    def _resolve_round(self):
        """结算一轮"""
        first_suit = self.first_cards[0].suit if not self.first_cards[0].is_joker else None
        winner_offset = Rules.compare_cards(self.played_cards, first_suit, self.trump_suit)
        winner = (self.current_player + winner_offset) % 4
        
        round_score = Rules.calculate_round_score(self.played_cards)
        if self.roles[winner] == 'scorer':
            self.scores[self.team_scorer] += round_score
        
        self.current_player = winner
        self.played_cards = []
        self.first_cards = []
    
    def is_terminal(self):
        """检查游戏是否结束"""
        return all(len(hand) == 0 for hand in self.hands)
    
    def get_result(self, player_index):
        """获取游戏结果（从指定玩家视角）"""
        score = self.scores[self.team_scorer]
        player_team = player_index % 2
        
        if self.team_scorer == player_team:
            if score > 115:
                return 1.0
            elif score < 85:
                return -1.0
            else:
                return 0.0
        else:
            if score > 115:
                return -1.0
            elif score < 85:
                return 1.0
            else:
                return 0.0
    
    def get_current_player_team(self):
        """获取当前玩家的队伍"""
        return self.current_player % 2
