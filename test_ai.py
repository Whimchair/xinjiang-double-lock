from game.game import Game
from ai.rule_based_ai import RuleBasedAI

def test_ai_vs_random(num_games=10):
    """测试规则AI vs 随机AI"""
    
    results = {
        'ai_team_wins': 0,
        'random_team_wins': 0,
        'draws': 0
    }
    
    for game_num in range(num_games):
        print(f"\n{'='*50}")
        print(f"第 {game_num + 1} 局游戏")
        print(f"{'='*50}")
        
        # 创建AI实例：玩家0和2使用规则AI（一队）
        ai_players = {
            0: RuleBasedAI(None),  # 玩家0
            2: RuleBasedAI(None)   # 玩家2
        }
        
        game = Game(ai_players=ai_players)
        game.start_game()
        
        # 统计结果
        score = game.scores[game.team_scorer]
        ai_team = 0  # AI队伍（玩家0和2）
        
        if game.team_scorer == ai_team:
            # AI队伍是得分组
            if score > 115:
                results['ai_team_wins'] += 1
            elif score < 85:
                results['random_team_wins'] += 1
            else:
                results['draws'] += 1
        else:
            # AI队伍是跑分组
            if score > 115:
                results['random_team_wins'] += 1
            elif score < 85:
                results['ai_team_wins'] += 1
            else:
                results['draws'] += 1
    
    # 显示统计结果
    print(f"\n{'='*50}")
    print("测试结果统计")
    print(f"{'='*50}")
    print(f"总对局数: {num_games}")
    print(f"规则AI队伍胜利: {results['ai_team_wins']} ({results['ai_team_wins']/num_games*100:.1f}%)")
    print(f"随机AI队伍胜利: {results['random_team_wins']} ({results['random_team_wins']/num_games*100:.1f}%)")
    print(f"平局: {results['draws']} ({results['draws']/num_games*100:.1f}%)")
    print(f"\n规则AI胜率: {results['ai_team_wins']/num_games*100:.1f}%")

if __name__ == "__main__":
    print("=== 规则AI vs 随机AI 测试 ===")
    print("规则AI队伍: 玩家1 和 玩家3")
    print("随机AI队伍: 玩家2 和 玩家4")
    
    test_ai_vs_random(num_games=20)