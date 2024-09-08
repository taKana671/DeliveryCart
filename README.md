# DeliveryCart

DeliveryCart is the game made with Python and Panda3D, controlling a cart loaded with baggages carefully not to drop them.　The road is winding. If mishandle, the cart will jump into water.

In this game, I had some new challenges. First, I made procedurally my own viecle by using panda3d BulletVehicle. It was difficult to adjust the positions of the cart body and wheels, but I did well for my first time, I think. The second, I tried to make waving water by creating a plane having many vertices and manipulating them from frame to frame. I'm very glad my water surface waves well. The third, I connected hollow cylinders also by manipulating vertices to generate winding road, which was very difficult too. It looks good for me. The fourth, the biggest hurdle, fading from one camera perspective to another, which I made through.　I think I did very well, but I believe there is still room for improvement. 

I repeatedly read panda3D manual and sample codes, and went community site. I've visited this community site countless times. Thanks to this site, I've learned a lot of things about 3D game programming. Thank you, all of panda3d community members.　

![demo](https://github.com/user-attachments/assets/f5929748-7a83-4cb5-a8e0-e4a1fcc0f62d)


# Requirements
* Panda3D 1.10.14
* numpy 1.23.5
* opencv-contrib-python 4.8.0.74
* opencv-python 4.8.0.74

# Environment
* Python 3.11
* Windows11
