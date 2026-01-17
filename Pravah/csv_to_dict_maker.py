import csv
from collections import defaultdict

def output_csv_file(file_name):

    def read_csv_to_dict_of_lists(filename):
       
        data_dict = defaultdict(list)
        
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                for key, value in row.items():
                    data_dict[key].append(value)
        return dict(data_dict)


    file_data = read_csv_to_dict_of_lists(filename=file_name)
    return file_data