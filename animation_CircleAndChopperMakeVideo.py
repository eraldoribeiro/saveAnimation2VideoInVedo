"""
Click on and adjust viewing angle to activate. 

Press Enter or Space to step through the animation. 

ESC: terminates the program.

Once the animation terminates, the animation sequence is saved in 
the file animation.mp4, which should be compatible with 
most video players (e.g., Quicktime player, VNC). 

"""
from vedo import *
import os
import time 
import numpy as np
from os import path



def RotationAboutY(theta: float) -> np.ndarray:
    """Returns the matrix of the 3-D rotation about the y-axis. 
       Matrix is in homogeneous coordinates

    Args:
      theta: Rotation angle in radians (float)

    Returns:
      RotY: Rotation matrix (4x4 np.ndarray) 
      
    """    

    # Matrix of 3-D rotation by angle=theta about the y-axis
    RotY = np.array(
        [
            [ np.cos(theta),  0, np.sin(theta),  0],
            [             0,  1,             0,  0],
            [-np.sin(theta),  0, np.cos(theta),  0],
            [             0,  0,             0,  1]
        ]
    )

    return RotY

def getNewPosition_yellowPoint(p: np.ndarray, angle: float, T_01: np.ndarray) -> np.ndarray:   
    """Obtains the (global) coordinates of a point/object 
    after a rotation about the point's/object's local frame. 

    Args:
      p:     Current position (3x1 np.ndarray) 
      angle: Rotation angle in radians (float)
      T_01:  Transform between the local frame F{1} to the global 
             frame F{0}  (4x4 np.ndarray)

    Returns:
      newPosition: Coordinates of the new location of p (3x1 np.ndarray) 
      
    """

    # Convert point to homogeneous coords
    p_tilde = np.block([[p], [1]])

    # Motion of the yellow point is just a rotation 
    R_y = RotationAboutY(angle)  # Using my own rotation function

    # I want to rotate the point w.r.t. local frame.
    # However, the point's original location is given in global coordinates. 
    # As a result, rotating it about a local frame using just a rotation matrix 
    # will not produce the desired outcome. I need first to convert the point to
    # the local frame, rotate it, and then convert its rotated coordinates back to 
    # the global frame prior to displaying the result. 
        
    # This matrix transforms between the local frame F{0} to the global frame F{1}
    T_10 = np.linalg.inv(T_01)
    
    # The following matrix controls the motion of the point. This matrix 
    # a composition of transformations. First: Convert the coordinates of the 
    # point from global to local coords. Second: Rotate the point. Third: Convert
    # the result from local to global coords.
    T_Motion = T_01 @ R_y @ T_10

    # This is the new location of the yellow point in global coordinates
    p = T_Motion @ p_tilde
    
    # Convert from homogeneous to Cartesian before returning   
    p_new = np.array([p[0]/p[3], 
                      p[1]/p[3],
                      p[2]/p[3]])    
    
    return p_new

def loop_func(event):
    """This is the callback function that is called when the timer goes off 
    or the chosen condition happens. 

    The variable that changes (e.g., angle, distance) when this function is called needs 
    to be global. 
      
    """    

    global p
    
    # Get updated position of point/object 
    p = getNewPosition_yellowPoint(p, theta, T_01)
    
    # Update object's position (leave a trail behind, just for fun!)
    yellowPoint.pos(p)

    # Update the scene 
    plt.render()
    
    video.add_frame()                  # add individual frame

    
    
#--------------------------------------------------------------------------
#  Begin script 
#--------------------------------------------------------------------------


# Read mesh files of each part, and color-label them
mainBodyMesh = Mesh("./main_body.vtk").c("white")
topRotorMesh = Mesh("./top_rotor.vtk").c("red")
tailRotorMesh = Mesh("./tail_rotor.vtk").c("blue")

# Create a local coordinade frame (approx.) centered at the front of the chopper.
# This local frame is just translated w.r.t. to the global frame. Local frame
# will govern the motion of the yellow point. The motion is just a
# rotation about the local y-axis.

# Create a line to visualize the local y-axis
startPoint, endPoint = (-40, 0, -20), (-40, -20, -20)
line = Line(startPoint, endPoint).lw(5).c((0, 1, 0))

# Create a point to provide an example of animation. Point
# is off-set along the x-axis to show rotation about the local y-axis.
p = np.array([[-30.0], [-10.0], [-20.0]])
print("\nThe start position of the rotating point \n in global coordinates = ")
print(p)

# Create a Vedo point at location p
yellowPoint = Point(p, c="y")     


# Transformation matrix from local frame to global (local frame is F{1}).
# I am centering the frame at the start point of the green line, i.e., startPoint
T_01 = np.array(
    [
        [1.0, 0.0, 0.0, -40],
        [0.0, 1.0, 0.0,   0],
        [0.0, 0.0, 1.0, -20],
        [0.0, 0.0, 0.0, 1.0],
    ]
)

print("\nTransformation from local frame F{1} to global frame F{0}:\nT_01 = ")
print(T_01)
print("\n")

# Rotation step
theta = np.pi/20

# Open a video file and force it to last 3 seconds in total. 
# Creating a tmp file because the Vedo's video function creates 
# a video that might not show in all players. So, we will call 
# ffmpeg ourselves to modify the file to play in more players. 
# See os.system() call at the end of this script.
video = Video("tmp.mp4", 
#              duration=4, 
              backend='ffmpeg', 
              fps = 24
             ) 


# Build the graphical scene with all objects and axes
plt = Plotter(size=(1050, 600))
plt += [mainBodyMesh, topRotorMesh, tailRotorMesh, yellowPoint, line, __doc__]
plt.background("black", "w").add_global_axes(axtype=1).look_at(plane='yz')


# Timer ID
timer_id = None

# Link the callback function and create/activate the timer
plt.add_callback("timer", loop_func)
plt.timer_callback("create", dt=50)


# Render 
plt.show().close()

video.close()                         # merge all the recorded frames

# Convert the video file spider.mp4 to play on a wider range of video players 
if path.exists("./animation.mp4"):
    os.system("rm animation.mp4")
    
os.system("ffmpeg -i tmp.mp4 -pix_fmt yuv420p animation.mp4")
os.system("rm tmp.mp4")

#--------------------------------------------------------------------------
#  End script 
#--------------------------------------------------------------------------
     
   
    
