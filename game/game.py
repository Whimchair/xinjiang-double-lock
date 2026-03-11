import random
from game.deck import Deck
from game.player import Player
from game.rules import Rules
from game.card import Card

class Game:
    def __init__(self, ai_players=None):
        """
        ai_players: 字典，{玩家索引: AI实例}
        例如：{0: RuleBasedAI(), 2: RuleBasedAI()} 表示玩家0和2使用规则AI
        """
        self.players = [Player(f"玩家{i+1}") for i in range(4)]
        # 分组：0和2一队，1和3一队
        self.players[0].team = 0
        self.players[1].team = 1
        self.players[2].team = 0
        self.players[3].team = 1
        
        # 设置AI
        self.ai_players = ai_players or {}
        for idx, ai in self.ai_players.items():
            self.players[idx].ai = ai
            ai.player = self.players[idx]
        
        self.deck = Deck()
        self.trump_suit = None
        self.scores = [0, 0]  # 两队得分
        self.team_scorer = None  # 得分组
        self.current_player_index = 0
        self.rounds_played = 0
        self.game_phase = 'deal'  # deal, declare, top, play, end
    
    def start_game(self):
        """开始游戏"""
        print("=== 双扣游戏开始 ===")
        
        # 洗牌
        self.deck.shuffle()
        
        # 发牌并叫主（合并阶段）
        self._deal_and_declare()
        
        # 顶主对阶段
        if self.trump_suit:
            self._top_trump()
        
        # 打牌阶段
        self._play_cards()
        
        # 结算
        self._end_game()
    
    def _deal_and_declare(self):
        """发牌阶段（包含叫主判断）"""
        print("\n=== 发牌阶段 ===")
        
        declarer = None
        declarer_pair = None
        
        # 逐张发牌
        for player_idx, card, round_num in self.deck.deal_one_by_one(self.players):
            player = self.players[player_idx]
            
            # 检查是否形成对子
            has_pair, suit, rank = player.check_new_card_pair(card)
            
            if has_pair and self.trump_suit is None:
                # 有对子且还没人叫主，可以选择叫主
                if player.ai:
                    # AI决策：70%概率叫主
                    if random.random() > 0.3:
                        self.trump_suit = suit
                        declarer = player
                        declarer_pair = (suit, rank)
                        print(f"第{round_num}轮: {player.name} 叫主，主花色: {suit}")
                else:
                    # 真人玩家（在交互式游戏中处理）
                    # 这里默认不叫，由交互式游戏处理
                    pass
        
        # 显示最终手牌
        print("\n发牌完成！")
        for player in self.players:
            print(f"{player.name} 手牌: {len(player.hand)}张")
        
        # 如果没人叫主，随机选择
        if self.trump_suit is None:
            suits = ['黑桃', '红心', '梅花', '方块']
            self.trump_suit = random.choice(suits)
            print(f"\n无人叫主，随机选择主花色: {self.trump_suit}")
        
        return declarer
    
    def _declare_trump(self):
        """叫主阶段"""
        print("\n=== 叫主阶段 ===")
        declared = False
        
        # 按顺序检查每个玩家是否有对子
        for i, player in enumerate(self.players):
            if player.has_pair():
                # 模拟玩家选择是否叫主（这里简化为随机）
                if random.random() > 0.3:  # 70%概率叫主
                    pairs = player.get_pairs()
                    # 选择第一个对子作为主牌
                    suit, rank = pairs[0]
                    self.trump_suit = suit
                    print(f"{player.name} 叫主，主花色: {suit}")
                    declared = True
                    break
        
        if not declared:
            # 随机选择一个花色作为主牌
            suits = ['黑桃', '红心', '梅花', '方块']
            self.trump_suit = random.choice(suits)
            print(f"无人叫主，随机选择主花色: {self.trump_suit}")
    
    def _top_trump(self):
        """顶主对阶段"""
        print(f"\n=== 顶主对阶段 (主花色: {self.trump_suit}) ===")
        
        # 找出叫主的玩家
        declarer = None
        for player in self.players:
            if any(suit == self.trump_suit for (suit, rank) in player.get_pairs()):
                declarer = player
                break
        
        if not declarer:
            declarer = random.choice(self.players)
        
        declarer_team = declarer.team
        print(f"叫主方: {declarer.name} (队{declarer_team})")
        
        # 非叫主方玩家可以顶主对
        max_pair = None
        max_player = None
        
        for player in self.players:
            if player.team == declarer_team:
                continue
            
            # 检查是否有主花色的对子
            for (suit, rank) in player.get_pairs():
                if suit == self.trump_suit:
                    # 比较对子大小（K最大，A最小）
                    rank_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                    if max_pair is None or rank_order.index(rank) > rank_order.index(max_pair[1]):
                        max_pair = (suit, rank)
                        max_player = player
        
        if max_player:
            print(f"{max_player.name} 顶主对: {max_pair[0]}{max_pair[1]}")
            # 顶主对获胜，成为得分组
            self.team_scorer = max_player.team
        else:
            # 无人顶主对，叫主方成为得分组
            self.team_scorer = declarer_team
        
        # 设置玩家角色
        for player in self.players:
            if player.team == self.team_scorer:
                player.role = 'scorer'
            else:
                player.role = 'runner'
        
        print(f"得分组: 队{self.team_scorer}")
        print(f"跑分组: 队{1 - self.team_scorer}")
    
    def _play_cards(self):
        """打牌阶段"""
        print("\n=== 打牌阶段 ===")
        
        # 确定第一轮出牌者（跑分组）
        runner_players = [p for p in self.players if p.role == 'runner']
        first_player = random.choice(runner_players)
        self.current_player_index = self.players.index(first_player)
        
        print(f"第一轮出牌者: {first_player.name}")
        
        # 游戏循环
        while all(len(p.hand) > 0 for p in self.players):
            self._play_round()
            self.rounds_played += 1
    
    def _play_round(self):
        """玩一轮"""
        played_cards = []
        current_player = self.players[self.current_player_index]
        
        print(f"\n第{self.rounds_played + 1}轮，{current_player.name} 出牌")
        
        # 首家出牌
        legal_actions = Rules.get_legal_actions(current_player.hand, [], self.trump_suit)
        
        # 使用AI决策或随机选择
        if current_player.ai:
            game_state = {
                'trump_suit': self.trump_suit,
                'first_cards': []
            }
            action = current_player.ai.choose_action(game_state, legal_actions)
        else:
            action = random.choice(legal_actions)
        
        current_player.remove_cards(action)
        played_cards.append(action)
        print(f"{current_player.name} 出: {action}")
        
        # 其他玩家跟牌
        for i in range(1, 4):
            next_index = (self.current_player_index + i) % 4
            next_player = self.players[next_index]
            
            legal_actions = Rules.get_legal_actions(next_player.hand, action, self.trump_suit)
            
            if legal_actions:
                # 使用AI决策或随机选择
                if next_player.ai:
                    game_state = {
                        'trump_suit': self.trump_suit,
                        'first_cards': action
                    }
                    follow_action = next_player.ai.choose_action(game_state, legal_actions)
                else:
                    follow_action = random.choice(legal_actions)
                
                next_player.remove_cards(follow_action)
                played_cards.append(follow_action)
                print(f"{next_player.name} 出: {follow_action}")
            else:
                print(f"{next_player.name} 无牌可出")
        
        # 比较牌大小
        first_suit = action[0].suit if not action[0].is_joker else None
        winner_index = Rules.compare_cards(played_cards, first_suit, self.trump_suit)
        winner = self.players[(self.current_player_index + winner_index) % 4]
        
        # 计算得分
        round_score = Rules.calculate_round_score(played_cards)
        if winner.role == 'scorer':
            self.scores[self.team_scorer] += round_score
            print(f"{winner.name} 赢下本轮，得分: {round_score}")
        else:
            print(f"{winner.name} 赢下本轮，无得分")
        
        # 下一轮由赢家先出
        self.current_player_index = self.players.index(winner)
        
        # 显示当前得分
        print(f"当前得分 - 队{self.team_scorer}: {self.scores[self.team_scorer]}, 队{1 - self.team_scorer}: {self.scores[1 - self.team_scorer]}")
    
    def _end_game(self):
        """游戏结束，判定胜负"""
        print("\n=== 游戏结束 ===")
        score = self.scores[self.team_scorer]
        
        print(f"得分组（队{self.team_scorer}）最终得分: {score}")
        
        if score > 115:
            print("得分组胜利！")
        elif score < 85:
            print("跑分组胜利！")
        else:
            print("平局！")
        
        # 显示所有玩家剩余手牌
        for player in self.players:
            print(f"{player.name} 剩余手牌: {player.hand}")

if __name__ == "__main__":
    game = Game()
    game.start_game()