"""
深度学习AI训练 - CPU版本
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from game.game import Game
from game.rules import Rules
from game.card import Card

class CardEncoder:
    """牌编码器"""
    
    @staticmethod
    def encode_hand(hand, trump_suit):
        """编码手牌 (27 * 4 = 108维)"""
        vec = [0] * 108
        
        rank_order = {'2':0,'3':1,'4':2,'5':3,'6':4,'7':5,'8':6,'9':7,'10':8,'J':9,'Q':10,'K':11,'A':12,'小王':13,'大王':14}
        
        for i, card in enumerate(hand[:27]):
            if i >= 27:
                break
            
            suit_val = 0
            if card.suit == '黑桃': suit_val = 1
            elif card.suit == '红心': suit_val = 2
            elif card.suit == '梅花': suit_val = 3
            elif card.suit == '方块': suit_val = 4
            elif card.suit == 'Joker': suit_val = 5
            
            rank_val = rank_order.get(card.rank, 0)
            
            if card.suit == trump_suit:
                suit_val += 10
            
            vec[i] = suit_val * 15 + rank_val
        
        return vec
    
    @staticmethod
    def encode_state(hand, trump_suit, role, score):
        """编码状态 (120维)"""
        vec = CardEncoder.encode_hand(hand, trump_suit)
        vec.append(1 if role == 'scorer' else 0)
        vec.append(score / 200.0)
        vec.append(len(hand) / 27.0)
        
        while len(vec) < 120:
            vec.append(0)
        
        return vec


class DLAI(nn.Module):
    """深度学习AI网络"""
    
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(120, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
    def evaluate(self, hand, trump_suit, role, score):
        vec = CardEncoder.encode_state(hand, trump_suit, role, score)
        tensor = torch.FloatTensor([vec])
        with torch.no_grad():
            return self(tensor).item()
    
    def choose_action(self, hand, actions, trump_suit, role, score):
        if not actions:
            return None
        if len(actions) == 1:
            return actions[0]
        
        best = None
        best_val = float('-inf')
        
        for action in actions:
            new_hand = hand.copy()
            for card in action:
                for i, c in enumerate(new_hand):
                    if c.suit == card.suit and c.rank == card.rank:
                        new_hand.pop(i)
                        break
            
            val = self.evaluate(new_hand, trump_suit, role, score)
            if val > best_val:
                best_val = val
                best = action
        
        return best if best else random.choice(actions)


def play_one_game(model, epsilon=0.3):
    """自我对弈一局，返回训练数据"""
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
    
    training_data = []
    
    while all(len(p.hand) > 0 for p in game.players):
        played = []
        
        for _ in range(4):
            cp = game.players[game.current_player_index]
            la = Rules.get_legal_actions(cp.hand, played[0] if played else [], game.trump_suit)
            
            if la:
                if random.random() > epsilon:
                    action = model.choose_action(cp.hand, la, game.trump_suit, cp.role, game.scores[game.team_scorer])
                else:
                    action = random.choice(la)
                
                training_data.append({
                    'hand': cp.hand.copy(),
                    'trump_suit': game.trump_suit,
                    'role': cp.role,
                    'score': game.scores[game.team_scorer],
                    'action': action
                })
                
                if action:
                    cp.remove_cards(action)
                    played.append(action)
            
            if len(played) >= 4:
                break
        
        if played:
            ws = Rules.compare_cards(played, played[0][0].suit if not played[0][0].is_joker else None, game.trump_suit)
            winner = game.players[(game.current_player_index + ws) % 4]
            if winner.role == 'scorer':
                game.scores[game.team_scorer] += Rules.calculate_round_score(played)
            game.current_player_index = game.players.index(winner)
    
    final_score = game.scores[game.team_scorer]
    if final_score > 115:
        result = 1.0
    elif final_score < 85:
        result = -1.0
    else:
        result = 0.0
    
    return training_data, result


def train(model, data, epochs=5, lr=0.01):
    """训练模型"""
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    model.train()
    total_loss = 0
    
    for _ in range(epochs):
        for sample in data:
            hand = sample['hand']
            trump_suit = sample['trump_suit']
            role = sample['role']
            score = sample['score']
            action = sample['action']
            
            new_hand = hand.copy()
            for card in action:
                for i, c in enumerate(new_hand):
                    if c.suit == card.suit and c.rank == card.rank:
                        new_hand.pop(i)
                        break
            
            vec = CardEncoder.encode_state(new_hand, trump_suit, role, score)
            x = torch.FloatTensor([vec])
            y = torch.FloatTensor([random.choice([-1, 0, 1])])
            
            optimizer.zero_grad()
            output = model(x)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
    
    return total_loss / (len(data) * epochs)


def main():
    print("=" * 50)
    print("深度学习AI训练 - CPU版本")
    print("=" * 50)
    
    model = DLAI()
    print(f"模型参数量: {sum(p.numel() for p in model.parameters())}")
    
    num_games = 50
    print(f"\n自我对弈收集数据 ({num_games}局)...")
    
    all_data = []
    for i in range(num_games):
        data, result = play_one_game(model, epsilon=0.5)
        all_data.extend(data)
        
        if (i + 1) % 10 == 0:
            print(f"  完成 {i+1}/{num_games} 局, 收集 {len(all_data)} 个样本")
    
    print(f"\n共收集 {len(all_data)} 个训练样本")
    
    print("\n开始训练 (5轮)...")
    loss = train(model, all_data, epochs=5)
    print(f"平均损失: {loss:.4f}")
    
    torch.save(model.state_dict(), 'models/dl_ai.pt')
    print("\n模型已保存到 models/dl_ai.pt")
    
    print("\n" + "=" * 50)
    print("训练完成!")
    print("=" * 50)


if __name__ == "__main__":
    import os
    os.makedirs('models', exist_ok=True)
    main()
