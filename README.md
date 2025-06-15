# DeliveryCart

DeliveryCart is the game made with Python and Panda3D, controlling a cart loaded with baggages carefully not to drop them.　The road is winding. If mishandle, the cart will jump into water.

In this game, I had some new challenges like below.
1. Make procedurally my own viecle by using panda3d BulletVehicle. It was difficult to adjust the positions of the cart body and wheels. I did well for my first time, I think.
2. Creat procedurally a plane having many vertices and manipulate them from frame to frame to make waving water. Seeing the result, I'm very glad my water surface waves well.
3. Connect hollow cylinders also by manipulating vertices to generate winding road, which was very difficult too. The result looks good for me.
4. Fade from one camera perspective to another, which was the biggest hurdle. I think I did very well, but there is still room for improvement. 

I repeatedly read panda3D manual and sample codes, and went to the panda3D community site to find a hint to solve problems. I've visited this site countless times until now. Thanks to this community site, I've learned a lot of things about 3D game coding. 

https://github.com/user-attachments/assets/2e098b50-9540-4996-8477-eb0abfbf6b3a


# Requirements
* Panda3D 1.10.15
  
# Environment
* Python 3.12
* Windows11

# Usage

* Clone this repository with submodule.

```
git clone --recursive https://github.com/taKana671/DeliveryCart.git
```

* Execute a command below on your command line.
```
>cd DeliveryCart
>python delivery_cart.py.py
```

# Controls:
* Select level from 1 to 4. Level means the number of baggages on the cart.
* Press [Esc] to quit.
* Press [W] key to go foward. 
* Press [Q] key to turn left. If stop holding down the key, the steering angle gradually goes to zero.
* Press [E] key to turn right. If stop holding down the key, the steering angle gradually goes to zero.
* Press [S] key to go back. 
* Press [ D ] key to toggle debug ON and OFF.  
