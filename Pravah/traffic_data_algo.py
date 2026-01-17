import time
from data_continuity_adder import line_definer_10, line_definer_20


alpha_t = {'838633406':0, '838495888':0, '838633634':0, '838495943':0}
beta_t = {'838633406':0, '838495888':0, '838633634':0, '838495943':0}
alpha_t_plus_30 = {'838633406':0, '838495888':0, '838633634':0, '838495943':0}
beta_t_plus_30 = {'838633406':0, '838495888':0, '838633634':0, '838495943':0}
time_default = 30

alpha_t_values = list(alpha_t.values())

alpha_t_plus_10 = [line_definer_10(i) for i in alpha_t_values]
alpha_t_plus_20 = [line_definer_20(i) for i in alpha_t_values]




class TrafficLightManager:
    def __init__(self, alpha_t, beta_t, alpha_t_plus_30, beta_t_plus_30):
        self.alpha_t = alpha_t
        self.beta_t = beta_t
        self.alpha_t_plus_30 = alpha_t_plus_30
        self.beta_t_plus_30 = beta_t_plus_30
        self.alpha_t_updating = alpha_t
        self.alpha_t_plus_30_updating = alpha_t_plus_30

    def primary_condition_checker(self, alpha):
        if alpha>0.5:
            time=40
            return time
        elif alpha > 0.7:
            time = 50
            return time

        elif alpha > 0.9:
            time = 60
            return time
        else:
            return 30      

    def main_loop(self, index_of_best):

        if self.beta_t[index_of_best] <= 0.5 and self.beta_t_plus_30[index_of_best] <0.8:
                time_out = self.primary_condition_checker(index_of_best)
                self.alpha_t_updating.pop()
                return time_out
        else:
            return False
        


traffic_list_manager_object = TrafficLightManager(alpha_t=list(alpha_t.values()), alpha_t_plus_30=list(alpha_t_plus_30.values()), beta_t=list(beta_t.values()), beta_t_plus_30=list(beta_t_plus_30.values()))

sorted_alpha_t = sorted(alpha_t)
sorted_alpha_t_plus_30 = sorted(alpha_t_plus_30)

order_of_green = []

while True:
    pass


            


            
            



        


    


    
