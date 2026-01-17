import csv
import os
import math

folder_dir='Anomaly Detection\AnomalyDetectionTraining'
dir_list = os.listdir(folder_dir)
data = {}
data_headings = ['segment_id','average_speed', 'speed_stddev', 'sample_size']
for file_dir in dir_list:
    fields= []
    file_path=os.path.join(folder_dir, file_dir)
    with open (file_path, 'r') as csvfile :
        csvReader = csv.DictReader(csvfile)
        while True:
            for row in csvReader:
                segment_id = row['segment_id']
                avg_speed = row['average_speed']
                stddiv_speed = row['speed_stddev']
                sample_size = row['sample_size']
                if segment_id not in data:
                    data[segment_id]={}
                    data[segment_id]['average_speed']= {}
                    data[segment_id]['speed_stddev']= {}
                    data[segment_id]['sample_size']= {}
                    data[segment_id]['average_speed']= [avg_speed]
                    data[segment_id]['speed_stddev']= [stddiv_speed]
                    data[segment_id]['sample_size']= [sample_size]
                else:
                    data[segment_id]['average_speed'].append(avg_speed)
                    data[segment_id]['speed_stddev'].append(stddiv_speed)
                    data[segment_id]['sample_size'].append(sample_size)
            break

final_data= []
numerator=0
denominator=0
for key in data.keys():
    data_dict= data[key]
    avg_speed = data_dict['average_speed']
    stddiv_speed = data_dict['speed_stddev']
    sample_size = data_dict['sample_size']
    n= len(sample_size)
    sum_avg_speed=0
    for speed in avg_speed:
        sum_avg_speed+=float(speed)
    overall_mean= sum_avg_speed/n
    for i in range(n):
        if stddiv_speed[i]=='':
            stddiv_speed[i]=0
        denominator+=float(sample_size[i])
        numerator+= float(sample_size[i])*((float(stddiv_speed[i])**2)+((float(avg_speed[i])-(overall_mean))**2))
        
    overall_variance= numerator/denominator
    final_data.append({'segment_id':key, 'avg_speed': overall_mean, 'variance': overall_variance})

finald_csv_fields= ["segment_id", "avg_speed", "variance"]

file_name ='Anomaly Detection/Processed_CSV_Data.csv'


with open(file_name, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=finald_csv_fields)
    writer.writeheader()
    writer.writerows(final_data)







   


                    

            



