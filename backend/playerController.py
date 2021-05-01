import asyncio
import json
import aiohttp
import requests
from understat import Understat
import numpy as np
import pandas as pd
from matplotlib import pyplot

import sys
sys.path.append('../')
import os
from pointsPredictor import PointsPredictor

class PlayerController:
    def __init__(self, player_name):
        self.player_name = player_name

    async def get_player(self, name):
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            player = await understat.get_league_players("epl", 2020, player_name=name)
            return player[0]['id'], player[0]['team_title']

    async def get_player_matches(self, id):
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            player_matches = await understat.get_player_matches(id)
            return player_matches

    def find_player(self, name):
        name_split = name.split(' ')
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        players = json['elements']
        for player in players:
            if name_split[0] in player['first_name'].split(' ') and name_split[len(name_split) - 1] in player['second_name'].split(' '):
                return player
            else: 
                if name_split[0] in player['second_name'].split(' ') and name_split[len(name_split) - 1] in player['first_name'].split(' '):
                    return player

    def find_team(self, id):
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        teams = json['teams']
        for team in teams:
            if team['id'] == id:
                if team['name'] == "Man Utd":
                    return "Manchester United"
                if team['name'] == "Man City":
                    return "Manchester City"
                if team['name'] == "Sheffield Utd":
                    return "Sheffield United"
                if team['name'] == "West Brom":
                    return "West Bromwich Albion"
                if team['name'] == "Wolves":
                    return "Wolverhampton Wanderers"
                if team['name'] == "Spurs":
                    return "Tottenham"
                return team['name']

    def get_fpl_player_id(self, name):
        return self.find_player(name)['id']

    def get_player_playing_chance(self, name):
        player = self.find_player(name)
        #Get chance of playing based on player fitness
        fitness = player['chance_of_playing_next_round'] if player['chance_of_playing_next_round'] is not None else 100
        #Find number of minutes played recently by player
        id = player['id']
        matches = self.get_player_fpl_matches(id)
        total_minutes_played_lastthree = np.sum([match['minutes'] for match in matches[len(matches)-4:len(matches)-1]])
        minutes_played_per_game = total_minutes_played_lastthree/3

        playing_chance = (minutes_played_per_game * (fitness/100))/90
        return playing_chance

    def get_player_fpl_matches(self, id):
        if id is not None:
            url = 'https://fantasy.premierleague.com/api/element-summary/{}/'.format(id)
            r = requests.get(url)
            json = r.json()
            return json['history']
        return None

    def get_player_fpl_fixtures(self, id):
        if id is not None:
            url = 'https://fantasy.premierleague.com/api/element-summary/{}/'.format(id)
            r = requests.get(url)
            json = r.json()
            return json['fixtures']
        return None

    #Get team xGA and xG
    async def get_team_stats(self, match, team):
        date = match['kickoff_time'] 
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            #Get team stats
            team_results = await understat.get_team_results(team, 2020)
            result = None
            for res in team_results:
                if res["datetime"].split(" ")[0] in date:
                    result = res
            if result is not None:
                if result['side'] == "h":
                    return result["xG"]["a"], result["xG"]["h"]
                else:
                    return result["xG"]["h"], result["xG"]["a"]
            return None

    #Get opponents season long xGA and xG leading up to each match
    async def get_opponent_stats(self, opponent_team):
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            team_stats = await understat.get_team_stats(opponent_team, 2020)
            xG = np.sum([
                team_stats['situation']['OpenPlay']['xG'],
                team_stats['situation']['FromCorner']['xG'],
                team_stats['situation']['SetPiece']['xG'],
                team_stats['situation']['DirectFreekick']['xG'],
                team_stats['situation']['Penalty']['xG'],
            ])
            xGA = np.sum([
                team_stats['situation']['OpenPlay']['against']['xG'], 
                team_stats['situation']['FromCorner']['against']['xG'],
                team_stats['situation']['SetPiece']['against']['xG'],
                team_stats['situation']['DirectFreekick']['against']['xG'],
                team_stats['situation']['Penalty']['against']['xG'],
            ])
            return xG, xGA

    def get_fpl_opponent_strength(self, id):
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        teams = json['teams']
        if id is not None:
            for team in teams:
                if id == team['id']:
                    return team['strength_attack_home'], team['strength_attack_away'], team['strength_defence_home'], team['strength_defence_away']

    def model_player_points(self):
        #Read csv file for input into prediction model
        df_players = pd.read_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv', index_col=0)
        self.predictor = PointsPredictor(df_players)

        #Choose best parameters for model
        selected_params = self.predictor.tune_params()
        n_estimators = selected_params["n_estimators"]
        max_depth = selected_params["max_depth"]

        #Choose best model using these selected parameters
        self.predictor.select_model(n_estimators, max_depth)

        #train best model
        self.predictor.train_model()

    def model_features(self):
        self.predictor.get_feature_importance()

    def predict_player_points(self, next_opponents, later_gw=0):
        loop = asyncio.get_event_loop()
        task1 = loop.create_task(self.get_player(self.player_name))
        player_id, player_team = loop.run_until_complete(task1)

        task2 = loop.create_task(self.get_player_matches(player_id))
        matches = loop.run_until_complete(task2)

        #Get fpl-related data
        fpl_player_id = self.get_fpl_player_id(self.player_name)
        fpl_matches = self.get_player_fpl_matches(fpl_player_id)
        fpl_fixtures = self.get_player_fpl_fixtures(fpl_player_id)
        
        #Compute median of data pertaining to the last 6 matches for player
        games_considered = 6
        xG_lastsix = np.median([float(match['xG']) for match in matches[:games_considered]])
        npxG_lastsix = np.median([float(match['npxG']) for match in matches[:games_considered]])
        goals_lastsix = np.median([float(match['goals']) for match in matches[:games_considered]])
        xA_lastsix = np.median([float(match['xA']) for match in matches[:games_considered]])
        assists_lastsix = np.median([float(match['assists']) for match in matches[:games_considered]])
        key_passes_lastsix = np.median([float(match['key_passes']) for match in matches[:games_considered]])
        shots_lastsix = np.median([float(match['shots']) for match in matches[:games_considered]])
        xGChain_lastsix = np.median([float(match['xGChain']) for match in matches[:games_considered]])
        minutes_lastsix = np.median([float(match['time']) for match in matches[:games_considered]])

        #Team xGA and xG
        task3 = [self.get_team_stats(match, player_team) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)]]
        results3 = asyncio.gather(*task3, return_exceptions=True)
        team_stats = loop.run_until_complete(results3)
        team_xGA_lastsix = np.median([float(stat[0]) for stat in team_stats if stat is not None])
        team_xG_lastsix = np.median([float(stat[1]) for stat in team_stats if stat is not None])

        #Get opponent teams
        opponent_teams = [self.find_team(match['team_a']) if match['is_home'] is True else self.find_team(match['team_h']) for match in fpl_fixtures[later_gw:next_opponents]]
        #Opponent xGA and xG
        task4 = [self.get_opponent_stats(opponent) for opponent in opponent_teams]
        results4 = asyncio.gather(*task4, return_exceptions=True)
        opponent_stats = loop.run_until_complete(results4)
        opponent_xG = np.median([float(stat[0]) for stat in opponent_stats if stat is not None])
        opponent_xGA = np.median([float(stat[1]) for stat in opponent_stats if stat is not None])

        #Team goals scored and conceded
        team_goals_scored_lastsix = np.median([float(match['team_h_score']) if match['was_home'] is True else float(match['team_a_score']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)] if match['team_h_score'] and match['team_a_score'] is not None])
        team_goals_conceded_lastsix = np.median([float(match['goals_conceded']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)] if match['team_h_score'] and match['team_a_score'] is not None])
        saves_lastsix = np.median([float(match['saves']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)] if match['team_h_score'] and match['team_a_score'] is not None])

        #If a few games left or less, only need to consider those games
        if len(fpl_fixtures) < next_opponents:
            next_opponents = len(fpl_fixtures)
        next_opponent_attack_strength = np.median([float(self.get_fpl_opponent_strength(match['team_a'])[1]) if match['is_home'] is True else float(self.get_fpl_opponent_strength(match['team_h'])[1]) for match in fpl_fixtures[later_gw:next_opponents]])
        next_opponent_defense_strength = np.median([float(self.get_fpl_opponent_strength(match['team_a'])[3]) if match['is_home'] is True else float(self.get_fpl_opponent_strength(match['team_h'])[2]) for match in fpl_fixtures[later_gw:next_opponents]])

        #Check for player double gameweeks

        #Set up data and dataframe
        player_data = {
            'xG': [xG_lastsix],
            'npxG': [npxG_lastsix],
            'goals': [goals_lastsix],
            'xA': [xA_lastsix],
            'assists': [assists_lastsix],
            'key_passes': [key_passes_lastsix],
            'shots': [shots_lastsix],
            'xGChain': [xGChain_lastsix],
            'minutes': [minutes_lastsix],
            'team_xGA': [team_xGA_lastsix],
            'team_xG': [team_xG_lastsix],
            'opponent_xGA': [opponent_xGA],
            'opponent_xG': [opponent_xG],
            'team_goals_conceded': [team_goals_conceded_lastsix],
            'team_goals_scored': [team_goals_scored_lastsix],
            'saves': [saves_lastsix],
            'opponent_attack_strength': [next_opponent_attack_strength],
            'opponent_defense_strength': [next_opponent_defense_strength]
        }
        test_df = pd.DataFrame(data=player_data)
        
        #Get points prediction and errors
        pred = self.predictor.get_predictions(test_df)
        cv_error = self.predictor.get_cv_error()
        return pred[0], cv_error

def main():
    player_name = "Jamie Vardy"
    next_opponents = 2

    playerController = PlayerController(player_name=player_name)
    playerController.model_player_points()
    # playerController.model_features()

    prediction, cv_err = playerController.predict_player_points(next_opponents=next_opponents, later_gw=0)
    print('Predicted Points over the next %d gameweeks: %f' % (next_opponents, prediction))
    print('CV Error: %f' % cv_err)

    print(playerController.get_player_playing_chance(player_name))

if __name__ == '__main__':
    main()