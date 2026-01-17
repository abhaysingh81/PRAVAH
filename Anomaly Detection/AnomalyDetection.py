
import numpy as np
#from scipy.stats import multivariate_normal
import csv

class AnomalyDetection:

    def __init__(self, dataframe):
        self.time_set_name= dataframe['time_Set_name']
        self.speed_stddev = dataframe['speed_stddev']
        self.average_speed= dataframe['average_speed']
        self.segment_id= dataframe['segment_id']        

    def estimate_gaussian_params(self): 
        file_path= 'Anomaly Detection\Processed_CSV_Data.csv'
        with open (file_path, 'r') as csvfile :
            csvReader = csv.DictReader(csvfile)
            for row in csvReader:
                if self.segment_id==row['segment_id']:
                    mu=row['avg_speed']
                    var=row['variance']
        # X= np.array(self.average_speed)
        # m, n = X.shape
        # mu = 1 / m * np.sum(X, axis = 0)
        # var = 1 / m * np.sum((X - mu) ** 2, axis = 0)  
        return mu, var
    
    def univariate_gaussian( x, mean, variance):
        univariate_normal= ((1 / np.sqrt(2 * np.pi * variance)) * np.exp(-(x - mean)**2 / (2 * variance)))
        return univariate_normal

    def select_threshold(x_train, mean, variance):
        p_train = AnomalyDetection.univariate_gaussian(x_train, mean, variance)
        epsilon = np.percentile(p_train, 1)
        return epsilon

    def outlier_detection(self, x):
        mean, variance = AnomalyDetection.estimate_gaussian_params
        p = AnomalyDetection.univariate_gaussian(x, mean, variance)
        outliers = p < self.epsilon
        return outliers #Bool Value


print(AnomalyDetection.univariate_gaussian())