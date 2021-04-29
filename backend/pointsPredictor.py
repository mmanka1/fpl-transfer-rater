import pandas as pd
import numpy as np
import os
import seaborn as sns
from xgboost import XGBRegressor, plot_importance
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from matplotlib import pyplot

class OppStrength2(BaseEstimator,TransformerMixin):  
    def fit(self,X,y=None):
        return self
    
    def transform(self,X,y=None):
        X = X.assign(opponent_defense_strength2 = X.opponent_defense_strength**2)
        X = X.assign(opponent_attack_strength2 = X.opponent_attack_strength**2)
        return X
        
#Points predictor model which uses gradient boosting
class PointsPredictor:
    def __init__(self, df):
        self.X = df.drop('points', axis=1)
        self.y = df.points
        #Split data into training and testing sets, setting aside 30% of the data for testing
        self.Xtrain, self.Xtest, self.ytrain, self.ytest = train_test_split(self.X, self.y, test_size = 0.30, random_state = 0)

    def tune_params(self):
        model = XGBRegressor(verbosity = 0)
        parameters = {"n_estimators": [50,100,150], "max_depth": [2,4,6]}
        #Test different parameters for an estimator
        grid_search = GridSearchCV(model, parameters, scoring = 'neg_mean_squared_error')
        #Fit model according to different set of parameters
        grid_search.fit(self.Xtrain, self.ytrain)
        return grid_search.best_params_
    
    def select_model(self, n_estimators, max_depth):
        #Linear terms
        model_lin = Pipeline([
            ('regression', XGBRegressor(
                verbosity = 0,
                objective ='reg:squarederror', 
                importance_type="gain", 
                n_estimators=n_estimators, 
                max_depth=max_depth
            ))
        ])

        #Quadratic terms for opponent strength - makes no notable difference
        model_opp_str = Pipeline([
            ('opponentStrength', OppStrength2()),
            ('regression', XGBRegressor(
                verbosity = 0,
                objective ='reg:squarederror', 
                importance_type="gain", 
                n_estimators=n_estimators, 
                max_depth=max_depth
            ))
        ])

        #Include quadratic and interaction terms
        model_poly = Pipeline([
            ('poly', PolynomialFeatures(degree=2, include_bias=False)),
            ('regression', XGBRegressor(
                verbosity = 0,
                objective ='reg:squarederror', 
                importance_type="gain", 
                n_estimators=n_estimators, 
                max_depth=max_depth
            ))
        ])
        
        cv_error_lin = -cross_val_score(model_lin, self.Xtrain, self.ytrain, scoring = 'neg_mean_squared_error').mean()
        cv_error_opp_str = -cross_val_score(model_opp_str, self.Xtrain, self.ytrain, scoring = 'neg_mean_squared_error').mean()
        cv_error_poly = -cross_val_score(model_poly, self.Xtrain, self.ytrain, scoring = 'neg_mean_squared_error').mean()

        print('cv_score_lin %f' % cv_error_lin)
        print('cv_score_opp_str %f' % cv_error_opp_str)
        print('cv_score_poly %f\n' % cv_error_poly)

        if (cv_error_lin < cv_error_poly):
            self.best_fit_model = model_lin
            self.cv_error = cv_error_lin
        else:
            self.best_fit_model = model_poly
            self.cv_error = cv_error_poly
    
    def train_model(self):
        #Fit model to entire dataset
        self.best_fit_model.fit(self.X, self.y)

    def get_cv_error(self):
        return self.cv_error

    def get_feature_importance(self):
        plot_importance(self.best_fit_model.named_steps['regression'])
        pyplot.show()

    def get_generalization_error(self):
        #Refit model
        self.best_fit_model.fit(self.Xtrain, self.ytrain)
        #Get predictions
        ypred = self.best_fit_model.predict(self.Xtest)
        #Compute test errors
        self.generalization_error = ((self.ytest - ypred)**2).mean()
        return self.generalization_error

    def get_predictions(self, testData):
        return self.best_fit_model.predict(testData)