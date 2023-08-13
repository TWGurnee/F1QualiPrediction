import fastf1
from matplotlib import pyplot as plt
import fastf1.plotting
import fastf1.events
import pandas as pd
import numpy as np

from statistics import mean
from statistics import StatisticsError

from q_helpers import filter_anomalous_Q_laps, return_ranked_Q_laps, check_average_laps, pick_lead_driver
from constants import *

fastf1.Cache.enable_cache(r"M:\Coding\F1DataAnalysis\FastF1Cache")



# We want one scrape to then collate all data into one structure.
# First we scrape the races into new function adapted from below:
# This function needs to get each session, and return 

# From this output each DF can be averaged and calculated. This prevents scraping the data more than once, which is the rate limiting step.

def return_race_quali_ranks(race: str, quali_type: str | int = "Q" or 3, includes_anomalous_quali: bool = False):
    """
    Return ranked qualifying lap data for a specific race session.

    This function retrieves the qualifying lap data for a specific race session and calculates ranks for drivers
    based on their qualifying performance. Anomalies in lap times can also be filtered out.

    Args:
        race (str): The name of the race session.
        quali_type (str or int, optional): The type of qualifying session.
                                           Use "Q" for standard qualifying or 3 for sprint qualifying.
                                           Defaults to "Q".
        includes_anomalous_quali (bool, optional): Whether to include anomalies in lap times.
                                                   Defaults to False.

    Returns:
        dict: A dictionary containing two DataFrames:
            - "Fastest Laps": DataFrame with ranks for fastest lap times and sector times.
            - "Average Laps": DataFrame with ranks for average lap times and sector times.
              Both DataFrames include columns for Driver, Team, lap times, ranks, and percentage off pace.
    """    
    
    Q = fastf1.get_session(2023, race, quali_type) # Update logic here to stop trying to load races before the date of their arrival.
    Q.load()
    
    quali_filtered_laps, poor_quali_ranks = filter_anomalous_Q_laps(Q)
    
    if includes_anomalous_quali:
        Q_ranks = return_ranked_Q_laps(quali_filtered_laps, poor_quali_ranks)
        
    else:
        Q_ranks = return_ranked_Q_laps(quali_filtered_laps)
    
    return Q_ranks



def scrape_all_quali_laps(includes_anomalous_quali: bool = False):   
    """
    Scrape qualifying data for races and sprints.

    This function scrapes qualifying data for all specified races and associated sprints, if applicable.
    It uses the provided parameters to fetch qualifying ranks for each race and sprint.

    Args:
        includes_anomalous_quali (bool, optional): If True, includes anomalous qualifying data. Defaults to False.

    Returns:
        dict: A dictionary containing scraped qualifying data for races and sprints.
              The structure is as follows:
              {
                  "Races": {
                      "Race1": [quali_rank_1, quali_rank_2, ...],
                      "Race2": [quali_rank_1, quali_rank_2, ...],
                      ...
                  },
                  "Sprints": {
                      "Sprint1": [sprint_quali_rank_1, sprint_quali_rank_2, ...],
                      "Sprint2": [sprint_quali_rank_1, sprint_quali_rank_2, ...],
                      ...
                  }
              }
              If scraping encounters an error for any race, it will be omitted from the dictionary.
    """
    print("Scraping qualifying data")
   
    race_output = {}
    sprint_output = {}
    
    for race in RACES:
        print(f"Scraping {race}")
        try:    
            quali_ranks = return_race_quali_ranks(race=race, quali_type="Q", includes_anomalous_quali=includes_anomalous_quali)
            race_output[race] = quali_ranks

            if race in SPRINTS:
                sprint_ranks = return_race_quali_ranks(race=race, quali_type=3, includes_anomalous_quali=includes_anomalous_quali)
                sprint_output[race] = sprint_ranks
                
        except Exception as e:
            print(f"Cannot scrape {race} as: {e}")
            break
    

    
    return {"Races": race_output, "Sprints": sprint_output}



def filter_ranks_by_downforce(qualifying_ranks, downforce: int):
    """
    Filter qualifying ranks based on downforce level.

    This function filters the provided qualifying rank data based on the specified downforce level.
    If `downforce` is 0, the original ranking data for races and sprints is returned.
    Otherwise, the function filters the ranking data to include only tracks associated with the given downforce level.

    Args:
        qualifying_ranks (dict): A dictionary containing qualifying rank data for races and sprints.
        downforce (int): The downforce level to filter by. Use 0 to return all tracks.

    Returns:
        tuple: A tuple containing two dictionaries:
            - race_ranks: A dictionary containing filtered race ranking data based on the downforce level.
            - sprint_ranks: A dictionary containing filtered sprint ranking data based on the downforce level.
                          If `downforce` is 0, the original unfiltered data is returned.
    """
    
    if not downforce:
        return qualifying_ranks["Races"], qualifying_ranks["Sprints"]
    else:
        selected_tracks = DF_RACES[downforce]
        race_ranks = {track: df for track, df in qualifying_ranks["Races"].items() if track in selected_tracks}
        sprint_ranks = {track: df for track, df in qualifying_ranks["Sprints"].items() if track in selected_tracks}
        
        print(f"filtered rankings to downforce: {downforce}")
        return race_ranks, sprint_ranks


