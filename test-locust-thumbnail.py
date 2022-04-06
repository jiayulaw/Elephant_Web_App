

        
import time
from locust import HttpUser, task, between

# User account authentication is disabled for URLs used 
# in this load test at the time of testing.
# This was done to simplify testing methodology

class ElephantWebsiteTestUser(HttpUser):
    wait_time = between(0.5, 3.0)
    
    # def on_start(self):
    #     """ on_start is called when a Locust start before any task is scheduled """
    #     pass

    # def on_stop(self): -
    #     """ on_stop is called when the TaskSet is stopping """
    #     pass

    @task(1) # number inside bracket is the weight for each task
    def view_image(self):
        # go to view image page
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/display_image")
        # submit image filter form and get HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/display_image?station=any&detection_type=any&from=2021-03-08+21%3A56&to=2022-04-04+21%3A56%3A00&timezone=")
        for x in range(6):
            # get an image file from server to simulate traffic of image request when rendering HTML template
            self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/image%20uploads/end%20device%203/2022-03-25%2012-06-54-x-elephant.jpeg")
              


    @task(1)
    def test_about_us(self):
        # get 'test about us' HTML template (without user authentication)
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/about_us")
        # get an image file from server to simulate traffic of image request when rendering HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/thumbnail_bigpicture.png")
        
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/bigpicture.png")  

        
        