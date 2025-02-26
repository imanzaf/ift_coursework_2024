#this will be called from jenkins
from datetime import datetime

date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("this is from jenkins_test.py at " + date_str)