def return_df_q_rankings(qualifying_ranks, downforce: int):
    """
    Calculate pace rankings based on qualifying lap data.

    This function calculates pace rankings based on the provided qualifying rank data.
    Rankings are calculated for drivers and teams based on fastest lap and average lap times.
    Lead driver rankings are also calculated for both fastest and average lap times.

    Args:
        qualifying_ranks (dict): A dictionary containing qualifying rank data for races and sprints.
        downforce (int): The downforce level to filter by.

    Returns:
        dict: A dictionary containing DataFrames for different ranking categories:
            - "Lead Driver": DataFrame containing lead driver rankings for fastest and average lap times.
            - "Team": DataFrame containing team rankings for fastest and average lap times.
            - "Driver": DataFrame containing driver rankings for fastest and average lap times.
              Each DataFrame includes columns for Team/Driver, FL Average Rank, Avg pct of FL pace,
              AV Average Rank, and Avg pct of avg pace.
    """    
    
    print("Calculating pace rankings")
    #filter races by DF here
    race_ranks, sprint_ranks = filter_ranks_by_downforce(qualifying_ranks, downforce)
    # print(f"sprint ranks: {sprint_ranks}")
    
    # DFs for output
    driver_df = pd.DataFrame(columns=["Driver", "Team", "FL Average Rank", "Avg pct of FL pace", "AV Average Rank"])
    team_df = pd.DataFrame(columns=["Team", "FL Average Rank", "Avg pct of FL pace", "AV Average Rank"])
    lead_driver_df = pd.DataFrame(columns=["Team", "FL Average Rank", "Avg pct of FL pace", "AV Average Rank"])
    
    # setting up averaging lists for variabls.
    driver_names = DRIVERS.keys()
    team_names = CONSTRUCTORS.keys()
    
    driver_fl_ranks, driver_av_ranks, driver_fl_pct, driver_av_pct = {name: [] for name in driver_names}, {name: [] for name in driver_names}, {name: [] for name in driver_names}, {name: [] for name in driver_names}
    team_fl_ranks, team_av_ranks, team_fl_pct, team_av_pct = {name: [] for name in team_names}, {name: [] for name in team_names}, {name: [] for name in team_names}, {name: [] for name in team_names}
    lead_driver_fl_ranks, lead_driver_av_ranks, lead_driver_fl_pct, lead_driver_av_pct = {name: [] for name in team_names}, {name: [] for name in team_names}, {name: [] for name in team_names}, {name: [] for name in team_names}
    
    
    
    
    for race in race_ranks.keys():
        
        #if selection == "Driver":
        for index, row in race_ranks[race]["Fastest Laps"].iterrows():
            team = row['Driver']
            rank = row['FastestLapRank']
            pct = row['pct of pace']
            driver_fl_ranks[team].append(rank)
            driver_fl_pct[team].append(pct)
            
        for index, row in race_ranks[race]["Average Laps"].iterrows():
            team = row['Driver']
            rank = row['AverageLapRank']
            pct = row['pct of pace']
            driver_av_ranks[team].append(rank)  
            driver_av_pct[team].append(pct)   


        # if selection == "Team":
        for index, row in race_ranks[race]["Fastest Laps"].iterrows():
            team = row['Team']
            rank = row['FastestLapRank']
            pct = row['pct of pace']
            team_fl_ranks[team].append(rank)
            team_fl_pct[team].append(pct)


        for index, row in race_ranks[race]["Average Laps"].iterrows():
            team = row['Team']
            rank = row['AverageLapRank']
            pct = row['pct of pace']
            team_av_ranks[team].append(rank)
            team_av_pct[team].append(pct)
        
        
        # elif selection == "Lead Driver": 
        FL_LD_ranks = pick_lead_driver(race_ranks[race]["Fastest Laps"], selection="FL")
        AV_LD_ranks = pick_lead_driver(race_ranks[race]["Average Laps"], selection="AV")
        
        for index, row in FL_LD_ranks.iterrows(): #type: ignore
            team = row['Team']
            rank = row['FastestLapRank']
            pct = row['pct of pace']
            lead_driver_fl_ranks[team].append(rank)
            lead_driver_fl_pct[team].append(pct)
            
        for index, row in AV_LD_ranks.iterrows(): #type: ignore
            team = row['Team']
            rank = row['AverageLapRank']
            pct = row['pct of pace']
            lead_driver_av_ranks[team].append(rank)
            lead_driver_av_pct[team].append(pct)
        
        print(f"Calculated {race} averages")
        
        if race in SPRINTS:
            try:
                #if selection == "Driver":
                for index, row in sprint_ranks[race]["Fastest Laps"].iterrows():
                    team = row['Driver']
                    rank = row['FastestLapRank']
                    pct = row['pct of pace']
                    driver_fl_ranks[team].append(rank)
                    driver_fl_pct[team].append(pct)

                for index, row in sprint_ranks[race]["Average Laps"].iterrows():
                    team = row['Driver']
                    rank = row['AverageLapRank']
                    pct = row['pct of pace']
                    driver_av_ranks[team].append(rank)  
                    driver_av_pct[team].append(pct)   


                # if selection == "Team":
                for index, row in sprint_ranks[race]["Fastest Laps"].iterrows():
                    team = row['Team']
                    rank = row['FastestLapRank']
                    pct = row['pct of pace']
                    team_fl_ranks[team].append(rank)
                    team_fl_pct[team].append(pct)


                for index, row in sprint_ranks[race]["Average Laps"].iterrows():
                    team = row['Team']
                    rank = row['AverageLapRank']
                    pct = row['pct of pace']
                    team_av_ranks[team].append(rank)
                    team_av_pct[team].append(pct)


                # elif selection == "Lead Driver": 
                FL_LD_ranks = pick_lead_driver(sprint_ranks[race]["Fastest Laps"], selection="FL")
                AV_LD_ranks = pick_lead_driver(sprint_ranks[race]["Average Laps"], selection="AV")

                for index, row in FL_LD_ranks.iterrows(): #type: ignore
                    team = row['Team']
                    rank = row['FastestLapRank']
                    pct = row['pct of pace']
                    lead_driver_fl_ranks[team].append(rank)
                    lead_driver_fl_pct[team].append(pct)

                for index, row in AV_LD_ranks.iterrows(): #type: ignore
                    team = row['Team']
                    rank = row['AverageLapRank']
                    pct = row['pct of pace']
                    lead_driver_av_ranks[team].append(rank)
                    lead_driver_av_pct[team].append(pct)
                    
                print(f"Calculated {race} sprint averages")
            
            except Exception as e:
                print(f"Cannot calculate {race} sprint as Exception: {e}, This suggests timing data is skewed for this session.")

    
    # if selection == "Driver":
    for driver in driver_fl_ranks:
        team = get_constructor(driver)
        try:
            average = mean(driver_fl_ranks[driver])
            pct_avg = mean(driver_fl_pct[driver])
        except StatisticsError:
            continue
        driver_df.loc[len(driver_df)] = {"Driver": driver, "Team": team, "FL Average Rank": average, "Avg pct of FL pace": pct_avg} # type: ignore
    
    av_av_ranks = {driver: mean(ranks) for driver, ranks in driver_av_ranks.items() if ranks}
    av_av_pct = {driver: mean(pcts) for driver, pcts in driver_av_pct.items() if pcts}
    
    driver_df['AV Average Rank'] = [av_av_ranks.get(team, None) for team in driver_df['Driver']]
    driver_df['Avg pct of avg pace'] = [av_av_pct.get(team, None) for team in driver_df['Driver']]      
    
    # if selection == "Team":
    for team in team_fl_ranks:
        average = mean(team_fl_ranks[team])
        pct_avg = mean(team_fl_pct[team])
        team_df.loc[len(team_df)] = {"Team": team, "FL Average Rank": average, "Avg pct of FL pace": pct_avg} # type: ignore TBH I don't understand the error, but it works.
    
    av_av_ranks = {team: mean(ranks) for team, ranks in team_av_ranks.items() if ranks}
    av_av_pct = {team: mean(pcts) for team, pcts in team_av_pct.items() if pcts}
    
    team_df['AV Average Rank'] = [av_av_ranks.get(team, None) for team in team_df['Team']]
    team_df['Avg pct of avg pace'] = [av_av_pct.get(team, None) for team in team_df['Team']] 
        
    
    # if selection == "Lead Driver":
    new_rows = [{"Team": team, "FL Average Rank": mean(lead_driver_fl_ranks[team]), "Avg pct of FL pace": mean(lead_driver_fl_pct[team])} for team in lead_driver_fl_ranks]
    lead_driver_df = lead_driver_df.append(pd.DataFrame(new_rows), ignore_index=True) # type: ignore
    av_av_ranks = {team: mean(ranks) for team, ranks in lead_driver_av_ranks.items() if ranks}
    av_av_pct = {team: mean(pcts) for team, pcts in lead_driver_av_pct.items() if pcts}
    lead_driver_df['AV Average Rank'] = [av_av_ranks.get(team, None) for team in lead_driver_df['Team']] 
    lead_driver_df['Avg pct of avg pace'] = [av_av_pct.get(team, None) for team in lead_driver_df['Team']]


    driver_df = driver_df.sort_values('FL Average Rank').reset_index(drop=True) 
    team_df = team_df.sort_values('FL Average Rank').reset_index(drop=True)  
    lead_driver_df = lead_driver_df.sort_values('FL Average Rank').reset_index(drop=True)  


    output = {"Lead Driver": lead_driver_df, "Team": team_df, "Driver": driver_df}
    
    print(f"Completed races at downforce level {downforce}")
    return output


# res = Q_lap_pace_calculator(selection="Lead Driver", includes_anomalous_quali=False, downforce=3)

# # res = res.sort_values("Avg pct of avg pace").reset_index(drop=True)   

# print(res)
