from PIL import Image

import os

# #read the image
# im = Image.open("static/img/bigpicture.png")

# # check filesize
# file_size = os.stat('static/img/bigpicture.png')
# print("Size of file :", file_size.st_size, "bytes")

# #create thumbnail
# MAX_SIZE = (100, 100)
# im.thumbnail(MAX_SIZE)
  
# # creating thumbnail
# im.save('pythonthumb.png')
# im.show()

# # compress img
# # im.save("Compressed_"+ "file.png", "PNG", optimize = True, quality = 1)

# #image pixel dimension
# print(im.size)
# print(im.size[0])
# print(im.size[1])



def check_and_create_img_thumbnail(dir, filename, max_size_in_kb):
    """ check_and_create_img_thumbnail(dir, filename, max_size_in_kb)
    If image size is greater than max_size_in_kb, then the algorithm will continue compressing the image until it is smaller than maximum size.
    The function returns the boolean indicating whether input file is greater than specified size and the path of the compressed image.
    In the event where input file is already smaller than speciied size, the function returns the same path as input."""
    #read the img
    path = dir + filename
    im = Image.open(path)
    # check filesize
    file_size = os.stat(path)
    print("Size of file :", file_size.st_size, "bytes")
    size_bool = 0
    while (int(file_size.st_size)/1024) > max_size_in_kb:
        size_bool = 1
        #create thumbnail
        MAX_SIZE = (im.size[0]*0.8, im.size[1]*0.8)
        im.thumbnail(MAX_SIZE)
        # creating thumbnail
        path = dir + "compressed_" + filename
        im.save(path)
        # im.show()
        file_size = os.stat(path)
        print("Compressed image to size:", file_size.st_size)

    return size_bool, path

print(check_and_create_img_thumbnail("static/img/bigpicture.png", 1000)[1])