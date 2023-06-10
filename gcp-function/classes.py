from dotenv import load_dotenv
import os

load_dotenv()

factory_coord = os.getenv("FACTORY_GEO_COORD") 

class Installer:
    def __init__(self,id):
        
        self.id = id
        self.avail = True
        self.geo_coord = factory_coord
        self.time_spent = 0
        self.date = None
        self.start_time = None
        self.end_time = None
    
    def get_last_job_end_time():
        return self.end_time
        
    def reset_time_spent(self):
        self.time_spent = 0
        
    def reset_job(self):
        self.job_id = None
        self.start_time = None
        self.end_time = None
        
    def reset_location(self):
        self.geo_coord = factory_coord
    
    def overtime(self):
        if self.time_spent >= 480:
            return True
        else:
            return False

class Job:
    def __init__(self,job_coord,exp_job_time,est_ins_date,num_installers):
        self.start_time = None
        self.end_time = None
        self.job_location = job_coord
        self.exp_job_time = exp_job_time
        self.deadline = est_ins_date
        self.num_installers = num_installers
        self.review = False
        self.worker_ids = []