## Create assign material 

A simple blender addon, which helps with mateiral creation and assignment.


## Features

It really has just three features at the moment:

### Create material

![grafik](https://user-images.githubusercontent.com/13512160/209481281-b8dd0bbc-63b5-4e11-953e-6cae917f57de.png)

Creates a material and applies it directly to your current selection.
In object mode it clears the existing materials and assigns this new material - in edit mode it applies the new material to the current face selection.

Choose your prefered shader, base color and name for this material. The color is set on the shader and as the viewport display color.

### Pick material

Pick a material from the scene and then it will get applied the same way as if you would call 'Create material'

### Cleanup material slots

Cleans any unused material slots from the selected objects. Basically just a wrapper around a stock blender functionality but easier to reach. 

## Interface

The addon supports a few ways to get access to these features. 

1. use the pie menu - set up a hotkey in the keymap editor under 3D View > 3D View (Global) > Material

![grafik](https://user-images.githubusercontent.com/13512160/209481095-e1adc6bf-4e66-4b11-93f4-b41b7e16728d.png)

2. use a popup menu - set up a hotkey in the keymap editor under 3D View > 3D View (Global) > Material

![grafik](https://user-images.githubusercontent.com/13512160/209481205-7f42966e-1a18-463c-abfc-089d4d72b09c.png)

3. add a header menu - enable this in the addon preferences

![grafik](https://user-images.githubusercontent.com/13512160/209481221-affeac4f-122c-4ee3-9156-fd595b9c8b9a.png)

