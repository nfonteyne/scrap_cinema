from conf import DATABASE_PATH
import json
from datetime import date, datetime
from helper import filter_movies_by_date

def load_data(input_path):
    with open(input_path, encoding='utf-8') as fh:
        data = json.load(fh)
    return data

if __name__ == "__main__":
    data = load_data(DATABASE_PATH)
    filtered_data = filter_movies_by_date(data, date.today())
    print(filtered_data)
    # print(type(date.today()))
