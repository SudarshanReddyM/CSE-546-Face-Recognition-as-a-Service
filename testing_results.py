import sys
import os

path = "~/Desktop/CSE-546-Face-Recognition-as-a-Service/face_images_100/"
path = "/Users/dp/Desktop/CSE-546-Face-Recognition-as-a-Service/face_images_100/"
path = "/home/ec2-user/CSE-546-Face-Recognition-as-a-Service/face_images_100/"

def get_results():
    image_name = "test_"
    for i in range(0,100):
        if i < 10:
            input_path = image_name + "0" + str(i) + ".jpg"
        else:
            input_path = image_name + str(i) + ".jpg"
        if input_path in os.listdir(path):
            #print("/usr/bin/python3 /home/ec2-user/face_recognition.py " + path + input_path + " >> /home/ec2-user/output.txt")
            os.system("/usr/bin/python3 /home/ec2-user/face_recognition.py " + path + input_path + " >> /home/ec2-user/output.txt") 
            # print(input_path)
        # print("$$$", input_path)
        
if __name__=="__main__":
    get_results()
