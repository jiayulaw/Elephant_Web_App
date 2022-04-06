# .\env\Scripts\activate
# locust
# http://0.0.0.0:8089


import time
from locust import HttpUser, task, between

# User account authentication is disabled for URLs used 
# in this load test at the time of testing.
# This was done to simplify testing methodology

class ElephantWebsiteTestUser(HttpUser):
    wait_time = between(0.5, 3.0)         
    @task(1)
    def test_about_us(self):
        # get 'test about us' HTML template (without user authentication)
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/about_us")
        for x in range(20):
            # get an image file from server to simulate traffic of image request when rendering HTML template
            # self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/thumbnail_bigpicture.png")
            
            self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/bigpicture.png")  