# 方案一：MCTS + 信息集抽象（推荐首选）
class ShuangKouAI:
    """
    核心组件：
    1. 信息集抽象：将相似手牌状态聚类
    2. MCTS：处理决策树搜索
    3. 评估函数：结合领域知识
    """
    
    def __init__(self):
        # 信息集处理
        self.infoset_manager = InfoSetAbstractor()
        
        # MCTS搜索
        self.mcts = MCTS(
            iteration_limit=1000,
            exploration_constant=1.4
        )
        
        # 启发式评估
        self.heuristic = HeuristicEvaluator()

# 方案二：深度强化学习（进阶方案）
class RLShuangKouAI:
    """
    使用Deep CFR或NFSP处理不完全信息
    - 优势：自动发现策略
    - 劣势：训练成本高
    """
class SimpleShuangKouAI:
    """简化版：规则引擎 + 贪心策略"""
    
    def choose_action(self, legal_actions):
        """
        简单启发式：
        1. 能拿分时优先拿分（得分组）
        2. 优先出小牌保留大牌
        3. 主牌用于关键轮次
        """
        for action in legal_actions:
            if self.can_win_round(action):
                return action
        
        return self.play_smallest_card(legal_actions)