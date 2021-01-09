# imports 
from riotwatcher import LolWatcher, ApiError #for GET requests to Riot/Leauge API, #ApiError not used
# import pandas as pd # not in use
import psutil # for monitoring and closing the leauge client 
import time # for checking the timel

# TODO: Test everything! So far nothing has been tested:(
# TODO loop and periodically check matches in the background

#Hardcoded variables 
api_key = 'KEY'
watcher = LolWatcher(api_key)

#Global Variables
my_region = 'na1'
time_of_last_loss = 0
timeout_end = 0

# summoner details
s_name = 'Fio'
me = watcher.summoner.by_name(my_region, s_name)
#print(me)

# def check_last_two_ranked_games(s_name: str) -> List[dict]:
def get_last_two_ranked_games(s_name):
    # Get recent match history 
    matches = watcher.match.matchlist_by_account(my_region, me['accountId'])
    
    last_matches = []
    
    #Run through the last 50 matches,
    #Create list containing last two Ranked matches 
    match_counter = 0
    for match in matches['matches']: 
        match_counter +=1
        
        if match['queue'] == 420: #Check that match is ranked (queue type is 420)
            last_matches.append(match)
            
        if len(last_matches) > 1 or (match_counter > 50): 
            break
            
    return last_matches                  
    
def check_if_lost(match_list):
    '''
    Takes a list of matches as input
    Finds the details of thoes matches and
    checks if the user/Summoner has lost thoes games
    '''
    global my_region
    global watcher
    lost_games = []

    match_details = []
    for match in match_list:
        match_details.append(watcher.match.by_id(my_region, match['gameId']))
    
    for match_detail_dict, match in zip(match_details, match_list):
        for participant in match_detail_dict['participants']:
            if participant['championId'] == match['champion']:
                if not participant['stats']['win']:
                    lost_games.append(
                        {'gameId': match['gameId'],
                         'timestamp':match['timestamp']})
                    
#     return [lost_games, match_details]      
    return lost_games

def tilt_check(lost_games):
    # if user has lost 2 ranked games within 2 hours
    # the league client will be killed and forced closed for 2 hours.
   
    if not len(lost_games) > 1:
        return
    
    time_between_games = abs(lost_games[0]['timestamp'] - lost_games[1]['timestamp'])
    
    if (time.time()-lost_games[0]['timestamp'] < 7200) \
    and (time_between_games < 7200): 
        # if time between games is less than 2hrs and last game was less than 2hrs ago,
        # kill client
        timeout_end = lost_games[0]['timestamp'] + 7200
        while time.time() < timeout_end:
            kill_leauge()
            time.sleep(60)

def kill_leauge():
    for process in psutil.process_iter():
        if process.name() == "LeaugeClient.exe":
            process.kill()
            