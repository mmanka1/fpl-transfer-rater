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

    def get_fpl_player_id(self, name):
        name_split = name.split(' ')
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        players = json['elements']
        for player in players:
            if name_split[0] in player['first_name'].split(' ') and name_split[len(name_split) - 1] in player['second_name'].split(' '):
                return player['id']
            else: 
                if name_split[0] in player['second_name'].split(' ') and name_split[len(name_split) - 1] in player['first_name'].split(' '):
                    return player['id']

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

    async def get_team_xGA(self, match, team):
        date = match['kickoff_time'] 
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            team_results = await understat.get_team_results(team, 2020)
            result = None
            for res in team_results:
                if res["datetime"].split(" ")[0] in date:
                    result = res
            if result is not None:
                if result['side'] == "h":
                    return result["xG"]["a"]
                else:
                    return result["xG"]["h"]
            return None

    def get_fpl_opponent_strength(self, id):
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r = requests.get(url)
        json = r.json()
        teams = json['teams']
        if id is not None:
            for team in teams:
                if id == team['id']:
                    return team['strength_attack_home'], team['strength_attack_away'], team['strength_defence_home'], team['strength_defence_away']

    def predict_player_points(self, next_opponents):
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

        #Team xGA
        task3 = [self.get_team_xGA(match, player_team) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)]]
        results3 = asyncio.gather(*task3, return_exceptions=True)
        team_xGAs = loop.run_until_complete(results3)
        team_xGA_lastsix = np.median([float(xGA) for xGA in team_xGAs])

        team_goals_scored_lastsix = np.median([ float(match['team_h_score']) if match['was_home'] is True else float(match['team_a_score']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)]])
        team_goals_conceded_lastsix = np.median([float(match['goals_conceded']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)]])
        saves_lastsix = np.median([float(match['saves']) for match in fpl_matches[len(fpl_matches)-games_considered:len(fpl_matches)]])

        #If a few games left or less, only need to consider those games
        if len(fpl_fixtures) < next_opponents:
            next_opponents = len(fpl_fixtures)
        next_opponent_attack_strength = np.median([float(self.get_fpl_opponent_strength(match['team_a'])[1]) if match['is_home'] is True else float(self.get_fpl_opponent_strength(match['team_h'])[1]) for match in fpl_fixtures[:next_opponents]])
        next_opponent_defense_strength = np.median([float(self.get_fpl_opponent_strength(match['team_a'])[3]) if match['is_home'] is True else float(self.get_fpl_opponent_strength(match['team_h'])[2]) for match in fpl_fixtures[:next_opponents]])

        #Check for player double gameweeks

        #Set up data and dataframe
        player_data = {
            'xG': [xG_lastsix],
            'npxG': [npxG_lastsix],
            'goals': [goals_lastsix],
            'xA': [xA_lastsix],
            'assists': [assists_lastsix],
            'key_passes	': [key_passes_lastsix],
            'shots': [shots_lastsix],
            'xGChain': [xGChain_lastsix],
            'minutes': [minutes_lastsix],
            'team_xGA': [team_xGA_lastsix],
            'team_goals_conceded': [team_goals_conceded_lastsix],
            'team_goals_scored': [team_goals_scored_lastsix],
            'saves': [saves_lastsix],
            'opponent_attack_strength': [next_opponent_attack_strength],
            'opponent_defense_strength': [next_opponent_defense_strength]
        }
        test_df = pd.DataFrame(data=player_data)

        #Read csv file for input into prediction model
        df_players = pd.read_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv', index_col=0)
        self.predictor = PointsPredictor(df_players)

        #Choose best parameters for model
        selected_params = self.predictor.tune_params()
        n_estimators = selected_params["n_estimators"]
        max_depth = selected_params["max_depth"]

        #Choose best model using these selected parameters
        self.predictor.select_model(n_estimators, max_depth)
        
        #Get points prediction and errors
        pred = self.predictor.get_predictions(test_df)
        cv_error = self.predictor.get_cv_error()
        generalization_error = self.predictor.get_generalization_error()
        self.predictor.get_feature_importance()
        return pred[0], cv_error, generalization_error

def main():
    player_name = "Diogo Jota"
    next_opponents = 1
    playerController = PlayerController(player_name=player_name)
    prediction, cv_err, generalization_err = playerController.predict_player_points(next_opponents=next_opponents)
    print('Predicted Points over the next %d gameweeks: %f' % (next_opponents, prediction))
    print('CV Error: %f' % cv_err)
    print('Generalization Error: %f' % generalization_err)

if __name__ == '__main__':
    main()