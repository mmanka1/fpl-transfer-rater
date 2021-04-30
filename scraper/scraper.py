import asyncio
import json
import aiohttp
import requests
import pandas as pd
import os
from understat import Understat

semaphore = asyncio.Semaphore(10)

async def get_pl_player():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        return await understat.get_league_players("epl", 2020)

async def get_player_match_stats(player_id, player_name, player_team):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        return await understat.get_player_matches(player_id, {"season": "2020"}), player_name, player_team

#Get team xG and xGA
async def get_team_stats(match, player, team):
    date = match['date'] 
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            team_results = await understat.get_team_results(team, 2020)
            result = None
            for res in team_results:
                if res["datetime"].split(" ")[0] == date:
                    result = res
            if result is not None:
                # return player, match, xGA, xG
                if result['side'] == "h":
                    return player, match, result["xG"]["a"], result["xG"]["h"]
                else:
                    return player, match, result["xG"]["h"], result["xG"]["a"]
            return None

async def getPlayers():
    return await get_pl_player()

#Return player data in fpl
def get_fpl_player_id(name, players):
    name_split = name.split(' ')
    for player in players:
        if name_split[0] in player['first_name'].split(' ') and name_split[len(name_split) - 1] in player['second_name'].split(' '):
            return player['id']

def get_fpl_player_stats(player_id):
    if player_id is not None:
        url = 'https://fantasy.premierleague.com/api/element-summary/{}/'.format(player_id)
        r = requests.get(url)
        json = r.json()
        return json['history']
    return None

def get_fpl_team_strength(team_id, teams):
    if team_id is not None:
        for team in teams:
            if team_id == team['id']:
                return team['strength_attack_home'], team['strength_attack_away'], team['strength_defence_home'], team['strength_defence_away']

def match_df_row(row, fpl_data, attribute):
    for data in fpl_data:
        if data['name'] == row['player']:
            for f in data['fpl']:
                if row['date'] in f['kickoff']:
                    if attribute == 'points':
                        return f['points']
                    if attribute == 'goals_conceded':
                        return f['goals_conceded']
                    if attribute == 'goals_scored':
                        return f['goals_scored']
                    if attribute == 'yellow_cards':
                        return f['yellow_cards']
                    if attribute == 'red_cards':
                        return f['red_cards']
                    if attribute == 'saves':
                        return f['saves']
                    if attribute == 'opponent':
                        return f['opponent_id']
                    if attribute == 'opponent_attack':
                        return f['opponent_attack_strength']
                    if attribute == 'opponent_defense':
                        return f['opponent_defense_strength']
            return None
    return None

