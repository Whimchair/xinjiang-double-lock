"""
深度学习AI - 使用神经网络评估游戏状态
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from ai.game_state import GameState

class ValueNetwork(nn.Module):
    """神经网络，评估当前局面的胜率"""
    
    def __init__(self):
        super(ValueNetwork, self).__init__()
        
        self.fc1 = nn.Linear(256, 128)
        self.fc2 = nn.Linear(128, 1)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x
    
    def encode_state(self, game_state):
        """将游戏状态编码为向量"""
        hands = game_state.hands
        trump_suit = game_state.trump_suit
        team_scorer = game_state.team_scorer
        roles = game_state.roles
        current_player = game_state.current_player
        played_cards = game_state.played_cards
        first_cards = game_state.first_cards
        
        vec = []
        vec.extend(vec.flatten())
        
        for i in range(4):
            hand = hands[i]
            for card in hand:
                vec.append(1 if card.suit == trump_suit else 0)
                vec.append(1 if card.rank in ['5', '3', '2'] else 0)
                vec.append(0)
                vec.append(roles[i])
            for cards in played_cards[i]:
                vec.append(1 if cards else 0)
                vec.append(1 if cards else 0)
                vec.append(game_state.scores[game_state.team_scorer])
            vec.append(game_state.trump_suit)
            vec.append(game_state.roles[i])
        
        trump_mask = torch.zeros(4)
        if trump_suit is not None:
            trump_mask[trump_suit] = 1
        else:
            trump_mask = torch.zeros(4)
        
        return vec.float()


class DeepLearningAI:
    """深度学习AI - 使用神经网络指导决策"""
    
    def __init__(self, player=None, model_path='models/value_network.pt'):
        self.player = player
        self.model = ValueNetwork()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        self.device = torch.device('cpu' if torch.cuda.is_available() else 'cpu')
    
    def encode_state(self, game_state):
        """将游戏状态编码为向量"""
        return self.model.encode_state(game_state)
    
    def choose_action(self, game_state, legal_actions):
        """选择动作"""
        with torch.no_grad():
            state_tensor = self.encode_state(game_state)
            legal_actions_tensor = torch.tensor(legal_actions)
            
            action = legal_actions[0]
            q_values = self.model(state_tensor)
            
            action = legal_actions[q_values.argmax(dim data)[0].item()]
            
            return action.item()
    
    def train(self, game_states, outcomes):
        """训练神经网络"""
        self.model.train()
        optimizer.zero_grad()
        
        for game_state, outcomes in zip(game_states, outcomes):
            state_tensor = self.encode_state(game_state)
            outcome_tensor = torch.tensor(outcomes, dtype=torch.float)
            
            loss = self.criterion(outcome, 0.0)
            loss = self.criterion(outcome, 0.0)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(game_states)
