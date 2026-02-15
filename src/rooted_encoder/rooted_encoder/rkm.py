import numpy as np
from math import sin, cos

class KinematicModel():

    def __init__(self, robot_width=0.19861, wheel_radius=0.09597, initial_x=0,
                 initial_y=0, initial_theta=0, initial_speed_left=0,
                 initial_speed_right=0):
        self.pose = [initial_x, initial_y, initial_theta]
        self.left_speed = initial_speed_left
        self.right_speed = initial_speed_right
        self.r = wheel_radius
        self.d = robot_width
        self.speed = self.convert_LeftRight_to_LinearAngular(self.left_speed, self.right_speed)

    def convert_LeftRight_to_LinearAngular(self,L,R):
        LS = self.r/2*(L+R)
        AS = self.r/(2*self.d)*(R-L)
        return [LS, AS]

    def convert_LinearAngular_to_LeftRight(self,L,A):
        linear_speed = L
        angular_speed = A
        r = self.r
        return [(linear_speed-self.d*angular_speed)/r,
                (linear_speed+self.d*angular_speed)/r]

    def wheel_speed_equation(self, left_speed, right_speed):
        r = self.r
        t = self.pose[2]
        ls = left_speed
        rs = right_speed
        result = np.dot(np.array([[r/2*cos(t), r/2*cos(t)],
                                  [r/2*sin(t), r/2*sin(t)],
                                  [-r/(2*self.d), r/(2*self.d)]]),
                                  np.array([[ls],[rs]]))
        dx , dy, dtheta = [i[0] for i in result.tolist()]
        return dx, dy, dtheta

    def angle_limiter(self):
        theta = self.pose[2]
        if abs(theta)>np.pi:
            if theta>0:
                self.pose[2]=-2*np.pi+theta
            else:
                self.pose[2]=2*np.pi-theta

    def generalized_speed_equation(self, left_speed, right_speed):
        r = self.r
        t = self.pose[2]
        v, w =  r*(left_speed+right_speed)/2, (right_speed-left_speed)*r/self.d  #get_speed()
        dx, dy, dtheta = [i[0] for i in np.dot(np.array([[cos(t), 0],
                          [sin(t), 0], [0, 1]]),np.array([[v],[w]])).tolist()]
        return dx, dy, dtheta

    def update(self, dt):
        dx, dy, dtheta = self.generalized_speed_equation(self.left_speed, self.right_speed)
        self.pose = [round(self.pose[0]+dx*dt,3), round(self.pose[1]+dy*dt,3), round(self.pose[2]+dtheta*dt,3)]
        self.angle_limiter()
        self.speed = self.convert_LeftRight_to_LinearAngular(self.left_speed, self.right_speed)
        #print ("Current pose [x,y,theta]: ", self.pose)