from playerController import PlayerController

class TransferRater:
    def __init__(self, predictor, player_out, player_target, next_gws, starting_gw=0):
        #Instantiate controllers for each player
        self.player_out = PlayerController(player_name=player_out)
        self.player_target = PlayerController(player_name=player_target)

        #Get predicted points and chance of playing next round for the player to be transferred out
        self.predicted_points_player_out = self.player_out.predict_player_points(predictor=predictor, next_gws=next_gws, starting_gw=starting_gw)
        self.chance_playing_player_out = self.player_out.get_playing_chance()

        #Get predicted points for the target player
        self.predicted_points_target = self.player_target.predict_player_points(predictor=predictor, next_gws=next_gws, starting_gw=starting_gw)
        self.chance_playing_target = self.player_target.get_playing_chance()

        risk = (self.predicted_points_player_out) - (self.predicted_points_player_out*self.chance_playing_player_out)
        reward = (self.predicted_points_target*self.chance_playing_target) - (self.predicted_points_player_out)

        self.risk_reward_ratio = risk/reward

    def get_risk_reward(self):
        return self.risk_reward_ratio

    def get_expected_points_in(self):
        return self.predicted_points_target

    def get_expected_points_out(self):
        return self.predicted_points_player_out

    def get_chance_playing_in(self):
        return self.chance_playing_target

    def get_chance_playing_out(self):
        return self.chance_playing_player_out

    def get_feedback(self, bank, selling_price):
        #If the selling price of the player to transfer out + amount in the bank is less than target player's price
        if bank + selling_price < self.player_target.get_fpl_player_cost():
            return "Insufficient funds for transfer.", 0
        if self.risk_reward_ratio > 0.66 or self.risk_reward_ratio < 0 or self.risk_reward_ratio == -1*0.0:
            if self.get_expected_points_in() <= self.get_expected_points_out():
                return "Likely not worth the transfer: expected to lose more points than gain.", 1
            #If target is likely to play significantly less minutes than the player to transfer out - by a factor of > 30% of averaged minutes played in recent games
            if self.get_chance_playing_out() > self.get_chance_playing_in() + 0.30:
                return "Likely not worth the transfer: target will likely play less minutes.", 1
            return "Likely not worth the transfer: determined by a combination of playing time and points expected", 1
        if self.risk_reward_ratio >= 0.33 and self.risk_reward_ratio <= 0.66:
            return "Likely a safe transfer: little gain, little loss.", 2
        return "Likely a good transfer: expected to gain more points than lose.", 3