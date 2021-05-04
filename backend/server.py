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

@app.route('/myteam')
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

    rater = TransferRater(predictor=model.get_model(), free_transfers=free_transfers, player_out="Patrick Bamford", player_target="Dominic Calvert-Lewin", next_gws=2)
    return rater.get_feedback(bank=bank, selling_price=10.2)

if __name__ == '__main__':
    app.run(debug=True)