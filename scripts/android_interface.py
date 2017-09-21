#!/usr/bin/env python

__author__ = "Andrea Vanzo"

###  Imports  ###

# ROS imports
import rospy
import roslib

# ROS msg and srv imports
from std_msgs.msg import Int8

# Python Libraries
import sys
import socket
import aiml
import datetime
import json

###  Variables  ###
k = aiml.Kernel()
conn = None
time = datetime.datetime.now()

###  Classes  ###
class AndroidInterface(object):
    cmd_action = 'INIT'
    ###  Interaction Variables  ###
    UserID = 0
    reply = ''
    collaboration = ''

    def __init__(self):
        global conn

        HOST = ''
        #PORT = 9001
        #BASE_PATH = '/Volumes/MacintoshHDD/projects/PSint_controller/dialogue_interface/scripts/KB/'
        PORT = rospy.get_param('/android_interface/server_port')
        BASE_PATH = rospy.get_param('/android_interface/aiml_base_path')
        
        #######
        # ROBOT_NAME = rospy.get_param('/android_interface/robot_name')
        # self.UserID = rospy.get_param('android_interface/user_id')
        #######

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print 'Socket created'
            try:
                s.bind((HOST, PORT))
            except socket.error as msg:
                print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                sys.exit()
            print 'Socket bind complete'
            s.listen(10)

            print 'Socket now listening on port ' + str(PORT)
            k.learn(BASE_PATH + "en/dialogue_manager.aiml")
            k.learn(BASE_PATH + "en/lexicon.aiml")
            k.learn(BASE_PATH + "en/outside.aiml")
            #k.learn(BASE_PATH + "en/corridor.aiml")
            #k.learn(BASE_PATH + "en/coffee_machine.aiml")
            #k.learn(BASE_PATH + "en/inside_elevator.aiml")
            #k.learn(BASE_PATH + "en/outside_elevator.aiml")
            #k.learn(BASE_PATH + "en/printer.aiml")
            # k.respond(rospy.get_param('/android_interface/environment'))
            k.respond("OUTSIDE")


            rospy.init_node('dialogue_interface_node', anonymous=True)
            rospy.Subscriber("/cmd_action", Int8, self.cmdActionCb, queue_size=1)

            currentFragment = ''
            while not rospy.is_shutdown():
                print "Waiting for connection on port " + str(PORT)
                conn, addr = s.accept()
                print 'Connected with ' + addr[0] + ':' + str(addr[1])
                while not rospy.is_shutdown():
                    data = conn.recv(2048)  # 512
                    print 'Received: ' + data
                    if len(data) > 0:
                        if data[0] == "{":
                            print "User[", self.UserID, "]  log store "
                            f = open(BASE_PATH + '/jhri17_users_log_'
                                     + str(time.year) + '-'
                                     + str(time.month) + '-'
                                     + str(time.day) + '-'
                                     + str(time.hour) + '-'
                                     + str(time.minute)
                                     + '.txt', 'a')
                            f.write('UserId: ' + str(self.UserID) + ' =\n')
                            f.write('Answer: ' + self.collaboration + '\n')
                            f.write(data)
                            f.write('UserId: ' + str(self.UserID) +
                                    ' ----------------\n\n')
                            f.close()
                            self.UserID = self.UserID + 1

                    if data and not data.isspace():
                        if not data:
                            continue
                        if "KEEP_AWAKE" in data:
                            data = data.replace("KEEP_AWAKE", "")
                            continue
                            #if len(data) == 0:
                            #    continue
                        if '$' in data:
                            currentFragment = data[1:-1]
                            print 'You selected the ' + currentFragment + ' fragment'
                            continue
                        if currentFragment == "JOY":
                            print data
                        elif currentFragment == "SLU":
                            if data.startswith('[LOG]'):
                                print 'Log: ' + data
                            else:
                                transcriptions = json.loads(data)
                                best_hypo = transcriptions['hypotheses'][0]['transcription']
                                reply = k.respond(best_hypo)
                                conn.send(reply + '\n')
                    else:
                        print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
                        break
            s.close()
        except socket.error as socketerror:
            print("Error: ", socketerror)

    def cmdActionCb(self, action_msg):
        if(action_msg.data != self.cmd_action):
            cmd_to_send = ''
            if action_msg.data == 0:
                cmd_to_send = k.respond('GETATTENTION')
            elif action_msg.data == 1:
                cmd_to_send = k.respond('START')
            elif action_msg.data == 2:
                cmd_to_send = 'QUESTIONNAIRE'
            elif action_msg.data == 3:
                cmd_to_send = 'FINISH'

            print cmd_to_send
            conn.send(cmd_to_send + '\n')


###  If Main  ###
if __name__ == '__main__':
    AndroidInterface()
