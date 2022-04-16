# Commands to execute load test:
# cd C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2
# .\env\Scripts\activate
# cd C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\tests\test-locust-load-test
# locust -f test-locust-thumbnail.py OR # locust

# Go to browser:
# http://localhost:8089/

# Notes:
# User authentication and role system are disabled 
# in web application for this load test.
# This was done to simplify testing methodology.

import time
from locust import HttpUser, task, between

class ElephantWebsiteTestUser(HttpUser):
    # set a random wait time after each task execution
    wait_time = between(1.0, 1.0)         
    @task(1)
    def load_image(self):
        for x in range(1):
            # Uncomment below to get thumbnailed image
            self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/thumbnail_bigpicture.png")

            # Uncomment below to get original size image
            # self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/bigpicture.png")  


