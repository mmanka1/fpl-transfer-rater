from flask import Flask, request, make_response, jsonify
import asyncio
from transferRater import TransferRater
from userController import UserController
from model import Model

app = Flask(__name__)

def get_user(id, email, password):
    return UserController(user_id=id,email=email, password=password)

@app.route('/')
def welcome():
    return 'Welcome'

@app.route('/myteam', methods=['POST', 'GET'])
def my_team():
    user = get_user(1, "", "")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    task = loop.create_task(user.set_user_team())
    loop.run_until_complete(task)
    team = user.get_user_team()
    response = make_response(
        jsonify(
            {"team": team}
        )
    )
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/rate', methods=['POST', 'GET'])
def rater():
    model = Model(retrain=True)
    user = get_user(1, "", "")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    task = loop.create_task(user.set_user_transfer_status())
    loop.run_until_complete(task)
    bank = user.get_bank()
    free_transfers = user.get_free_transfer_limit()

    rater = TransferRater(predictor=model.get_model(), free_transfers=free_transfers, player_out="Harry Kane", player_target="Chris Wood", next_gws=4, starting_gw=0)
    r = rater.get_feedback(bank=bank, selling_price=10.2)
    feedback = r[0]
    rating = r[1]
    points_in = rater.get_expected_points_in()
    points_out = rater.get_expected_points_out()
    risk_reward_ratio = rater.get_risk_reward()
    chance_playing_transfer_in = rater.get_chance_playing_in()
    chance_playing_transfer_out = rater.get_chance_playing_out()

    response = make_response(
        jsonify(
            {
                "feedback": feedback,
                "transfer_rating": rating,
                "points_gain": str(points_in - points_out),
                "points_transfer_in": str(points_in),
                "points_transfer_out": str(points_out),
                "risk_reward_ratio": str(risk_reward_ratio),
                "chance_playing_transfer_in": chance_playing_transfer_in,
                "chance_playing_transfer_out": chance_playing_transfer_out,
            }
        )
    )
    response.headers["Content-Type"] = "application/json"
    return response

if __name__ == '__main__':
    app.run(debug=True)