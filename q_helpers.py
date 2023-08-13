import pandas as pd
import numpy as np
from functools import reduce

# from sklearn.neighbors import NearestNeighbors
# from sklearn.ensemble import IsolationForest

from constants import *

#### Helper functions for Quali analysis


def check_average_laps(df, driver):
    df = df[df["Driver"]==driver]
    print(df)

# Three Sigma rule currently eliminates relevant efforts as a large anomalous result will affect 3*StDev
# Using IQR instead and only removing the upper bound.

def filter_anomalous_Q_laps(Q_session):
    """
    Filter and identify anomalies in Qualifying session lap data.

    This function takes a Qualifying session object `Q_session` and performs the following steps:
    1. Removes irrelevant data from the Quali Session.
    2. Identifies accurate laps based on criteria.
    3. Removes lap times that are considered anomalies.
    4. Identifies drivers who did not set competitive laps.
    
    Args:
        Q_session: A Qualifying session object containing lap data.

    Returns:
        tuple: A tuple containing the following elements:
            - filtered_laps (DataFrame): A DataFrame containing lap data after removing anomalies.
            - poor_q_ranks (dict or None): A dictionary mapping poor qualifying drivers to their positions
              or None if all drivers set competitive laps.
    """
    
    k=2 # ************* Edit to adjust cutoff.
    
    
    relevant_data = Q_session.laps[["Driver", "Team", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time", "TyreLife", "IsAccurate", "Deleted"]]
    #IsAccurate removes inlaps and outlaps and some other non fast laps
    #Deleted records whether a lap time is deleted for track limits.
    accurate_laps = relevant_data[(relevant_data["IsAccurate"] == True) & (relevant_data["Deleted"] == False)]
    
    
    # Not all anomalies are caught so remove laptimes that are larger than 3 times the Std dev. (None should be smaller)
    # laptime_anomaly_threshold = Q_session.results["Q1"].median() + Q_session.results["Q1"].std()
    q1_laptimes = Q_session.results["Q1"].values
    
    # Calculate the first quartile (Q1) and third quartile (Q3)
    q1 = np.percentile(q1_laptimes, 25)
    q3 = np.percentile(q1_laptimes, 75)

    # Calculate the IQR (Interquartile Range)
    iqr = q3 - q1
    laptime_anomaly_threshold = q3 + k * iqr
    
    nanoseconds = pd.Timedelta(laptime_anomaly_threshold).total_seconds() * 1e9
    # Convert nanoseconds to minutes, seconds, and milliseconds
    minutes, seconds = divmod(nanoseconds / 1e9, 60)
    seconds, milliseconds = divmod(seconds, 1)
    milliseconds *= 1000

    # Format the time as mm:ss.ms
    formatted_time = "{:02d}:{:02d}.{:03d}".format(int(minutes), int(seconds), int(milliseconds))
    print(f"Cutoff laptime: {formatted_time}")

    # Remove anomalies
    filtered_laps = accurate_laps[accurate_laps['LapTime'] <= laptime_anomaly_threshold]
    
    # removed_laptimes = accurate_laps[accurate_laps['LapTime'] > laptime_anomaly_threshold]
    # print("Removed Lap Times:")
    # print(removed_laptimes)
    print(f"Removed {len(accurate_laps.values) - len(filtered_laps.values)} laps")
    
   
    nc_drivers = [value for value in DRIVERS.keys() if value not in filtered_laps["Driver"].values]
    poor_q_drivers = [driver for driver in nc_drivers if driver in Q_session.laps["Driver"].values]
    
    if poor_q_drivers: 
        print(f"The following drivers did not set a competitive lap: {poor_q_drivers}")
        poor_q_ranks = Q_session.results[["Abbreviation", "Position"]].set_index('Abbreviation')['Position'].loc[poor_q_drivers].to_dict()
        print(poor_q_ranks)
    
    else: poor_q_ranks = None
    
    # We still want to give a rank
    # take results from quali and pass through to ranker.
    # after ranking we can add them to bottom with their Q laps, no times and ranks given.
    
    # def map_positions(df, values):
    #     return df.set_index('Abbreviation')['Position'].loc[values].to_dict()
    

    return (filtered_laps, poor_q_ranks)



def return_ranked_Q_laps(df, poor_q_ranks=None):
    """
    Rank drivers based on qualifying lap data.

    This function takes a DataFrame `df` containing qualifying lap data and calculates ranks for drivers' fastest and
    average lap times as well as sector times. It also provides the percentage off pace compared to the fastest lap.

    Args:
        df (DataFrame): A DataFrame containing qualifying lap data for drivers.
        poor_q_ranks (dict, optional): A dictionary mapping drivers with poor qualifying laps to their positions.
                                       Defaults to None.

    Returns:
        dict: A dictionary containing two DataFrames:
            - "Fastest Laps": DataFrame with ranks for fastest lap times and sector times.
            - "Average Laps": DataFrame with ranks for average lap times and sector times.
              Both DataFrames include columns for Driver, Team, lap times, ranks, and percentage off pace.
              If `poor_q_ranks` is provided, drivers with poor qualifying laps are included with appropriate data.
    """
    
    df['LapTime'] = pd.to_timedelta(df['LapTime'])

    # Find the fastest lap time for each driver
    fastest_lap_time = df.groupby(['Driver', 'Team'])['LapTime'].min().reset_index()
    fastest_lap_time.rename(columns={'LapTime': 'FastestLapTime'}, inplace=True)
    
    # To correct for ValueError generated by poor quali laps being excluded
    tot_relevant_drivers = len(fastest_lap_time.values) + 1

    # Sort the DataFrame by fastest lap time and assign ranks
    df_sorted_by_fastest_lap = fastest_lap_time.sort_values('FastestLapTime').reset_index(drop=True)
    df_sorted_by_fastest_lap["FastestLapRank"] = range(1, tot_relevant_drivers)

    # Find the fastest sector1 time for each driver
    fastest_sector1_time = df.groupby(['Driver', 'Team'])['Sector1Time'].min().reset_index()
    fastest_sector1_time.rename(columns={'Sector1Time': 'FastestSector1Time'}, inplace=True)

    # Sort the DataFrame by fastest sector1 time and assign ranks
    df_sorted_by_fastest_sector1 = fastest_sector1_time.sort_values('FastestSector1Time').reset_index(drop=True)
    df_sorted_by_fastest_sector1["FastestSector1Rank"] = range(1, tot_relevant_drivers)

    # Find the fastest sector2 time for each driver
    fastest_sector2_time = df.groupby(['Driver', 'Team'])['Sector2Time'].min().reset_index()
    fastest_sector2_time.rename(columns={'Sector2Time': 'FastestSector2Time'}, inplace=True)

    # Sort the DataFrame by fastest sector2 time and assign ranks
    df_sorted_by_fastest_sector2 = fastest_sector2_time.sort_values('FastestSector2Time').reset_index(drop=True)
    df_sorted_by_fastest_sector2["FastestSector2Rank"] = range(1, tot_relevant_drivers)

    # Find the fastest sector3 time for each driver
    fastest_sector3_time = df.groupby(['Driver', 'Team'])['Sector3Time'].min().reset_index()
    fastest_sector3_time.rename(columns={'Sector3Time': 'FastestSector3Time'}, inplace=True)

    # Sort the DataFrame by fastest sector3 time and assign ranks
    df_sorted_by_fastest_sector3 = fastest_sector3_time.sort_values('FastestSector3Time').reset_index(drop=True)
    df_sorted_by_fastest_sector3["FastestSector3Rank"] = range(1, tot_relevant_drivers)
    
    # Fastest Lap Rank df:
    fl_ranks = pd.merge(fastest_lap_time, fastest_sector1_time, on=['Driver', 'Team'])
    fl_ranks = pd.merge(fl_ranks, fastest_sector2_time, on=['Driver', 'Team'])
    fl_ranks = pd.merge(fl_ranks, fastest_sector3_time, on=['Driver', 'Team'])
    fl_ranks = pd.merge(fl_ranks, df_sorted_by_fastest_lap[['Driver', 'FastestLapRank']], on=['Driver'])
    fl_ranks = pd.merge(fl_ranks, df_sorted_by_fastest_sector1[['Driver', 'FastestSector1Rank']], on=['Driver'])
    fl_ranks = pd.merge(fl_ranks, df_sorted_by_fastest_sector2[['Driver', 'FastestSector2Rank']], on=['Driver'])
    fl_ranks = pd.merge(fl_ranks, df_sorted_by_fastest_sector3[['Driver', 'FastestSector3Rank']], on=['Driver'])
    
    fl_ranks = fl_ranks.sort_values('FastestLapRank').reset_index(drop=True)
    
    fastest_lap_time = pd.to_timedelta(fl_ranks.loc[0, "FastestLapTime"])  # type: ignore
    fl_ranks["pct of pace"] = ((pd.to_timedelta(fl_ranks["FastestLapTime"]) - fastest_lap_time) / fastest_lap_time * 100)
    

    # Calculate average lap time for each driver
    average_lap_time = df.groupby(['Driver', 'Team'])['LapTime'].mean().reset_index()
    average_lap_time.rename(columns={'LapTime': 'AverageLapTime'}, inplace=True)

    # Sort the DataFrame by average lap time and assign ranks
    df_sorted_by_average_lap = average_lap_time.sort_values('AverageLapTime').reset_index(drop=True)
    df_sorted_by_average_lap["AverageLapRank"] = range(1, tot_relevant_drivers)

    # Calculate average sector1 time for each driver
    average_sector1_time = df.groupby(['Driver', 'Team'])['Sector1Time'].mean().reset_index()
    average_sector1_time.rename(columns={'Sector1Time': 'AverageSector1Time'}, inplace=True)

    # Sort the DataFrame by average sector1 time and assign ranks
    df_sorted_by_average_sector1 = average_sector1_time.sort_values('AverageSector1Time').reset_index(drop=True)
    df_sorted_by_average_sector1["AverageSector1Rank"] = range(1, tot_relevant_drivers)

    # Calculate average sector2 time for each driver
    average_sector2_time = df.groupby(['Driver', 'Team'])['Sector2Time'].mean().reset_index()
    average_sector2_time.rename(columns={'Sector2Time': 'AverageSector2Time'}, inplace=True)

    # Sort the DataFrame by average sector2 time and assign ranks
    df_sorted_by_average_sector2 = average_sector2_time.sort_values('AverageSector2Time').reset_index(drop=True)
    df_sorted_by_average_sector2["AverageSector2Rank"] = range(1, tot_relevant_drivers)

    # Calculate average sector3 time for each driver
    average_sector3_time = df.groupby(['Driver', 'Team'])['Sector3Time'].mean().reset_index()
    average_sector3_time.rename(columns={'Sector3Time': 'AverageSector3Time'}, inplace=True)

    # Sort the DataFrame by average sector3 time and assign ranks
    df_sorted_by_average_sector3 = average_sector3_time.sort_values('AverageSector3Time').reset_index(drop=True)
    df_sorted_by_average_sector3["AverageSector3Rank"] = range(1, tot_relevant_drivers)
    
    
    # Average Lap Rank df:
   
    av_ranks = pd.merge(average_lap_time, average_sector1_time, on=['Driver', 'Team'])
    av_ranks = pd.merge(av_ranks, average_sector2_time, on=['Driver', 'Team'])
    av_ranks = pd.merge(av_ranks, average_sector3_time, on=['Driver', 'Team'])
    av_ranks = pd.merge(av_ranks, df_sorted_by_average_lap[['Driver', 'AverageLapRank']], on=['Driver'])
    av_ranks = pd.merge(av_ranks, df_sorted_by_average_sector1[['Driver', 'AverageSector1Rank']], on=['Driver'])
    av_ranks = pd.merge(av_ranks, df_sorted_by_average_sector2[['Driver', 'AverageSector2Rank']], on=['Driver'])
    av_ranks = pd.merge(av_ranks, df_sorted_by_average_sector3[['Driver', 'AverageSector3Rank']], on=['Driver'])

    av_ranks = av_ranks.sort_values('AverageLapRank').reset_index(drop=True)
    
    # Calculate pct off pace
    fastest_lap_time = pd.to_timedelta(av_ranks.loc[0, "AverageLapTime"])  # type: ignore
    av_ranks["pct of pace"] = ((pd.to_timedelta(av_ranks["AverageLapTime"]) - fastest_lap_time) / fastest_lap_time * 100)
    
    # # Reorder the columns as requested
    av_ranks = av_ranks[[
        'Driver', 'Team',  
        'AverageLapTime', 'AverageLapRank', "pct of pace",
        'AverageSector1Time', "AverageSector1Rank", 
        'AverageSector2Time', "AverageSector2Rank", 
        'AverageSector3Time', "AverageSector3Rank"
    ]]
    
    #av_ranks = av_ranks.set_index("Driver")
    
    fl_ranks = fl_ranks[[
        'Driver', 'Team',  
        'FastestLapTime', 'FastestLapRank', "pct of pace",
        'FastestSector1Time', "FastestSector1Rank",
        'FastestSector2Time', "FastestSector2Rank",
        'FastestSector3Time', "FastestSector3Rank"
    ]]

    #fl_ranks = fl_ranks.set_index("Driver")
    
    # If want to include failed qualis then can do. 
    # If not then this is skipped (when comparing the car we do not want to take into account when the maximum of the car was not reached)
    
    if poor_q_ranks:
        for driver in poor_q_ranks:
            fldata = {
                'Driver': driver,
                'Team':get_constructor(driver),  
                'FastestLapTime': None,
                'FastestLapRank': poor_q_ranks[driver], 
                'FastestSector1Time': None,
                "FastestSector1Rank": None,
                'FastestSector2Time': None,
                "FastestSector2Rank": None,
                'FastestSector3Time': None,
                "FastestSector3Rank": None
            }
            
            avdata = {
                'Driver': driver,
                'Team':get_constructor(driver),  
                'AverageLapTime': None,
                'AverageLapRank': poor_q_ranks[driver], 
                'AverageSector1Time': None,
                "AverageSector1Rank": None,
                'AverageSector2Time': None,
                "AverageSector2Rank": None,
                'AverageSector3Time': None,
                "AverageSector3Rank": None
            }
            
            fl_ranks.loc[len(fl_ranks)] = fldata #type: ignore
            av_ranks.loc[len(av_ranks)] = avdata #type: ignore

    return {"Fastest Laps": fl_ranks, "Average Laps": av_ranks}


def pick_lead_driver(df, selection = "FL" or "AV"):
    """
    Pick the lead driver from each team based on qualifying lap data.

    This function takes a DataFrame `df` containing qualifying lap data and selects the lead driver for each team
    based on either fastest lap or average lap time.

    Args:
        df (DataFrame): A DataFrame containing ranked qualifying lap data for drivers.
        selection (str, optional): Selection criteria for picking the lead driver.
                                   Choose between "FL" (Fastest Lap) or "AV" (Average Lap).
                                   Defaults to "FL".

    Returns:
        DataFrame: A DataFrame with the lead drivers for each team based on the specified selection criteria.
                   The DataFrame includes updated ranks and lap times according to the chosen selection.
    """
    
    if selection == "FL":
        result = df.groupby('Team').apply(lambda x: x.drop(x['FastestLapRank'].idxmax()) if len(x) > 1 else x)
        result = result.sort_values('FastestLapTime').reset_index(drop=True)
        result['FastestLapRank'] = result['FastestLapTime'].rank(method='min')
        # result['FastestSector1Rank'] = result['FastestSector1Time'].rank(method='min')
        # result['FastestSector2Rank'] = result['FastestSector2Time'].rank(method='min')
        # result['FastestSector3Rank'] = result['FastestSector3Time'].rank(method='min')
        return result
        
    if selection == "AV":
        result = df.groupby('Team').apply(lambda x: x.drop(x['AverageLapRank'].idxmax()) if len(x) > 1 else x)
        result = result.sort_values('AverageLapTime').reset_index(drop=True)
        result['AverageLapRank'] = result['AverageLapTime'].rank(method='min')
        return result


