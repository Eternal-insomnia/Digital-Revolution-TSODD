import pandas as pd


# Функция для расчета населения зданий
def calculate_population(building):
    building_type = building['Type']
    apartments = building.get('Apartments', 0)
    if building_type == "Жилые дома":
        purpose = building.get('Purpose', 0)
        if purpose == "Таунхаус" and pd.isna(apartments):
            return 4
        elif purpose == "Малоэтажный жилой дом" and pd.isna(apartments):
            return 4
        elif purpose == "Общежитие" and pd.isna(apartments):
            return 4
        elif pd.isna(apartments):
            return 0
        else:
            return apartments * 3
    elif building_type == "Частные дома":
        return 4


    return 0  # Для прочих типов


def get_population(buildings):

    population_dict = {}

    # Расчет населения для всех зданий и логирование
    for key, bldg in buildings.items():
        for idx, building in bldg.iterrows():
            # Определение HouseId
            house_id = building.get('HouseId', f"{key}_{idx}")
            population = calculate_population(building)
            bldg.at[idx, 'Population'] = population
            population_dict[house_id] = population


    # Определяем процент людей в час пик
    peak_ratio = 0.7

    return population_dict