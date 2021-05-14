from flask import Flask, request, make_response, jsonify
import asyncio
from transferRater import TransferRater
from userController import UserController
from model import Model

app = Flask(__name__)
model = None

def get_user(id):
    return UserController(user_id=id)

@app.route('/')
def welcome():
    return 'Welcome'

@app.route('/myteam', methods=['POST', 'GET'])
def my_team():
    try:
        user = get_user(264545)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        #Get team picks
        task1 = loop.create_task(user.set_user_team())
        loop.run_until_complete(task1)
        team = user.get_user_team()

        #Get bank
        task2 = loop.create_task(user.set_bank())
        loop.run_until_complete(task2)
        bank = user.get_bank()
        response = make_response(
            jsonify(
                {
                    "error": False,
                    "message":{
                        "team": team,
                        "bank": bank
                    }
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response
    except Exception as exception:
        response = make_response(
            jsonify(
                {
                    "error": True,
                    "message": "failure occurred while retrieving team information: {}".format(exception)
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response

@app.route('/train', methods=['POST', 'GET'])
def train():
    try:
        global model
        model = Model(retrain=True)
        response = make_response(
            jsonify(
                {
                    "error": False,
                    "message": "model trained successfully"
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response
    except:
        response = make_response(
            jsonify(
                {
                    "error": True,
                    "message": "failure occurred while training model"
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response

@app.route('/rate', methods=['GET'])
def rater():
    try: 
        if model is not None:
            user = get_user(264545)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            task = loop.create_task(user.set_user_transfer_status())
            loop.run_until_complete(task)
            bank = user.get_bank()

            rater = TransferRater(predictor=model.get_model(), player_out="Harry Kane", player_target="Chris Wood", next_gws=4, starting_gw=0)
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
                        "error": False,
                        "message": {
                            "feedback": feedback,
                            "transfer_rating": rating,
                            "points_transfer_in": str(points_in),
                            "points_transfer_out": str(points_out),
                            "risk_reward_ratio": risk_reward_ratio,
                            "chance_playing_transfer_in": chance_playing_transfer_in,
                            "chance_playing_transfer_out": chance_playing_transfer_out,
                        }
                    }
                )
            )
            response.headers["Content-Type"] = "application/json"
            return response
        response = make_response(
            jsonify(
                {
                    "error": True,
                    "message": "model has not been trained"
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response
    except:
        response = make_response(
            jsonify(
                {
                    "error": True,
                    "message": "failure occurred while performing rating"
                }
            )
        )
        response.headers["Content-Type"] = "application/json"
        return response

if __name__ == '__main__':
    app.run(debug=True)