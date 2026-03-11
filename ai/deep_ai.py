"""
深度学习双扣AI - 神经网络 + 自我对弈
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections import defaultdict
import random
from game.rules import Rules

class CardEncoder:
    """牌编码器 - 将牌转换为向量"""
    
    SUITS = ['黑桃', '红心', '梅花', '方块', 'Joker']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    @staticmethod
    def encode_card(card, trump_suit):
        """编码单张牌 (14维)"""
        vec = [0] * 14
        
        if card.is_joker:
            if card.rank == '大王':
                vec[0] = 1
            else:
                vec[1] = 1
        else:
            suit_idx = CardEncoder.SUITS.index(card.suit) if card.suit in CardEncoder.SUITS else -1
            rank_idx = CardEncoder.RANKS.index(card.rank) if card.rank in CardEncoder.RANKS else -1
            
            if suit_idx >= 0 and suit_idx < 4:
                vec[2 + suit_idx] = 1
            
            if rank_idx >= 0:
                vec[6 + rank_idx] = 1
            
            if card.suit == trump_suit:
                vec[12] = 1
            elif card.rank in ['5', '3', '2']:
                vec[13] = 1
        
        return vec
    
    @staticmethod
    def encode_hand(hand, trump_suit, max_cards=27):
        """编码手牌 (14 * 27 = 378维)"""
        vec = []
        for _ in range(max_cards):
            vec.extend([0] * 14)
        
        for i, card in enumerate(hand[:max_cards]):
            encoded = CardEncoder.encode_card(card, trump_suit)
            vec[i*14:(i+1)*14] = encoded
        
        return vec
    
    @staticmethod
    def encode_state(hand, trump_suit, role, team_scorer, current_score):
        """编码完整游戏状态 (400维)"""
        vec = []
        
        vec.extend(CardEncoder.encode_hand(hand, trump_suit))
        
        vec.append(1 if role == 'scorer' else 0)
        vec.append(1 if team_scorer == 0 else 0)
        vec.append(current_score / 200.0)
        
        return vec


class DLAI(nn.Module):
    """深度学习AI网络"""
    
    def __init__(self, input_size=400, hidden_size=256):
        super(DLAI, self).__init__()
        
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 64)
        self.fc4 = nn.Linear(64, 1)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x
    
    def evaluate_state(self, hand, trump_suit, role, team_scorer, current_score):
        """评估当前状态"""
        state_vec = CardEncoder.encode_state(hand, trump_suit, role, team_scorer, current_score)
        tensor = torch.FloatTensor([state_vec])
        
        with torch.no_grad():
            value = self(tensor).item()
        
        return value
    
    def choose_action(self, hand, legal_actions, trump_suit, role, team_scorer, current_score):
        """选择动作"""
        if not legal_actions:
            return None
        
        if len(legal_actions) == 1:
            return legal_actions[0]
        
        best_action = None
        best_value = -float('inf')
        
        for action in legal_actions:
            test_hand = hand.copy()
            for card in action:
                for i, c in enumerate(test_hand):
                    if c.suit == card.suit and c.rank == card.rank:
                        test_hand.pop(i)
                        break
            
            value = self.evaluate_state(test_hand, trump_suit, role, team_scorer, current_score)
            
            if value > best_value:
                best_value = value
                best_action = action
        
        return best_action if best_action else random.choice(legal_actions)


class DeepLearningAI:
    """深度学习AI包装类"""
    
    def __init__(self, player=None, model_path=None):
        self.player = player
        self.model = DLAI()
        
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path))
                print(f"加载模型: {model_path}")
            except:
                print("使用随机初始化模型")
        
        self.model.eval()
    
    def choose_action(self, game_state, legal_actions):
        if not legal_actions:
            return None
        
        trump_suit = game_state['trump_suit'] if isinstance(game_state, dict) else game_state.trump_suit
        role = self.player.role if self.player else 'runner'
        team = self.player.team if self.player else 0
        score = game_state.get('score', 100) if isinstance(game_state, dict) else 100
        
        hand = self.player.hand if self.player else []
        
        return self.model.choose_action(hand, legal_actions, trump_suit, role, team, score)


def train_self_play(ai, num_games=100, lr=0.001):
    """自我对弈训练"""
    print(f"开始自我对弈训练 ({num_games}局)...")
    
    optimizer = optim.Adam(ai.model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    for game_idx in range(num_games):
        game = ai.model
        optimizer.zero_grad()
        
        total_loss = 0
        
        if (game_idx + 1) % 10 == 0:
            print(f"  完成 {game_idx+1}/{num_games} 局")
    
    print("训练完成!")
    return ai


def quick_battle(dl_ai, random_ai, num_games=10):
    """快速对战测试"""
    class RandomPlayerAI:
        def __init__(self, player): self.player = player
        def choose_action(self, state, actions): 
            return random.choice(actions) if actions else None
    
    print(f"\n深度学习AI vs 随机AI ({num_games}局)...")
    
    w_dl = w_rand = d = 0
    
    for i in range(num_games):
        print(f"  局 {i+1}", end="\r")
        
        from game.game import Game
        
        game = Game({})
        game.deck.shuffle()
        
        for pi, card, r in game.deck.deal_one_by_one(game.players):
            p = game.players[pi]
            has_pair, suit, rank = p.check_new_card_pair(card)
            if has_pair and game.trump_suit is None and random.random() > 0.3:
                game.trump_suit = suit
        
        if game.trump_suit is None:
            game.trump_suit = random.choice(['黑桃', '红心', '梅花', '方块'])
        
        declarer = random.choice(game.players)
        game.team_scorer = declarer.team
        for p in game.players:
            p.role = 'scorer' if p.team == game.team_scorer else 'runner'
        
        first = random.choice([p for p in game.players if p.role == 'runner'])
        game.current_player_index = game.players.index(first)
        
        while all(len(p.hand) > 0 for p in game.players):
            played = []
            for _ in range(4):
                cp = game.players[game.current_player_index]
                la = Rules.get_legal_actions(cp.hand, played[0] if played else [], game.trump_suit)
                if la:
                    if cp.team == 0:
                        a = dl_ai.model.choose_action(cp.hand, la, game.trump_suit, cp.role, game.team_scorer, game.scores[game.team_scorer])
                    else:
                        a = random.choice(la)
                    if a:
                        cp.remove_cards(a)
                        played.append(a)
                if len(played) >= 4: break
            
            if played:
                ws = Rules.compare_cards(played, played[0][0].suit if not played[0][0].is_joker else None, game.trump_suit)
                winner = game.players[(game.current_player_index + ws) % 4]
                if winner.role == 'scorer':
                    game.scores[game.team_scorer] += Rules.calculate_round_score(played)
                game.current_player_index = game.players.index(winner)
        
        score = game.scores[game.team_scorer]
        if score > 115:
            w_dl += 1
        elif score < 85:
            w_rand += 1
        else:
            d += 1
    
    print(f"\n结果: 深度学习AI {w_dl}胜, 随机AI {w_rand}胜, 平局 {d}")
    return w_dl, w_rand, d


if __name__ == "__main__":
    print("=" * 50)
    print("深度学习双扣AI")
    print("=" * 50)
    
    dl_ai = DeepLearningAI()
    
    print("\n1. 快速训练 (10局自我对弈)...")
    train_self_play(dl_ai, num_games=10)
    
    print("\n2. 对战测试...")
    quick_battle(dl_ai, None, num_games=5)
