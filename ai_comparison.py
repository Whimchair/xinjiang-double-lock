"""AI对战对比测试"""
import random
import time
from game.game import Game
from game.rules import Rules
from ai.rule_based_ai import RuleBasedAI
from ai.mcts_ai import ImprovedMCTSAI
from ai.game_state import GameState

class RandomAI:
    def __init__(self, player=None):
        self.player = player
    def choose_action(self, game_state, legal_actions):
        return random.choice(legal_actions)

def play_game(ai_config):
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
        player.role = 'scorer' if player.team == game.team_scorer else 'runner'
    
    runner_players = [p for p in game.players if p.role == 'runner']
    first_player = random.choice(runner_players)
    game.current_player_index = game.players.index(first_player)
    
    while all(len(p.hand) > 0 for p in game.players):
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
        return game.team_scorer
    elif score < 85:
        return 1 - game.team_scorer
    else:
        return -1

def run_battle(name, ai_config, num_games=10):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    
    team0_wins = 0
    team1_wins = 0
    draws = 0
    
    for i in range(num_games):
        winner = play_game(ai_config)
        if winner == 0:
            team0_wins += 1
        elif winner == 1:
            team1_wins += 1
        else:
            draws += 1
        print(f"  {i+1}/{num_games}", end="\r", flush=True)
    
    print(f"\n  队0胜: {team0_wins} ({team0_wins/num_games*100:.0f}%)  |  队1胜: {team1_wins} ({team1_wins/num_games*100:.0f}%)  |  平局: {draws} ({draws/num_games*100:.0f}%)")
    return team0_wins, team1_wins, draws

def main():
    print("=" * 60)
    print("         AI对战对比测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 规则AI vs 规则AI
    r1, r2, r3 = run_battle("规则AI vs 规则AI (10局)", {
        0: RuleBasedAI(None), 1: RuleBasedAI(None),
        2: RuleBasedAI(None), 3: RuleBasedAI(None)
    }, 10)
    results.append(("规则AI vs 规则AI", r1, r2, r3))
    
    # 测试2: 改进MCTS vs 规则AI
    r1, r2, r3 = run_battle("改进MCTS vs 规则AI (5局)", {
        0: ImprovedMCTSAI(None, time_limit=0.2),
        1: RuleBasedAI(None),
        2: ImprovedMCTSAI(None, time_limit=0.2),
        3: RuleBasedAI(None)
    }, 5)
    results.append(("MCTS vs 规则AI", r1, r2, r3))
    
    # 测试3: 随机AI vs 规则AI
    r1, r2, r3 = run_battle("随机AI vs 规则AI (10局)", {
        0: RuleBasedAI(None), 1: RandomAI(None),
        2: RuleBasedAI(None), 3: RandomAI(None)
    }, 10)
    results.append(("随机AI vs 规则AI", r1, r2, r3))
    
    print("\n" + "=" * 60)
    print("         对战结果汇总")
    print("=" * 60)
    print(f"{'对战':<20} {'队0胜':>8} {'队1胜':>8} {'平局':>8}")
    print("-" * 60)
    for name, t0, t1, d in results:
        print(f"{name:<20} {t0:>8} {t1:>8} {d:>8}")
    print("=" * 60)

if __name__ == "__main__":
    main()
