CONSTRUCTORS = {
    "Red Bull Racing": ("VER", "PER"),
    "Aston Martin": ("ALO", "STR"),
    "Mercedes": ("HAM", "RUS"),
    "Ferrari": ("LEC", "SAI"),
    "Alfa Romeo": ("BOT", "ZHO"),
    "Alpine": ("GAS", "OCO"),
    "Williams": ("ALB", "SAR"),
    "AlphaTauri": ("DEV", "TSU", "RIC"),
    "Haas F1 Team": ("HUL", "MAG"),
    "McLaren": ("NOR", "PIA")
}

def get_constructor(driver):
    for constructor, drivers in CONSTRUCTORS.items():
        if driver in drivers:
            return constructor
    return None

DRIVERS = {
    "VER": "Verstappen",
    "PER": "Perez",
    "LEC": "Leclerc",
    "SAI": "Sainz",
    "ALO": "Alonso",
    "HAM": "Hamilton",
    "RUS": "Russell",
    "OCO": "Ocon",
    "STR": "Stroll",
    "NOR": "Norris",
    "GAS": "Gasly",
    "HUL": "Hulkenburg",
    "ZHO": "Zhou",
    "MAG": "Magnussen",
    "BOT": "Bottas",
    "ALB": "Albon",
    "PIA": "Piastri",
    "TSU": "Tsunoda",
    "DEV": "De Vries",
    "SAR": "Sargeant",
    "RIC": "Ricciardo"
}

RACES = [
    'Sakhir',
    'Jeddah',
    'Melbourne',
    'Baku',
    'Miami',
    'Monaco',
    'Barcelona',
    'Montréal',
    'Spielberg',
    'Silverstone',
    'Budapest',
    'Spa-Francorchamps',
    'Zandvoort',
    'Monza',
    'Marina Bay',
    'Suzuka',
    'Lusail',
    'Austin',
    'Mexico City',
    'São Paulo',
    'Las Vegas',
    'Yas Island'
]

SPRINTS = [
    "Baku",
    "Spielberg",
    "Spa-Francorchamps",
    "Lusail",
    "Austin",
    "São Paulo"
]

RACE_DF_RATING = {
    'Sakhir': 3,
    'Jeddah': 2,
    'Melbourne': 4,
    'Baku': 1,
    'Miami': 2,
    'Monaco': 5,
    'Barcelona': 4,
    'Montréal': 2,
    'Spielberg': 3,
    'Silverstone': 4,
    'Budapest': 5,
    'Spa-Francorchamps': 2,
    'Zandvoort': 4,
    'Monza': 1,
    'Marina Bay': 5,
    'Suzuka': 4,
    'Lusail': 4,
    'Austin': 3,
    'Mexico City': 5,
    'São Paulo': 4,
    'Las Vegas': 1,
    'Yas Island': 3
}

DF_RACES = {
    1: ['Baku', 'Monza', 'Las Vegas'],
    2: ['Jeddah', 'Miami', 'Montréal', 'Spa-Francorchamps'],
    3: ['Sakhir', 'Spielberg', 'Austin', 'Yas Island'],
    4: ['Melbourne', 'Barcelona', 'Silverstone', 'Zandvoort', 'Suzuka', 'Lusail', 'São Paulo'],
    5: ['Monaco', 'Budapest', 'Marina Bay', 'Mexico City']
}

DF_RACES = {
    1: ['Baku', 'Monza', 'Las Vegas'],
    2: ['Jeddah', 'Miami', 'Montréal', 'Spa-Francorchamps'],
    3: ['Sakhir', 'Spielberg', 'Austin', 'Yas Island'],
    4: ['Melbourne', 'Barcelona', 'Silverstone', 'Zandvoort', 'Suzuka', 'Lusail', 'São Paulo'],
    5: ['Monaco', 'Budapest', 'Marina Bay', 'Mexico City'],
    
        #1+2
    6: ['Baku', 'Jeddah', 'Miami', 'Montréal', 'Spa-Francorchamps', 'Monza', 'Las Vegas'],
        #2+3
    7: ['Sakhir', 'Jeddah', 'Miami', 'Montréal', 'Spielberg', 'Spa-Francorchamps', 'Austin', 'Yas Island'],
        #3+4
    8: ['Sakhir', 'Melbourne', 'Barcelona', 'Spielberg', 'Silverstone', 'Zandvoort', 'Suzuka', 'Lusail', 'Austin', 'São Paulo', 'Yas Island'],
        #4+5
    9: ['Melbourne', 'Monaco', 'Barcelona', 'Silverstone', 'Budapest', 'Zandvoort', 'Marina Bay', 'Suzuka', 'Lusail', 'Mexico City', 'São Paulo']
}



TRACK_SECTOR_DF = {}