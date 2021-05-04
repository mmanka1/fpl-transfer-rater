import pandas as pd
import os
from pointsPredictor import PointsPredictor

class Model:
    def __init__(self, retrain=False):
        #Read csv file for input into prediction model
        df_players = pd.read_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv', index_col=0)
        self.predictor = PointsPredictor(df_players)

        if retrain is True:
            #Choose best parameters for model
            selected_params = self.predictor.tune_params()
            n_estimators = selected_params["n_estimators"]
            max_depth = selected_params["max_depth"]

            #Choose best model using these selected parameters
            self.predictor.select_model(n_estimators, max_depth)

            #train best model
            self.predictor.train_model()
    
    def get_model(self):
        return self.predictor