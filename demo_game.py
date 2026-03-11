"""
双扣游戏 - 自动演示模式
展示游戏流程，无需手动输入
"""
import random
from game.game import Game
from game.rules import Rules
from ai.rule_based_ai import RuleBasedAI

def demo_game():
    """自动演示一局游戏"""
    print("=" * 60)
    print("          双扣游戏演示模式")
    print("=" * 60)
    print("\n演示说明：")
    print("- 所有玩家都由AI控制")
    print("- 自动展示完整的游戏流程")
    print("- 观察AI的决策过程")
    print("\n" + "=" * 60)
    
    input("\n按回车键开始演示...")
    
    # 创建AI玩家
    ai_players = {
        0: RuleBasedAI(None),
        1: RuleBasedAI(None),
        2: RuleBasedAI(None),
        3: RuleBasedAI(None)
    }
    
    game = Game(ai_players=ai_players)
    
    # 洗牌
    game.deck.shuffle()
    
    # 发牌并叫主（合并阶段）
    print("\n" + "=" * 60)
    print("【发牌阶段】")
    print("=" * 60)
    
    # 逐张发牌并判断叫主
    for player_idx, card, round_num in game.deck.deal_one_by_one(game.players):
        player = game.players[player_idx]
        
        # 检查是否形成对子
        has_pair, suit, rank = player.check_new_card_pair(card)
        
        if has_pair and game.trump_suit is None:
            # AI决策：70%概率叫主
            if random.random() > 0.3:
                game.trump_suit = suit
                print(f"第{round_num}轮: {player.name} 叫主，主花色: {suit}")
    
    # 显示最终手牌
    print("\n发牌完成！")
    for player in game.players:
        print(f"  {player.name}: {len(player.hand)}张牌")
    
    # 如果没人叫主，随机选择
    if game.trump_suit is None:
        suits = ['黑桃', '红心', '梅花', '方块']
        game.trump_suit = random.choice(suits)
        print(f"\n无人叫主，随机选择主花色: {game.trump_suit}")
    
    # 顶主对阶段
    print("\n" + "=" * 60)
    print(f"【顶主对阶段】主花色: {game.trump_suit}")
    print("=" * 60)
    
    declarer = None
    for player in game.players:
        if any(suit == game.trump_suit for (suit, rank) in player.get_pairs()):
            declarer = player
            break
    
    if not declarer:
        declarer = random.choice(game.players)
    
    print(f"叫主方: {declarer.name} (队{declarer.team})")
    
    max_pair = None
    max_player = None
    
    for player in game.players:
        if player.team == declarer.team:
            continue
        
        for (suit, rank) in player.get_pairs():
            if suit == game.trump_suit:
                rank_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                if max_pair is None or rank_order.index(rank) > rank_order.index(max_pair[1]):
                    max_pair = (suit, rank)
                    max_player = player
    
    if max_player:
        print(f"{max_player.name} 顶主对: {max_pair[0]}{max_pair[1]}")
        game.team_scorer = max_player.team
    else:
        game.team_scorer = declarer.team
    
    for player in game.players:
        if player.team == game.team_scorer:
            player.role = 'scorer'
        else:
            player.role = 'runner'
    
    print(f"\n得分组: 队{game.team_scorer} ({game.players[game.team_scorer].name} 和 {game.players[game.team_scorer + 2].name})")
    print(f"跑分组: 队{1 - game.team_scorer}")
    
    input("\n按回车键开始打牌...")
    
    # 打牌阶段
    print("\n" + "=" * 60)
    print("【打牌阶段】")
    print("=" * 60)
    
    runner_players = [p for p in game.players if p.role == 'runner']
    first_player = random.choice(runner_players)
    game.current_player_index = game.players.index(first_player)
    
    print(f"第一轮出牌者: {first_player.name}")
    
    # 游戏循环
    while all(len(p.hand) > 0 for p in game.players):
        played_cards = []
        current_player = game.players[game.current_player_index]
        
        print(f"\n第{game.rounds_played + 1}轮")
        print("-" * 40)
        
        # 首家出牌
        legal_actions = Rules.get_legal_actions(current_player.hand, [], game.trump_suit)
        game_state = {'trump_suit': game.trump_suit, 'first_cards': []}
        action = current_player.ai.choose_action(game_state, legal_actions)
        current_player.remove_cards(action)
        played_cards.append(action)
        print(f"{current_player.name} 出: {action}")
        
        # 其他玩家跟牌
        for i in range(1, 4):
            next_index = (game.current_player_index + i) % 4
            next_player = game.players[next_index]
            
            legal_actions = Rules.get_legal_actions(next_player.hand, action, game.trump_suit)
            game_state = {'trump_suit': game.trump_suit, 'first_cards': action}
            follow_action = next_player.ai.choose_action(game_state, legal_actions)
            next_player.remove_cards(follow_action)
            played_cards.append(follow_action)
            print(f"{next_player.name} 出: {follow_action}")
        
        # 比较牌大小
        first_suit = action[0].suit if not action[0].is_joker else None
        winner_index = Rules.compare_cards(played_cards, first_suit, game.trump_suit)
        winner = game.players[(game.current_player_index + winner_index) % 4]
        
        # 计算得分
        round_score = Rules.calculate_round_score(played_cards)
        if winner.role == 'scorer':
            game.scores[game.team_scorer] += round_score
            print(f">>> {winner.name} 赢，得分: {round_score}，总分: {game.scores[game.team_scorer]} <<<")
        else:
            print(f">>> {winner.name} 赢，无得分 <<<")
        
        game.current_player_index = game.players.index(winner)
        game.rounds_played += 1
        
        # 每5轮暂停一次
        if game.rounds_played % 5 == 0:
            input("\n按回车键继续...")
    
    # 游戏结束
    print("\n" + "=" * 60)
    print("【游戏结束】")
    print("=" * 60)
    
    score = game.scores[game.team_scorer]
    print(f"\n得分组最终得分: {score}")
    
    if score > 115:
        print("得分组胜利！")
    elif score < 85:
        print("跑分组胜利！")
    else:
        print("平局！")
    
    print("\n演示结束！")

if __name__ == "__main__":
    demo_game()