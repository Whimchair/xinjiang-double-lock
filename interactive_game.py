import random
from game.game import Game
from game.rules import Rules
from ai.rule_based_ai import RuleBasedAI
from ai.mcts_ai import ImprovedMCTSAI
from ai.game_state import GameState

class InteractiveGame:
    """交互式双扣游戏 - 真人参与"""
    
    def __init__(self):
        self.game = None
        self.human_player_index = 0  # 真人玩家索引
    
    def start(self):
        """启动交互式游戏"""
        print("=" * 60)
        print("          欢迎来到双扣游戏！")
        print("=" * 60)
        print("\n游戏说明：")
        print("- 你将扮演玩家1，与AI对战")
        print("- 玩家1和玩家3是一队，玩家2和玩家4是一队")
        print("- 输入牌的编号来选择要出的牌")
        print("- 输入'q'退出游戏")
        print("\nAI模式：")
        print("  [1] 规则AI（快速）")
        print("  [2] MCTS AI（更强，但较慢）")
        print("\n" + "=" * 60)
        
        ai_mode = input("\n选择AI模式 (1/2，默认1): ").strip()
        use_mcts = ai_mode == '2'
        
        input("\n按回车键开始游戏...")
        
        if use_mcts:
            ai_players = {
                1: ImprovedMCTSAI(None, time_limit=1.0),
                2: ImprovedMCTSAI(None, time_limit=1.0),
                3: ImprovedMCTSAI(None, time_limit=1.0)
            }
            print("\n使用MCTS AI（每步思考约1秒）")
        else:
            ai_players = {
                1: RuleBasedAI(None),
                2: RuleBasedAI(None),
                3: RuleBasedAI(None)
            }
            print("\n使用规则AI")
        
        self.game = Game(ai_players=ai_players)
        self._run_game()
    
    def _run_game(self):
        """运行游戏"""
        # 洗牌
        self.game.deck.shuffle()
        
        # 发牌并叫主（合并阶段）
        self._deal_and_declare()
        
        # 顶主对阶段
        if self.game.trump_suit:
            self._top_trump()
        
        # 打牌阶段
        self._play_cards()
        
        # 结算
        self._end_game()
    
    def _deal_and_declare(self):
        """发牌阶段（包含叫主判断）"""
        print("\n" + "=" * 60)
        print("【发牌阶段】")
        print("=" * 60)
        print("\n正在发牌...每发到对子可以选择叫主")
        
        declarer = None
        
        # 逐张发牌
        for player_idx, card, round_num in self.game.deck.deal_one_by_one(self.game.players):
            player = self.game.players[player_idx]
            
            # 检查是否形成对子
            has_pair, suit, rank = player.check_new_card_pair(card)
            
            if has_pair and self.game.trump_suit is None:
                if player_idx == self.human_player_index:
                    # 真人玩家选择是否叫主
                    print(f"\n第{round_num}轮发牌:")
                    print(f"你发到: {card}")
                    print(f"你有一对 {suit}{rank}！")
                    
                    choice = input("是否用这对牌叫主？(y/n): ").strip().lower()
                    if choice == 'y':
                        self.game.trump_suit = suit
                        declarer = player
                        print(f"\n你叫主，主花色: {suit}")
                else:
                    # AI玩家决策：70%概率叫主
                    if random.random() > 0.3:
                        self.game.trump_suit = suit
                        declarer = player
                        print(f"\n第{round_num}轮: {player.name} 叫主，主花色: {suit}")
        
        # 显示最终手牌
        print("\n" + "=" * 60)
        print("发牌完成！")
        print("=" * 60)
        for player in self.game.players:
            print(f"{player.name} 手牌: {len(player.hand)}张")
        
        # 如果没人叫主，随机选择
        if self.game.trump_suit is None:
            suits = ['黑桃', '红心', '梅花', '方块']
            self.game.trump_suit = random.choice(suits)
            print(f"\n无人叫主，随机选择主花色: {self.game.trump_suit}")
        
        input("\n按回车键继续...")
    
    def _top_trump(self):
        """顶主对阶段"""
        print("\n" + "=" * 60)
        print(f"【顶主对阶段】主花色: {self.game.trump_suit}")
        print("=" * 60)
        
        # 找出叫主的玩家
        declarer = None
        for player in self.game.players:
            if any(suit == self.game.trump_suit for (suit, rank) in player.get_pairs()):
                declarer = player
                break
        
        if not declarer:
            declarer = random.choice(self.game.players)
        
        declarer_team = declarer.team
        print(f"叫主方: {declarer.name} (队{declarer_team})")
        
        # 非叫主方玩家可以顶主对
        max_pair = None
        max_player = None
        
        for player in self.game.players:
            if player.team == declarer_team:
                continue
            
            # 检查是否有主花色的对子
            for (suit, rank) in player.get_pairs():
                if suit == self.game.trump_suit:
                    rank_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                    if max_pair is None or rank_order.index(rank) > rank_order.index(max_pair[1]):
                        max_pair = (suit, rank)
                        max_player = player
        
        if max_player:
            print(f"{max_player.name} 顶主对: {max_pair[0]}{max_pair[1]}")
            self.game.team_scorer = max_player.team
        else:
            self.game.team_scorer = declarer_team
        
        # 设置玩家角色
        for player in self.game.players:
            if player.team == self.game.team_scorer:
                player.role = 'scorer'
            else:
                player.role = 'runner'
        
        print(f"\n得分组: 队{self.game.team_scorer}")
        print(f"跑分组: 队{1 - self.game.team_scorer}")
        
        # 显示真人玩家的角色
        human_player = self.game.players[self.human_player_index]
        if human_player.role == 'scorer':
            print(f"\n你是得分组，目标是拿分（超过115分获胜）")
        else:
            print(f"\n你是跑分组，目标是阻止对方拿分（控制在85分以下）")
        
        input("\n按回车键开始打牌...")
    
    def _play_cards(self):
        """打牌阶段"""
        print("\n" + "=" * 60)
        print("【打牌阶段】")
        print("=" * 60)
        
        # 确定第一轮出牌者（跑分组）
        runner_players = [p for p in self.game.players if p.role == 'runner']
        first_player = random.choice(runner_players)
        self.game.current_player_index = self.game.players.index(first_player)
        
        print(f"第一轮出牌者: {first_player.name}")
        
        # 游戏循环
        while all(len(p.hand) > 0 for p in self.game.players):
            self._play_round()
            self.game.rounds_played += 1
    
    def _play_round(self):
        """玩一轮"""
        played_cards = []
        current_player = self.game.players[self.game.current_player_index]
        
        print("\n" + "-" * 60)
        print(f"第{self.game.rounds_played + 1}轮")
        print("-" * 60)
        
        print(f"当前得分 - 队{self.game.team_scorer}: {self.game.scores[self.game.team_scorer]}")
        
        legal_actions = Rules.get_legal_actions(current_player.hand, [], self.game.trump_suit)
        
        if self.game.current_player_index == self.human_player_index:
            action = self._human_choose_action(legal_actions, None)
        else:
            game_state = self._create_game_state()
            action = current_player.ai.choose_action(game_state, legal_actions)
            print(f"\n{current_player.name} 思考中...")
            print(f"{current_player.name} 出: {action}")
        
        current_player.remove_cards(action)
        played_cards.append(action)
        
        for i in range(1, 4):
            next_index = (self.game.current_player_index + i) % 4
            next_player = self.game.players[next_index]
            
            legal_actions = Rules.get_legal_actions(next_player.hand, action, self.game.trump_suit)
            
            if legal_actions:
                if next_index == self.human_player_index:
                    follow_action = self._human_choose_action(legal_actions, action)
                else:
                    game_state = self._create_game_state()
                    game_state.first_cards = action
                    follow_action = next_player.ai.choose_action(game_state, legal_actions)
                    print(f"{next_player.name} 思考中...")
                    print(f"{next_player.name} 出: {follow_action}")
                
                next_player.remove_cards(follow_action)
                played_cards.append(follow_action)
        
        first_suit = action[0].suit if not action[0].is_joker else None
        winner_index = Rules.compare_cards(played_cards, first_suit, self.game.trump_suit)
        winner = self.game.players[(self.game.current_player_index + winner_index) % 4]
        
        round_score = Rules.calculate_round_score(played_cards)
        if winner.role == 'scorer':
            self.game.scores[self.game.team_scorer] += round_score
            print(f"\n>>> {winner.name} 赢下本轮，得分: {round_score} <<<")
        else:
            print(f"\n>>> {winner.name} 赢下本轮，无得分 <<<")
        
        self.game.current_player_index = self.game.players.index(winner)
    
    def _create_game_state(self):
        """创建当前游戏状态"""
        return GameState.from_game(self.game)
    
    def _show_hand(self, player):
        """显示玩家手牌（从大到小排列，主牌单独显示）"""
        print(f"\n你的手牌 ({len(player.hand)}张):")
        
        rank_order = ['大王', '小王', 'A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
        trump_suit = self.game.trump_suit
        trump_ranks = ['5', '3', '2']
        
        trump_cards = {'Joker': [], '主花色': [], '常主': []}
        side_cards = {'黑桃': [], '红心': [], '梅花': [], '方块': []}
        
        for card in player.hand:
            if card.suit == 'Joker':
                trump_cards['Joker'].append(card.rank)
            elif card.suit == trump_suit:
                trump_cards['主花色'].append(card.rank)
            elif card.rank in trump_ranks:
                trump_cards['常主'].append((card.suit, card.rank))
            else:
                side_cards[card.suit].append(card.rank)
        
        print("  【主牌】")
        if trump_cards['Joker']:
            sorted_ranks = sorted(trump_cards['Joker'], key=lambda r: rank_order.index(r) if r in rank_order else 99)
            print(f"    Joker: {', '.join(sorted_ranks)}")
        if trump_cards['主花色']:
            sorted_ranks = sorted(trump_cards['主花色'], key=lambda r: rank_order.index(r) if r in rank_order else 99)
            print(f"    {trump_suit}: {', '.join(sorted_ranks)}")
        if trump_cards['常主']:
            sorted_cards = sorted(trump_cards['常主'], key=lambda x: (trump_ranks.index(x[1]), x[0]))
            cards_str = ', '.join([f"{s}{r}" for s, r in sorted_cards])
            print(f"    常主: {cards_str}")
        
        print("  【副牌】")
        for suit in ['黑桃', '红心', '梅花', '方块']:
            if suit == trump_suit:
                continue
            ranks = side_cards[suit]
            if ranks:
                sorted_ranks = sorted(ranks, key=lambda r: rank_order.index(r) if r in rank_order else 99)
                print(f"    {suit}: {', '.join(sorted_ranks)}")
    
    def _human_choose_action(self, legal_actions, first_cards):
        """真人玩家选择出牌"""
        human_player = self.game.players[self.human_player_index]
        
        print(f"\n轮到你出牌！")
        self._show_hand(human_player)
        
        if first_cards:
            print(f"\n首家出牌: {first_cards}")
        
        self._show_legal_actions(legal_actions)
        
        while True:
            choice = input(f"\n选择出牌 (1-{len(legal_actions)}): ").strip()
            
            if choice == 'q':
                print("退出游戏")
                exit(0)
            
            try:
                action_idx = int(choice) - 1
                if 0 <= action_idx < len(legal_actions):
                    return legal_actions[action_idx]
                else:
                    print("无效选择，请重新输入")
            except:
                print("无效输入，请输入数字")
    
    def _show_legal_actions(self, legal_actions):
        """显示可选的出牌（横向排列，优化对子显示）"""
        print(f"\n可选的出牌 ({len(legal_actions)}种)：")
        
        if len(legal_actions) <= 20:
            self._show_actions_simple(legal_actions)
        else:
            self._show_actions_grouped(legal_actions)
    
    def _show_actions_simple(self, legal_actions):
        """简单横向排列显示"""
        cols = 4
        for i in range(0, len(legal_actions), cols):
            row_actions = legal_actions[i:i+cols]
            row_str = "  ".join(f"[{i+j+1:2d}] {self._format_action(a)}" for j, a in enumerate(row_actions))
            print(f"  {row_str}")
    
    def _get_card_sort_key(self, card):
        """获取牌的排序键（主牌优先，从大到小）"""
        rank_order = {'大王': 0, '小王': 1, 'A': 2, 'K': 3, 'Q': 4, 'J': 5, '10': 6, 
                      '9': 7, '8': 8, '7': 9, '6': 10, '5': 11, '4': 12, '3': 13, '2': 14}
        trump_suit = self.game.trump_suit
        trump_ranks = ['5', '3', '2']
        
        is_trump = 0
        if card.suit == 'Joker':
            is_trump = 0
        elif card.suit == trump_suit:
            is_trump = 1
        elif card.rank in trump_ranks:
            is_trump = 2
        else:
            is_trump = 3
        
        rank_val = rank_order.get(card.rank, 99)
        return (is_trump, rank_val, card.suit)
    
    def _show_actions_grouped(self, legal_actions):
        """分组显示（用于选择较多的情况）"""
        singles = []
        pairs = []
        others = []
        
        for idx, action in enumerate(legal_actions):
            if len(action) == 1:
                singles.append((idx, action))
            elif len(action) == 2:
                pairs.append((idx, action))
            else:
                others.append((idx, action))
        
        singles.sort(key=lambda x: x[0])
        
        if singles:
            print(f"\n  【单牌】({len(singles)}种)：")
            cols = 6
            for i in range(0, len(singles), cols):
                row = singles[i:i+cols]
                row_str = "  ".join(f"[{idx+1:2d}] {self._format_action(a)}" for idx, a in row)
                print(f"    {row_str}")
        
        if pairs:
            print(f"\n  【对子】({len(pairs)}种)：")
            cols = 5
            for i in range(0, len(pairs), cols):
                row = pairs[i:i+cols]
                row_str = "  ".join(f"[{idx+1:2d}] {self._format_action(a)}" for idx, a in row)
                print(f"    {row_str}")
        
        if others:
            print(f"\n  【其他】({len(others)}种)：")
            cols = 4
            for i in range(0, len(others), cols):
                row = others[i:i+cols]
                row_str = "  ".join(f"[{idx+1:2d}] {self._format_action(a)}" for idx, a in row)
                print(f"    {row_str}")
    
    def _format_action(self, action):
        """格式化出牌显示"""
        if len(action) == 1:
            return str(action[0])
        elif len(action) == 2:
            return f"{action[0]}+{action[1]}"
        else:
            return str(action)
    
    def _end_game(self):
        """游戏结束"""
        print("\n" + "=" * 60)
        print("【游戏结束】")
        print("=" * 60)
        
        score = self.game.scores[self.game.team_scorer]
        print(f"\n得分组（队{self.game.team_scorer}）最终得分: {score}")
        
        human_player = self.game.players[self.human_player_index]
        
        if score > 115:
            if human_player.role == 'scorer':
                print("\n🎉 恭喜！你赢了！（得分组胜利）")
            else:
                print("\n😢 很遗憾，你输了。（得分组胜利）")
        elif score < 85:
            if human_player.role == 'runner':
                print("\n🎉 恭喜！你赢了！（跑分组胜利）")
            else:
                print("\n😢 很遗憾，你输了。（跑分组胜利）")
        else:
            print("\n🤝 平局！")
        
        print("\n感谢游玩！")

if __name__ == "__main__":
    game = InteractiveGame()
    game.start()