#!/usr/bin/env python3
"""
深度学习双扣AI - GPU训练版本
用法: python train_gpu.py --games 1000 --epochs 50 --batch 64
"""
import os
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import random
import numpy as np
from game.game import Game
from game.rules import Rules

os.makedirs('models', exist_ok=True)

class CardEncoder:
    """牌编码器 - 将游戏状态编码为向量"""
    
    @staticmethod
    def encode(hand, trump_suit, role, score, remaining_cards):
        """编码状态 (35维)"""
        vec = []
        
        rank_map = {'2':0,'3':1,'4':2,'5':3,'6':4,'7':5,'8':6,'9':7,'10':8,'J':9,'Q':10,'K':11,'A':12,'小王':13,'大王':14}
        suit_map = {'黑桃':0,'红心':1,'梅花':2,'方块':3,'Joker':4}
        
        # 编码手牌 (前15张)
        for card in hand[:15]:
            s = suit_map.get(card.suit, 4)
            r = rank_map.get(card.rank, 0)
            if card.suit == trump_suit:
                s += 10
            vec.append(s * 15 + r)
        
        while len(vec) < 15:
            vec.append(0)
        
        # 编码剩余手牌数
        vec.append(remaining_cards / 27.0)
        
        # 编码角色 (0=跑分, 1=得分)
        vec.append(1.0 if role == 'scorer' else 0.0)
        
        # 编码当前得分
        vec.append(score / 200.0)
        
        # 编码主花色
        suit_vals = {'黑桃':0,'红心':1,'梅花':2,'方块':3}
        vec.append(suit_vals.get(trump_suit, -1) / 3.0)
        
        return vec


class DLAI(nn.Module):
    """深度学习网络"""
    
    def __init__(self, input_dim=35, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 64)
        self.fc4 = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        return self.fc4(x)


class GameDataset(Dataset):
    """游戏数据集"""
    
    def __init__(self, data):
        self.data = data
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


def play_selfplay_game(model, epsilon=0.3):
    """自我对弈一局，返回训练数据"""
    game = Game({})
    game.deck.shuffle()
    
    # 发牌
    for pi, card, _ in game.deck.deal_one_by_one(game.players):
        p = game.players[pi]
        has_pair, suit, rank = p.check_new_card_pair(card)
        if has_pair and game.trump_suit is None and random.random() > 0.3:
            game.trump_suit = suit
    
    if game.trump_suit is None:
        game.trump_suit = random.choice(['黑桃', '红心', '梅花', '方块'])
    
    # 确定庄家
    declarer = random.choice(game.players)
    game.team_scorer = declarer.team
    for p in game.players:
        p.role = 'scorer' if p.team == game.team_scorer else 'runner'
    
    # 首家
    first = random.choice([p for p in game.players if p.role == 'runner'])
    game.current_player_index = game.players.index(first)
    
    # 收集训练数据: (state, action_result)
    # action_result: 出牌后的状态价值 (+1赢/-1输/0平)
    training_data = []
    
    while all(len(p.hand) > 0 for p in game.players):
        played = []
        
        for _ in range(4):
            cp = game.players[game.current_player_index]
            la = Rules.get_legal_actions(cp.hand, played[0] if played else [], game.trump_suit)
            
            if la:
                # epsilon-greedy 探索
                if random.random() < epsilon:
                    action = random.choice(la)
                else:
                    action = choose_best_action(model, cp.hand, la, game.trump_suit, 
                                              cp.role, game.scores[game.team_scorer])
                
                # 记录状态
                state = CardEncoder.encode(cp.hand, game.trump_suit, cp.role, 
                                         game.scores[game.team_scorer], len(cp.hand))
                training_data.append(state)
                
                cp.remove_cards(action)
                played.append(action)
            
            if len(played) >= 4:
                break
        
        # 结算
        if played:
            ws = Rules.compare_cards(played, 
                                   played[0][0].suit if not played[0][0].is_joker else None, 
                                   game.trump_suit)
            winner = game.players[(game.current_player_index + ws) % 4]
            if winner.role == 'scorer':
                game.scores[game.team_scorer] += Rules.calculate_round_score(played)
            game.current_player_index = game.players.index(winner)
    
    # 最终结果
    final_score = game.scores[game.team_scorer]
    if final_score > 115:
        result = 1.0  # 大胜
    elif final_score < 85:
        result = -1.0  # 大败
    else:
        result = 0.0  # 平局
    
    # 为每个状态添加结果标签
    labeled_data = [(state, result) for state in training_data]
    return labeled_data


