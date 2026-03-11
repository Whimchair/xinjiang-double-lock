"""简化版MCTS AI - 更快更稳定"""
import math
import random
import time

class SimpleMCTSNode:
    """简化MCTS节点"""
    
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = {}
        self.visit_count = 0
        self.total_reward = 0.0
    
    def is_fully_expanded(self):
        return len(self.children) >= len(self.state.get_legal_actions())
    
    def best_child(self, exploration_weight=1.4):
        best_score = -float('inf')
        best_action = None
        
        for action, child in self.children.items():
            if child.visit_count == 0:
                return action, child
            
            exploitation = child.total_reward / child.visit_count
            exploration = exploration_weight * math.sqrt(
                math.log(self.visit_count) / child.visit_count
            )
            score = exploitation + exploration
            
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action, self.children[best_action]
    
    def update(self, reward):
        self.visit_count += 1
        self.total_reward += reward


class SimpleMCTS:
    """简化版MCTS"""
    
    def __init__(self, iterations=50, time_limit=0.5, exploration_weight=1.4):
        self.iterations = iterations
        self.time_limit = time_limit
        self.exploration_weight = exploration_weight
    
    def search(self, state):
        """执行MCTS搜索"""
        root = SimpleMCTSNode(state.clone())
        
        if self.time_limit:
            start_time = time.time()
            while time.time() - start_time < self.time_limit:
                self._iterate(root)
        else:
            for _ in range(self.iterations):
                self._iterate(root)
        
        return self._best_action(root)
    
    def _iterate(self, root):
        node = self._select(root)
        
        if not node.state.is_terminal():
            node = self._expand(node)
        
        reward = self._simulate(node)
        self._backpropagate(node, reward)
    
    def _select(self, node):
        while not node.state.is_terminal() and node.is_fully_expanded():
            action, child = node.best_child(self.exploration_weight)
            if child is None:
                break
            node = child
        return node
    
    def _expand(self, node):
        legal_actions = node.state.get_legal_actions()
        tried_actions = set(tuple(a) for a in node.children.keys())
        untried = [a for a in legal_actions if tuple(a) not in tried_actions]
        
        if not untried:
            return node
        
        action = random.choice(untried)
        new_state = node.state.clone()
        new_state.apply_action(action)
        
        action_key = tuple(action)
        child = SimpleMCTSNode(new_state, parent=node, action=action)
        node.children[action_key] = child
        return child
    
    def _simulate(self, node):
        state = node.state.clone()
        current_player = state.current_player
        
        while not state.is_terminal():
            legal_actions = state.get_legal_actions()
            if not legal_actions:
                break
            action = random.choice(legal_actions)
            state.apply_action(action)
        
        return state.get_result(current_player)
    
    def _backpropagate(self, node, reward):
        current = node
        flip = False
        while current is not None:
            if flip:
                current.update(-reward)
            else:
                current.update(reward)
            flip = not flip
            current = current.parent
    
    def _best_action(self, root):
        if not root.children:
            return root.state.get_legal_actions()[0]
        
        best_child = max(root.children.values(), key=lambda c: c.visit_count)
        return best_child.action


class ImprovedMCTSAI:
    """改进的MCTS AI"""
    
    def __init__(self, player=None, iterations=30, time_limit=0.3):
        self.player = player
        self.mcts = SimpleMCTS(iterations=iterations, time_limit=time_limit)
    
    def choose_action(self, game_state, legal_actions):
        if not legal_actions:
            return None
        
        if len(legal_actions) == 1:
            return legal_actions[0]
        
        state = game_state.get('state') if isinstance(game_state, dict) else game_state
        
        if state is None:
            return random.choice(legal_actions)
        
        action = self.mcts.search(state)
        
        if action is None:
            return random.choice(legal_actions)
        
        for la in legal_actions:
            if self._actions_equal(action, la):
                return la
        
        return random.choice(legal_actions)
    
    def _actions_equal(self, action1, action2):
        if len(action1) != len(action2):
            return False
        for c1 in action1:
            found = False
            for c2 in action2:
                if c1.suit == c2.suit and c1.rank == c2.rank:
                    found = True
                    break
            if not found:
                return False
        return True
