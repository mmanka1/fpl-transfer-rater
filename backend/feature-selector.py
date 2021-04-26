import pandas as pd
import numpy as np
import os
from statsmodels.stats.outliers_influence import variance_inflation_factor 

df_players = pd.read_csv(os.getcwd() + '\\backend\data\\form_fixture_stats.csv', index_col=0)

#Sort rows by opponent played, which approximates random sorting
df_players.sort_values(by=['opponent'], inplace=True)
#Drop non-numeric columns
df_players.drop(['player', 'opponent'], axis=1, inplace=True)

#Find highly correlated feature variables
vif_data = pd.DataFrame() 
vif_data["feature"] = df_players.columns 
vif_data["VIF"] = [variance_inflation_factor(df_players.values, i) for i in range(len(df_players.columns))] 
print(vif_data)

#Drop columns corresponding to higher VIFs and check new VIFs
df_players.drop(['yellow_cards', 'red_cards', 'xGBuildup', 'assists', 'npxG', 'goals'], axis=1, inplace=True)

vif_data_cleaned = pd.DataFrame() 
vif_data_cleaned["feature"] = df_players.columns 
vif_data_cleaned["VIF"] = [variance_inflation_factor(df_players.values, i) for i in range(len(df_players.columns))] 
print(vif_data_cleaned)

#Write cleaned dataframe to csv
df_players.to_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv')