if __name__ == '__main__':
    #Task 1 - get players
    loop = asyncio.get_event_loop()
    task1 = loop.create_task(getPlayers())
    players = loop.run_until_complete(task1)

    #Task 2 - get player match stats - including underlying data
    task2 = [get_player_match_stats(player['id'], player['player_name'], player['team_title']) for player in players]
    results2 = asyncio.gather(*task2, return_exceptions=True)
    match_stats = loop.run_until_complete(results2)

    #Task 3  - get team match stats - including underlying data
    task3 = [get_team_stats(match, player[1], player[2]) for player in match_stats if type(player) is not UnboundLocalError for match in player[0]]
    results3 = asyncio.gather(*task3, return_exceptions=True)
    player_matches = loop.run_until_complete(results3)
    player_matches = [player for player in player_matches if type(player) is not UnboundLocalError and player is not None]  #Filter player matches list
    # player_matches = [player for player in player_matches if type(player) is aiohttp.client_exceptions.ClientConnectorError]

    player_name = [match_player[0] for match_player in player_matches]
    unique_players = set(player_name)

    # #Create request to fpl data endpoint
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    r = requests.get(url)
    json = r.json()

    #Get FPL player data
    fpl = []
    for name in unique_players:
        fpl_stats = get_fpl_player_stats(get_fpl_player_id(name, json['elements']))
        if fpl_stats is not None:
            p = {"name": name, "fpl":[]}
            for gw_stats in fpl_stats:
                opponent_strength = get_fpl_team_strength(gw_stats['opponent_team'], json['teams'])
                p["fpl"].append({
                  "points": gw_stats['total_points'], 
                  "goals_conceded": gw_stats['goals_conceded'], 
                  "goals_scored": gw_stats['team_h_score'] if gw_stats['was_home'] is True else gw_stats['team_a_score'],
                  "yellow_cards": gw_stats['yellow_cards'],
                  "red_cards": gw_stats['yellow_cards'],
                  "saves": gw_stats['saves'],
                  "opponent_id": gw_stats['opponent_team'],
                  "opponent_attack_strength": opponent_strength[1] if gw_stats['was_home'] is True else opponent_strength[0],
                  "opponent_defense_strength": opponent_strength[3] if gw_stats['was_home'] is True else opponent_strength[2],
                  "kickoff": gw_stats['kickoff_time']
                })
            fpl.append(p)
    
    # Prepare columns 
    player_xG = [match_stat[1]['xG'] for match_stat in player_matches]
    player_npxG = [match_stat[1]['npxG'] for match_stat in player_matches]
    player_npG = [match_stat[1]['npg'] for match_stat in player_matches]
    player_G = [match_stat[1]['goals'] for match_stat in player_matches]
    player_xA = [match_stat[1]['xA'] for match_stat in player_matches]
    player_A = [match_stat[1]['assists'] for match_stat in player_matches]
    player_KP = [match_stat[1]['key_passes'] for match_stat in player_matches]
    player_shots = [match_stat[1]['shots'] for match_stat in player_matches]
    player_xGChain = [match_stat[1]['xGChain'] for match_stat in player_matches]
    player_xGBuildup = [match_stat[1]['xGBuildup'] for match_stat in player_matches]
    player_minutes = [match_stat[1]['time'] for match_stat in player_matches]
    team_xGA = [match_stat[2] for match_stat in player_matches]
    team_xG = [match_stat[3] for match_stat in player_matches]
    game_date = [match_stat[1]['date'] for match_stat in player_matches]

    #Prepare dataframe
    d = {'player': player_name, 
        'xG': player_xG,
        'npxG': player_npxG,
        'npG': player_npG,
        'goals': player_G,
        'xA': player_xA,
        'assists': player_A,
        'key_passes': player_KP,
        'shots': player_shots,
        'xGChain': player_xGChain,
        'xGBuildup': player_xGBuildup,
        'minutes': player_minutes,
        'team_xGA': team_xGA,
        'team_xG': team_xG,
        'date': game_date
    }

    #Create dataframe
    stats_df = pd.DataFrame(data=d)
    
    #Add columns consisting of fpl data
    stats_df['points'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'points'), axis = 1)
    stats_df['team_goals_conceded'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'goals_conceded'), axis = 1)
    stats_df['team_goals_scored'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'goals_scored'), axis = 1)
    stats_df['yellow_cards'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'yellow_cards'), axis = 1)
    stats_df['red_cards'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'red_cards'), axis = 1)
    stats_df['saves'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'saves'), axis = 1)
    stats_df['opponent'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'opponent'), axis = 1)
    stats_df['opponent_attack_strength'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'opponent_attack'), axis = 1)
    stats_df['opponent_defense_strength'] = stats_df.apply(lambda row: match_df_row(row, fpl, 'opponent_defense'), axis = 1)
    
    #Remove rows corresponding to matches without any points recorded
    stats_df.dropna(axis = 0, inplace=True)

    #Remove kickoff date column
    stats_df.drop(['date'], axis=1, inplace=True)
    
    #Example output
    print(stats_df.loc[stats_df['player'] == 'Harry Kane'].head(10))

    #Write dataframe to csv
    stats_df.to_csv(os.getcwd() + '\\backend\data\\form_fixture_stats.csv')