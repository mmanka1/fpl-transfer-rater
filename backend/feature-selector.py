import pandas as pd
import numpy as np
import os
from statsmodels.stats.outliers_influence import variance_inflation_factor 

df_players = pd.read_csv(os.getcwd() + '\\backend\data\\form_fixture_stats.csv', index_col=0)

#Sort rows by opponent played, which approximates random sorting
df_players.sort_values(by=['opponent'], inplace=True)
#Drop non-numeric columns
df_players.drop(['player', 'opponent'], axis=1, inplace=True)

#Get features
X = df_players.drop(['points'], axis=1)

#Find highly correlated feature variables
vif_data = pd.DataFrame() 
vif_data["feature"] = X.columns 
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))] 
print(vif_data)

#Drop columns corresponding to features with higher VIFs and check new VIFs
X_cleaned = X.drop(['yellow_cards', 'red_cards', 'npG', 'xGBuildup'], axis=1)

print('\nAfter removing features with high VIF:')
vif_data_cleaned = pd.DataFrame() 
vif_data_cleaned["feature"] = X_cleaned.columns 
vif_data_cleaned["VIF"] = [variance_inflation_factor(X_cleaned.values, i) for i in range(len(X_cleaned.columns))] 
print(vif_data_cleaned)

#Write cleaned dataframe to csv
df_players.to_csv(os.getcwd() + '\\backend\data\\cleaned_form_fixture_stats.csv')







