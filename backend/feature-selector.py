import pandas as pd
import numpy as np
import os
from statsmodels.stats.outliers_influence import variance_inflation_factor 

df_players = pd.read_csv(os.getcwd() + '\\backend\data\\form_fixture_stats.csv', index_col=0)

#Sort rows by opponent played, which approximates random sorting
df_players.sort_values(by=['opponent'], inplace=True)
print(df_players)

#Drop columns corresponding to higher VIFs
df_players.drop(['player', 'opponent', 'yellow_cards', 'red_cards', 'xGBuildup', 'goals', 'assists', 'minutes', 'npxG'], axis=1, inplace=True)

#Find highly correlated feature variables
vif_data = pd.DataFrame() 
vif_data["feature"] = df_players.columns 
vif_data["VIF"] = [variance_inflation_factor(df_players.values, i) for i in range(len(df_players.columns))] 

print(vif_data)






