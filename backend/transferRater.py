from playerController import PlayerController
from pointsPredictor import PointsPredictor
import pandas as pd
import os

class TransferRater:
    def __init__(self, predictor, free_transfers, player_out, player_target, next_gws, starting_gw=0):
        #Instantiate controllers for each player
        player_out = PlayerController(player_name=player_out)
        player_target = PlayerController(player_name=player_target)

        # #Read csv file for input into prediction model
        # df_players = pd.read_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv', index_col=0)
        # predictor = PointsPredictor(df_players)

        # #Choose best parameters for model
        # selected_params = predictor.tune_params()
        # n_estimators = selected_params["n_estimators"]
        # max_depth = selected_params["max_depth"]

        # #Choose best model using these selected parameters
        # predictor.select_model(n_estimators, max_depth)

        # #train best model
        # predictor.train_model()

        #Get predicted points and chance of playing next round for the player to be transferred out
        predicted_points_player_out, cv_err = player_out.predict_player_points(next_gws=next_gws, starting_gw=starting_gw)
        chance_playing_player_out = player_out.get_playing_chance()

        #Get predicted points for the target player
        predicted_points_target, _ = player_target.predict_player_points(next_gws=next_gws, starting_gw=starting_gw)
        chance_playing_target = player_target.get_playing_chance()

        hit = 0 if free_transfers > 0 else 4
        risk = (predicted_points_player_out + hit) - predicted_points_player_out(chance_playing_player_out)
        reward = predicted_points_target(chance_playing_target) - (predicted_points_player_out + hit)

        self.risk_reward_ratio = risk/reward

    def get_risk_reward(self):
        return self.risk_reward_ratio