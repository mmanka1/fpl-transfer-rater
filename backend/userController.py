from fpl import FPL
from fpl.models.user import User
import requests
import aiohttp
import asyncio

from requests.api import request

from playerController import PlayerController

class UserController:
    def __init__(self, user_id):
        self.id = user_id
        self.playerController = PlayerController()

    async def set_user_team(self):
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            user = await fpl.get_user(self.id)
            my_teams = await user.get_picks()
            self.curr_gw = len(my_teams)
            current_team = my_teams[self.curr_gw]
            self.players = [{
                "player": self.playerController.get_fpl_player(player['element']),
                } 
            for player in current_team]

    def get_user_team(self):
        return self.players
        
    async def set_bank(self):
        url = 'https://fantasy.premierleague.com/api/entry/{}/event/{}/picks/'.format(self.id, self.curr_gw)
        r = requests.get(url)
        json = r.json()
        self.bank = int(json['entry_history']['bank'])/10
    
    def get_bank(self):
        return self.bank

def main():
    id = 1 #Replace with 6 digit integer id
    userController = UserController(id)

    loop = asyncio.get_event_loop()
    task1 = loop.create_task(userController.get_user_team())
    user_team = loop.run_until_complete(task1)
    print(user_team)

    # task2 = loop.create_task(userController.get_user_transfer_status())
    # budget_remaining, transfers_remaining = loop.run_until_complete(task2)
    
if __name__ == '__main__':
    main()