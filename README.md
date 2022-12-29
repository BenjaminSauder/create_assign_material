## Create assign material 

A simple and slim blender addon which helps with material creation and assignment.


## Features

It really has just a few features at the moment:

### Create material

![grafik](https://user-images.githubusercontent.com/13512160/209481281-b8dd0bbc-63b5-4e11-953e-6cae917f57de.png)

Creates a material and applies it directly to your current selection.
In object mode it clears the existing materials and assigns this new material - in edit mode it applies the new material to the current face selection.

Choose your prefered shader, base color and name for this material. The color is set on the shader and as the viewport display color.

### Pick material

Pick a material from the scene and then it will get applied the same way as if you would call 'Create material'.

### Cleanup material slots

Cleans any unused material slots from the selected objects. Basically just a wrapper around a stock blender functionality but easier to reach. 

### Assign material

Assign existing materials directly from the menu or pie. This list can get very long, so there is also a search button. Be aware that there exists a cap on how many materials will be listed - default is 50, but can be changed in the addon preferences.


## Interface

The addon supports a few ways to get access to these features. 

1. use the pie menu - set up a hotkey in the keymap editor under 3D View > 3D View (Global) > Material

![grafik](https://user-images.githubusercontent.com/13512160/210015394-3921981f-640a-4772-908a-e009d759d625.png)

2. use a popup menu - set up a hotkey in the keymap editor under 3D View > 3D View (Global) > Material

![grafik](https://user-images.githubusercontent.com/13512160/210015509-68cd0ce6-f646-4383-91d4-343be0b36e09.png)

3. add a header menu - you can enable this in the addon preferences - off by default
 
![grafik](https://user-images.githubusercontent.com/13512160/210015469-7cfcf253-e017-483a-a6e8-967db258e9b1.png)


