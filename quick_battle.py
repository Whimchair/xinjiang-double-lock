"""快速AI对战测试 - 规则AI vs 规则AI"""
import random
import time
from game.game import Game
from game.rules import Rules
from ai.rule_based_ai import RuleBasedAI
from ai.game_state import GameState

def play_game_fast(ai_config):
    """快速进行一局游戏"""
    game = Game(ai_players=ai_config)
    game.deck.shuffle()
    
    for player_idx, card, round_num in game.deck.deal_one_by_one(game.players):
        player = game.players[player_idx]
        has_pair, suit, rank = player.check_new_card_pair(card)
        if has_pair and game.trump_suit is None:
            if random.random() > 0.3:
                game.trump_suit = suit
    
    if game.trump_suit is None:
        game.trump_suit = random.choice(['黑桃', '红心', '梅花', '方块'])
    
    declarer = random.choice(game.players)
    game.team_scorer = declarer.team
    for player in game.players:
        if player.team == game.team_scorer:
            player.role = 'scorer'
        else:
            player.role = 'runner'
    
    runner_players = [p for p in game.players if p.role == 'runner']
    first_player = random.choice(runner_players)
    game.current_player_index = game.players.index(first_player)
    
    rounds = 0
    while all(len(p.hand) > 0 for p in game.players):
        rounds += 1
        played_cards = []
        current_player = game.players[game.current_player_index]
        
        legal_actions = Rules.get_legal_actions(current_player.hand, [], game.trump_suit)
        
        if current_player.ai:
            state = GameState.from_game(game)
            action = current_player.ai.choose_action(state, legal_actions)
            current_player.remove_cards(action)
            played_cards.append(action)
        
        for i in range(1, 4):
            next_index = (game.current_player_index + i) % 4
            next_player = game.players[next_index]
            
            legal_actions = Rules.get_legal_actions(next_player.hand, played_cards[0], game.trump_suit)
            
            if legal_actions:
                if next_player.ai:
                    state = GameState.from_game(game)
                    state.first_cards = played_cards[0]
                    action = next_player.ai.choose_action(state, legal_actions)
                else:
                    action = random.choice(legal_actions)
                next_player.remove_cards(action)
                played_cards.append(action)
        
        first_suit = played_cards[0][0].suit if not played_cards[0][0].is_joker else None
        winner_index = Rules.compare_cards(played_cards, first_suit, game.trump_suit)
        winner = game.players[(game.current_player_index + winner_index) % 4]
        
        round_score = Rules.calculate_round_score(played_cards)
        if winner.role == 'scorer':
            game.scores[game.team_scorer] += round_score
        
        game.current_player_index = game.players.index(winner)
    
    score = game.scores[game.team_scorer]
    if score > 115:
        return game.team_scorer, score, rounds
    elif score < 85:
        return 1 - game.team_scorer, score, rounds
    else:
        return -1, score, rounds

def main():
    print("=" * 60)
    print("        AI对战测试 - 规则AI vs 规则AI")
    print("=" * 60)
    print("\n配置：两队都使用规则AI")
    
    num_games = 10
    print(f"对局数: {num_games}")
    print("\n开始对战...")
    
    team0_wins = 0
    team1_wins = 0
    draws = 0
    
    for i in range(num_games):
        print(f"第 {i+1}/{num_games} 局...", end="", flush=True)
        
        ai_config = {
            0: RuleBasedAI(None),
            1: RuleBasedAI(None),
            2: RuleBasedAI(None),
            3: RuleBasedAI(None)
        }
        
        start_time = time.time()
        winner, score, rounds = play_game_fast(ai_config)
        elapsed = time.time() - start_time
        
        if winner == 0:
            team0_wins += 1
            print(f"队0胜! 得分:{score}, 轮数:{rounds}, 用时:{elapsed:.1f}s")
        elif winner == 1:
            team1_wins += 1
            print(f"队1胜! 得分:{score}, 轮数:{rounds}, 用时:{elapsed:.1f}s")
        else:
            draws += 1
            print(f"平局! 得分:{score}, 轮数:{rounds}, 用时:{elapsed:.1f}s")
    
    print("\n" + "=" * 60)
    print("对战结果统计")
    print("=" * 60)
    print(f"总对局数: {num_games}")
    print(f"队0胜: {team0_wins} ({team0_wins/num_games*100:.1f}%)")
    print(f"队1胜: {team1_wins} ({team1_wins/num_games*100:.1f}%)")
    print(f"平局: {draws} ({draws/num_games*100:.1f}%)")
    
    print("\n规则AI对战完成！每局约4-5秒")

if __name__ == "__main__":
    main()
