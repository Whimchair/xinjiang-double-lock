"""
深度学习AI训练 - 简化版
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from game.game import Game
from game.rules import Rules
import os

os.makedirs('models', exist_ok=True)

class CardEncoder:
    @staticmethod
    def encode(hand, trump_suit, role, score):
        vec = []
        
        rank_map = {'2':0,'3':1,'4':2,'5':3,'6':4,'7':5,'8':6,'9':7,'10':8,'J':9,'Q':10,'K':11,'A':12,'小王':13,'大王':14}
        suit_map = {'黑桃':0,'红心':1,'梅花':2,'方块':3,'Joker':4}
        
        for card in hand[:15]:
            s = suit_map.get(card.suit, 4)
            r = rank_map.get(card.rank, 0)
            if card.suit == trump_suit:
                s += 10
            vec.append(s * 15 + r)
        
        while len(vec) < 15:
            vec.append(0)
        
        vec.append(1 if role == 'scorer' else 0)
        vec.append(score / 200.0)
        
        return vec


class DLAI(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(17, 32)
        self.fc2 = nn.Linear(32, 1)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        return self.fc2(x)


def play_game_train(model):
    """玩一局，返回 (状态, 结果) 列表"""
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
    
    data = []
    
    while all(len(p.hand) > 0 for p in game.players):
        played = []
        for _ in range(4):
            cp = game.players[game.current_player_index]
            la = Rules.get_legal_actions(cp.hand, played[0] if played else [], game.trump_suit)
            
            if la:
                action = random.choice(la)
                
                data.append(CardEncoder.encode(cp.hand, game.trump_suit, cp.role, game.scores[game.team_scorer]))
                
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
    
    score = game.scores[game.team_scorer]
    if score > 115:
        result = 1.0
    elif score < 85:
        result = -1.0
    else:
        result = 0.0
    
    return data, result


def main():
    print("=" * 50)
    print("深度学习AI训练")
    print("=" * 50)
    
    model = DLAI()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    print(f"参数量: {sum(p.numel() for p in model.parameters())}")
    
    # 收集数据
    print("\n收集自我对弈数据 (20局)...")
    all_states = []
    all_results = []
    
    for i in range(20):
        states, result = play_game_train(model)
        all_states.extend(states)
        all_results.extend([result] * len(states))
        
        if (i+1) % 5 == 0:
            print(f"  {i+1}/20 局, {len(all_states)} 样本")
    
    print(f"共 {len(all_states)} 样本")
    
    # 训练
    print("\n训练 (10轮)...")
    X = torch.FloatTensor(all_states)
    Y = torch.FloatTensor(all_results).unsqueeze(1)
    
    model.train()
    for epoch in range(10):
        optimizer.zero_grad()
        pred = model(X)
        loss = criterion(pred, Y)
        loss.backward()
        optimizer.step()
        print(f"  轮{epoch+1}: loss={loss.item():.4f}")
    
    # 保存
    torch.save(model.state_dict(), 'models/dl_ai.pt')
    print("\n模型已保存!")


if __name__ == "__main__":
    main()