def choose_best_action(model, hand, actions, trump_suit, role, score):
    """选择最佳动作"""
    if len(actions) == 1:
        return actions[0]
    
    best_action = None
    best_value = float('-inf')
    
    for action in actions:
        # 模拟出牌后的手牌
        new_hand = hand.copy()
        for card in action:
            for i, c in enumerate(new_hand):
                if c.suit == card.suit and c.rank == card.rank:
                    new_hand.pop(i)
                    break
        
        # 编码状态
        state = CardEncoder.encode(new_hand, trump_suit, role, score, len(new_hand))
        tensor = torch.FloatTensor([state])
        
        with torch.no_grad():
            value = model(tensor).item()
        
        if value > best_value:
            best_value = value
            best_action = action
    
    return best_action if best_action else random.choice(actions)


def collect_data(model, num_games, epsilon):
    """收集自我对弈数据"""
    print(f"收集数据中 ({num_games}局)...")
    all_data = []
    
    for i in range(num_games):
        data = play_selfplay_game(model, epsilon)
        all_data.extend(data)
        
        if (i + 1) % 100 == 0:
            print(f"  完成 {i+1}/{num_games} 局, {len(all_data)} 样本")
    
    return all_data


def train_model(model, data, epochs, batch_size, lr):
    """训练模型"""
    print(f"\n训练模型 ({epochs}轮, batch={batch_size})...")
    
    dataset = GameDataset(data)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        num_batches = 0
        
        for states, results in dataloader:
            states = states
            results = results.unsqueeze(1)
            
            optimizer.zero_grad()
            outputs = model(states)
            loss = criterion(outputs, results)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        print(f"  轮{epoch+1}/{epochs}: loss={avg_loss:.4f}")
    
    return model


def main():
    parser = argparse.ArgumentParser(description='双扣AI GPU训练')
    parser.add_argument('--games', type=int, default=1000, help='自我对弈局数')
    parser.add_argument('--epochs', type=int, default=30, help='训练轮数')
    parser.add_argument('--batch', type=int, default=64, help='批次大小')
    parser.add_argument('--lr', type=float, default=0.001, help='学习率')
    parser.add_argument('--model', type=str, default='models/dl_ai.pt', help='模型保存路径')
    parser.add_argument('--load', type=str, default=None, help='加载已有模型')
    args = parser.parse_args()
    
    print("=" * 50)
    print("双扣AI GPU训练")
    print("=" * 50)
    print(f"设备: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
    print(f"参数: games={args.games}, epochs={args.epochs}, batch={args.batch}")
    print()
    
    # 设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 模型
    model = DLAI().to(device)
    
    if args.load:
        try:
            model.load_state_dict(torch.load(args.load, map_location=device))
            print(f"加载模型: {args.load}")
        except:
            print("使用随机初始化模型")
    
    print(f"参数量: {sum(p.numel() for p in model.parameters())}")
    
    # 第一阶段: 收集数据 (epsilon=0.5 探索)
    data = collect_data(model, args.games, epsilon=0.5)
    print(f"共收集 {len(data)} 样本")
    
    # 分离状态和标签
    states, results = zip(*data)
    states = torch.FloatTensor(states).to(device)
    results = torch.FloatTensor(results).to(device)
    
    # 第二阶段: 训练
    dataset = torch.utils.data.TensorDataset(states, results)
    dataloader = DataLoader(dataset, batch_size=args.batch, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(args.epochs):
        total_loss = 0
        num_batches = 0
        
        for batch_states, batch_results in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_states)
            loss = criterion(outputs, batch_results.unsqueeze(1))
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        print(f"训练 轮{epoch+1}/{args.epochs}: loss={total_loss/num_batches:.4f}")
    
    # 保存
    torch.save(model.state_dict(), args.model)
    print(f"\n模型已保存: {args.model}")
    print("=" * 50)


if __name__ == "__main__":
    main()
