import os
import sys
# import itertools


# results_path = "/Users/dp/Desktop/CSE-546-Face-Recognition-as-a-Service/expected_results.csv"
# output_path = "/Users/dp/Desktop/CSE-546-Face-Recognition-as-a-Service/output.txt"

results_path = "/home/ec2-user/CSE-546-Face-Recognition-as-a-Service/expected_results.csv"
output_path = "/home/ec2-user/CSE-546-Face-Recognition-as-a-Service/output.txt"
def validator():
    counter_true = 0
    counter_false = 0
    with open(results_path, "r") as file, open(output_path, "r") as f1:
        next(file)
        for expected, output in zip(file, f1):
            if expected.split(",")[1] == output:
                counter_true +=1
                # print(True)
            elif expected.split(",")[1] == output.rstrip():
                counter_true += 1
            else:
                counter_false += 1
                print(False, expected.split(",")[1],"**", output) 
    return counter_true,counter_false
            
            
if __name__=="__main__":
    print(validator())