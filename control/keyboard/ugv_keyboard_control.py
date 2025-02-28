import rospy
from geometry_msgs.msg import Twist
import sys, select, os
import tty, termios
from std_msgs.msg import String


MAX_LIN_VEL = 20
MAX_ANGLE = 1
LIN_VEL_STEP_SIZE = 0.1
ANGLE_STEP_SIZE = 0.03

cmd_vel_mask = False
ctrl_leader = False

msg2all = """
Control Your XTDrone!
To all drones  (press g to control the leader)
---------------------------
   1   2   3   4   5   6   7   8   9   0
        w       r    t   y        i
   a    s    d       g       j    k    l
        x       v    b   n        ,

w/x : increase/decrease forward velocity 
a/d : increase/decrease steering angle
i/, : no use
j/l : no use
r   : no use
t/y : no use
v/n : no use
b   : no use
s/k : stop
0~9 : extendable mission(eg.different formation configuration)
      this will mask the keyboard control
g   : control the leader
CTRL-C to quit
"""

msg2leader = """
Control Your XTDrone!
To the leader  (press g to control all drones)
---------------------------
   1   2   3   4   5   6   7   8   9   0
        w       r    t   y        i
   a    s    d       g       j    k    l
        x       v    b   n        ,

w/x : increase/decrease forward velocity 
a/d : increase/decrease steering angle
i/, : no use
j/l : no use
r   : no use
t/y : no use
v/n : no use
b   : no use
s/k : stop
0~9 : extendable mission(eg.different formation configuration)
      this will mask the keyboard control
g   : control all drones
CTRL-C to quit
"""

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def print_msg():
    if ctrl_leader:
        print(msg2leader)
    else:
        print(msg2all)

if __name__=="__main__":

    settings = termios.tcgetattr(sys.stdin)

    ugv_num = int(sys.argv[1])
    rospy.init_node('ugv_keyboard_control')
    multi_cmd_vel_flu_pub = [None]*ugv_num
    multi_cmd_pub = [None]*ugv_num
    for i in range(ugv_num):
        multi_cmd_vel_flu_pub[i] = rospy.Publisher('/ugv_'+str(i)+'/cmd_vel', Twist, queue_size=1)
        multi_cmd_pub[i] = rospy.Publisher('/ugv_'+str(i)+'/cmd',String,queue_size=1)
    leader_cmd_vel_pub = rospy.Publisher("/ugv/leader/cmd_vel", Twist, queue_size=1)
    leader_cmd_pub = rospy.Publisher("/ugv/leader_cmd", String, queue_size=1)
    cmd= String()
    twist = Twist()    

    forward  = 0.0
    angle  = 0.0



    print_msg()
    while(1):
        key = getKey()
        if key == 'w' :
            forward = forward + LIN_VEL_STEP_SIZE
            print_msg()
            print("currently:\t forward vel %.2f\t steering angle %.2f " % (forward, angle))
        elif key == 'x' :
            forward = forward - LIN_VEL_STEP_SIZE
            print_msg()
            print("currently:\t forward vel %.2f\t steering angle %.2f " % (forward, angle))
        elif key == 'a' :
            angle = angle + ANGLE_STEP_SIZE
            print_msg()
            print("currently:\t forward vel %.2f\t steering angle %.2f " % (forward, angle))
        elif key == 'd' :
            angle = angle - ANGLE_STEP_SIZE
            print_msg()
            print("currently:\t forward vel %.2f\t steering angle %.2f " % (forward, angle))

        elif key == 'g':
            ctrl_leader = not ctrl_leader
            print_msg()

        elif key == 's' :
            cmd_vel_mask = False
            forward   = 0.0
            angle   = 0.0
            print_msg()
            print("currently:\t forward vel %.2f\t steering angle %.2f " % (forward, angle))
        else:
            for i in range(10):
                if key == str(i):
                    cmd = 'mission'+key
                    print_msg()
                    print(cmd)
                    cmd_vel_mask = True
            if (key == '\x03'):
                break
            
        if forward > MAX_LIN_VEL:
            forward = MAX_LIN_VEL
        elif forward < -MAX_LIN_VEL:
            forward = -MAX_LIN_VEL
        if angle > MAX_ANGLE:
            angle = MAX_ANGLE
        elif angle < -MAX_ANGLE:
            angle = -MAX_ANGLE

        twist.linear.x = forward; twist.angular.z =  angle
        
        for i in range(ugv_num):
            if ctrl_leader:
                leader_cmd_vel_pub.publish(twist)
                leader_cmd_pub.publish(cmd)
            else:
                if not cmd_vel_mask:
                    multi_cmd_vel_flu_pub[i].publish(twist)    
                multi_cmd_pub[i].publish(cmd)
                
        cmd = ''


    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
