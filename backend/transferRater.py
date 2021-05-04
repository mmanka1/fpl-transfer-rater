from playerController import PlayerController

class TransferRater:
    def __init__(self, predictor, free_transfers, player_out, player_target, next_gws, starting_gw=0):
        #Instantiate controllers for each player
        self.player_out = PlayerController(player_name=player_out)
        self.player_target = PlayerController(player_name=player_target)

        #Get predicted points and chance of playing next round for the player to be transferred out
        predicted_points_player_out, cv_err = self.player_out.predict_player_points(predictor=predictor, next_gws=next_gws, starting_gw=starting_gw)
        chance_playing_player_out = self.player_out.get_playing_chance()

        #Get predicted points for the target player
        predicted_points_target, _ = self.player_target.predict_player_points(predictor=predictor, next_gws=next_gws, starting_gw=starting_gw)
        chance_playing_target = self.player_target.get_playing_chance()

        hit = 0 if free_transfers > 0 else 4
        risk = (predicted_points_player_out + hit) - (predicted_points_player_out*chance_playing_player_out)
        reward = (predicted_points_target*chance_playing_target) - (predicted_points_player_out + hit)

        self.risk_reward_ratio = risk/reward

    def get_risk_reward(self):
        return self.risk_reward_ratio

    def get_feedback(self, bank, selling_price):
        #If the selling price of the player to transfer out + amount in the bank is less than target player's price
        if bank + selling_price < self.player_target.get_fpl_player_cost():
            return "Insufficient funds for transfer."
        if self.risk_reward_ratio > 0.5 or self.risk_reward_ratio < 0:
            return "Likely not worth the transfer: expected to lose more points than gain."
        if self.risk_reward_ratio >= 0.33 and self.risk_reward_ratio <= 0.5:
            return "Likely a safe transfer: little gain, little loss."
        return "Likely a good transfer: expected to gain more points than lose."