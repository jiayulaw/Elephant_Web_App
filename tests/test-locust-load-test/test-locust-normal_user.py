# Commands to execute load test:
# cd C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2
# .\env\Scripts\activate
# cd C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\tests\test-locust-load-test
# locust -f test-locust-normal_user.py 

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
    wait_time = between(1.0,5.0)
    @task(1)
    def login_page(self):
        # get login page HTML template 
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/login")

    @task(1)
    def device_monitoring_page(self):
        # get device monitoring page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/device_monitoring") 
        
    @task(1)
    def view_image_page(self):
        # get image view page HTML template 
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/display_image")

        # simulate image filter HTML form submission 
        # from 2021-09-01 02:04:00 to 2022-04-15 02:04:00, any source, any type
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/display_image?station=any&detection_type=any&from=2021-09-01+02%3A04&to=2022-04-15+02%3A04%3A00")
        # get image files from server to simulate traffic of image request when rendering HTML template
        for x in range(800):
            self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/image%20uploads/end%20device%203/2021-06-15%2016-18-18-x-elephant.jpg")

    @task(1)
    def upload_image_page(self):
        # get image upload page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/data_center/upload_image") 

    @task(1)
    def analytics_page(self):
        # get analytics page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/analytics")

    @task(1)
    def server_activity_page(self):
        # get server activity page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/admin/home")

    @task(1)
    def user_management_page(self):
        # get user management page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/admin/admin_manage")

    @task(1)
    def account_creation_page(self):
        # get account creation page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/admin/register")

    @task(1)
    def about_us_page(self):
        # get 'about us' page HTML template 
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/about_us")
        # get image files from server to simulate traffic of image request when rendering HTML template
        for x in range(5):
            self.client.get("https://d3m318b1ejw1x6.cloudfront.net/static/img/thumbnail_bigpicture.png")

    @task(1)
    def debugger_page(self):
        # get account debugger page HTML template
        self.client.get("https://d3m318b1ejw1x6.cloudfront.net/debug")


        