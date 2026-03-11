"""测试MCTS AI vs 规则AI"""
import random
from game.game import Game
from game.rules import Rules
from ai.rule_based_ai import RuleBasedAI
from ai.mcts_ai import MCTSAI
from ai.game_state import GameState

def test_mcts():
    print("测试MCTS AI...")
    
    ai_players = {
        0: MCTSAI(None, time_limit=0.5),
        1: RuleBasedAI(None),
        2: MCTSAI(None, time_limit=0.5),
        3: RuleBasedAI(None)
    }
    
    game = Game(ai_players=ai_players)
    game.deck.shuffle()
    
    for player_idx, card, round_num in game.deck.deal_one_by_one(game.players):
        player = game.players[player_idx]
        has_pair, suit, rank = player.check_new_card_pair(card)
        if has_pair and game.trump_suit is None:
            if random.random() > 0.3:
                game.trump_suit = suit
    
    if game.trump_suit is None:
        game.trump_suit = random.choice(['黑桃', '红心', '梅花', '方块'])
    
    declarer = None
    for player in game.players:
        if any(suit == game.trump_suit for (suit, rank) in player.get_pairs()):
            declarer = player
            break
    
    if not declarer:
        declarer = random.choice(game.players)
    
    game.team_scorer = declarer.team
    for player in game.players:
        if player.team == game.team_scorer:
            player.role = 'scorer'
        else:
            player.role = 'runner'
    
    print(f"主花色: {game.trump_suit}")
    print(f"得分组: 队{game.team_scorer}")
    
    runner_players = [p for p in game.players if p.role == 'runner']
    first_player = random.choice(runner_players)
    game.current_player_index = game.players.index(first_player)
    
    for round_num in range(3):
        current_player = game.players[game.current_player_index]
        legal_actions = Rules.get_legal_actions(current_player.hand, [], game.trump_suit)
        
        if current_player.ai:
            state = GameState.from_game(game)
            action = current_player.ai.choose_action(state, legal_actions)
            print(f"{current_player.name} 出: {action}")
            current_player.remove_cards(action)
        else:
            action = random.choice(legal_actions)
            current_player.remove_cards(action)
    
    print("\n测试成功！MCTS AI可以正常工作")

if __name__ == "__main__":
    test_mcts()
