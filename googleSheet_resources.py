### Import Libraries ###
import gspread
import urllib.request
import bs4 as bs
import pandas as pd
import threading as td
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import json
from google.oauth2 import service_account
import os
import fastf1

from secrets2.ss_key import sskey
from quali_analysis import scrape_all_quali_laps, return_df_q_rankings #, Q_lap_pace_calculator


fastf1.Cache.enable_cache(r"M:\Coding\F1DataAnalysis\FastF1Cache")

#from constants import *

#######################################################################################################################################################################################

###  Authorisation ###
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(ROOT_DIR, r"secrets2/creds.json")

# Load Google API Credentials
with open(CREDS) as source:
    info = json.load(source)
credentials = service_account.Credentials.from_service_account_info(
    info
)  # Check GDrive Creds

# Open Google Sheet and set pages as variables
gc = gspread.service_account(filename=CREDS)  # Check GSheets Creds
sh = gc.open_by_key(sskey)  # Get SpreadSheet
quali = sh.get_worksheet(0)

    
def record_quali_ranks():
    """
    Record qualifying lap rankings in a Google Sheets document.

    This function scrapes qualifying lap data, calculates pace rankings, and records the rankings
    in a Google Sheets document. Rankings for lead drivers, teams, and drivers are recorded
    separately on different parts of the sheet.

    Returns:
        None
    """
    print_coords = [2, 1]
    
    scrape = scrape_all_quali_laps()
    
    for i in range(10):
        
        data = return_df_q_rankings(scrape, i)
        
        set_with_dataframe(quali, data["Lead Driver"], row=print_coords[0], col=print_coords[1])
        print_coords[1]+=6
        set_with_dataframe(quali, data["Team"], row=print_coords[0], col=print_coords[1])
        print_coords[1]+=6
        set_with_dataframe(quali, data["Driver"], row=print_coords[0], col=print_coords[1])

        print("Sheet updated\n")
            
        
        print_coords[0]+=23
        print_coords[1]=1       

record_quali_ranks()