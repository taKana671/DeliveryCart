# DeliveryCart

DeliveryCart is the game made with Python and Panda3D, controlling a cart loaded with baggages carefully not to drop them.　The road is winding. If mishandle, the cart will jump into water.

In this game, I had some new challenges like below.
1. Make procedurally my own viecle by using panda3d BulletVehicle. It was difficult to adjust the positions of the cart body and wheels. I did well for my first time, I think.
2. Creat procedurally a plane having many vertices and manipulate them from frame to frame to make waving water. Seeing the result, I'm very glad my water surface waves well.
3. Connect hollow cylinders also by manipulating vertices to generate winding road, which was very difficult too. The result looks good for me.
4. Fade from one camera perspective to another, which was the biggest hurdle. I think I did very well, but there is still room for improvement. 

I repeatedly read panda3D manual and sample codes, and went to the panda3D community site to find a hint to solve a problem. I've visited this site countless times until now. Thanks to this community site, I've learned a lot of things about 3D game coding. 

https://github.com/user-attachments/assets/f5929748-7a83-4cb5-a8e0-e4a1fcc0f62d


# Requirements
* Panda3D 1.10.14
* numpy 1.23.5
* opencv-contrib-python 4.8.0.74
* opencv-python 4.8.0.74

# Environment
* Python 3.11
* Windows11

# Usage
* Execute a command below on your command line.
```
>>>python delivery_cart.py.py
```

# Controls:
* Press [Esc] to quit.
* Press [W] key to go foward. 
* Press [Q] key to turn left. If stop holding down the key, the steering angle gradually goes to zero.
* Press [E] key to turn right. If stop holding down the key, the steering angle gradually goes to zero.
* Press [S] key to go back. 
* Press [ D ] key to toggle debug ON and OFF.  
