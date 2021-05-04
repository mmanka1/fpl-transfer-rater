from fpl import FPL
from fpl.models.user import User
import aiohttp
import asyncio

import sys
sys.path.append('../')
from playerController import PlayerController

class UserController:
    def __init__(self, user_id, email, password):
        self.id = user_id
        self.email = email
        self.password = password
        self.playerController = PlayerController()

    async def get_user_team(self):
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            await fpl.login(self.email, self.password)
            user = await fpl.get_user(self.id)
            team = await user.get_team()
            self.players = [(self.playerController.get_fpl_player(player['element']), int(player['selling_price'])/10) for player in team]
            return self.players
               
    async def set_user_transfer_status(self):
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            await fpl.login(self.email, self.password)
            user = await fpl.get_user(self.id)
            status = await user.get_transfers_status()
            self.budget = status['bank']/10
            self.transfer_limit = status['limit']
    
    def get_budget(self):
        return self.budget

    def get_transfer_limit(self):
        return self.transfer_limit

def main():
    id = 1 #Replace with 6 digit integer id
    email = ''
    password = ''
    userController = UserController(264545, email, password)

    loop = asyncio.get_event_loop()
    task1 = loop.create_task(userController.get_user_team())
    user_team = loop.run_until_complete(task1)
    print(user_team)

    # task2 = loop.create_task(userController.get_user_transfer_status())
    # budget_remaining, transfers_remaining = loop.run_until_complete(task2)
    
if __name__ == '__main__':
    main()