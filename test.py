import os



# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print(BASE_DIR)

# JsonFileName = '2021-08-15 16-18-18-x-babyy' + ".json"
# print(JsonFileName)
# # JsonFilePath = os.path.join(directory, JsonFileName)
# # JsonFilePath = rf"static/image uploads/end device 2/"+JsonFileName
# JsonFilePath = os.path.join(rf"static/image uploads/end device 2", JsonFileName)
# print(JsonFilePath)
# JsonFilePath = os.path.join(BASE_DIR, JsonFilePath)

# print(JsonFilePath)
# # Record to database the new image    

# if os.path.exists(JsonFilePath):
#     print("yes")
# else:
#     print("no")
print(os.environ.get('USER'))