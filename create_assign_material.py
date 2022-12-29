import bpy
import bmesh

from bpy_extras import view3d_utils

bl_info = {
    "name": "Create Assign Material",
    "author": "Benjamin Sauder",
    "blender": (3, 1, 0),
    "description": "Creates and assigns a material to the selected objects/faces.",
    "category": "Object",
    "doc_url": "https://github.com/BenjaminSauder/create_assign_material",
}


# -------------------------------------
# Operators
# -------------------------------------

class MaterialSlotCleanup(bpy.types.Operator):
    """Remove unused material slots from selected object"""
    bl_idname = "object.material_slot_cleanup"
    bl_label = "Material slot cleanup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0
    
    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.editmode_toggle()
           
        bpy.ops.object.material_slot_remove_unused()
        
        if context.mode != 'OBJECT':
            bpy.ops.object.editmode_toggle()          

        return {'FINISHED'}


class MaterialCreateAssignMethods():

    def apply_material_to_object(self, object, material):
        object.data.materials.clear()
        object.data.materials.append(material)
    

    def apply_material_to_polygons(self, object, material, cleanup_slots):        
        bm = bmesh.from_edit_mesh(object.data)            
        selected_faces = [f.index for f in bm.faces if f.select]
        all_faces_selected = len(bm.faces) == len(selected_faces)
                
        # check if incomming material is already present
        material_index = -1        
        for i, mat in enumerate(object.data.materials):
            if mat == material:
                material_index = i
                break
        
        # material is not present
        if material_index == -1:
            material_index = len(object.data.materials)

            #no materials assign, but we have a face selection
            if material_index == 0 and not all_faces_selected:
                object.data.materials.append(None)
                material_index += 1

            object.data.materials.append(material)
        
        for index in selected_faces:
            bm.faces[index].material_index = material_index
            
        bmesh.update_edit_mesh(object.data)
        
        if cleanup_slots:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.material_slot_remove_unused()
            bpy.ops.object.mode_set(mode='EDIT')


    # lets keep the shader_types enum close to the usage function
    shader_types = [
        ("Principled", "Principled BSDF", "", "", 0),
        ("Diffuse", "Diffuse BSDF", "", "", 1),
        ("Emission", "Emission", "", "", 2),
        ("PrincipledVolume", "Principled Volume", "", "", 3),
    ]   

    def create_material(self, name, color, shader):
        material = bpy.data.materials.new(name=name)
        material.use_nodes = True
        material.diffuse_color = color
        
        material_output = material.node_tree.nodes.get('Material Output')
              
        shader_node = material.node_tree.nodes.get('Principled BSDF')      
        if shader == "Diffuse":
            material.node_tree.nodes.remove(shader_node)
            shader_node = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            shader_node.inputs[0].default_value = color
            material.node_tree.links.new(material_output.inputs[0], shader_node.outputs[0])
        elif shader == "Emission":
            material.node_tree.nodes.remove(shader_node)
            shader_node = material.node_tree.nodes.new('ShaderNodeEmission')            
            shader_node.inputs[0].default_value = color
            shader_node.inputs[1].default_value = 3.0
            material.node_tree.links.new(material_output.inputs[0], shader_node.outputs[0])     

        elif shader == "PrincipledVolume":
            material.node_tree.nodes.remove(shader_node)
            shader_node = material.node_tree.nodes.new('ShaderNodeVolumePrincipled')            
            shader_node.inputs[0].default_value = color
            material.node_tree.links.new(material_output.inputs[0], shader_node.outputs[0])
        else:
            #principled shader is default
            shader_node.inputs[0].default_value = color
        
        return material


existing_material_names = None

def create_unique_name(name):
    global existing_material_names

    if not existing_material_names:
        existing_material_names = set([x.name for x in bpy.data.materials])        
    
    while name in existing_material_names:
        parts = name.split("_")
        last_part = parts[-1]
            
        if last_part.isnumeric():
            count = int(last_part)
            count += 1
            name = "_".join(parts[:-1]) + "_" + str(count)  
        else:        
            name = name + "_1"
            
    return name
    

class MaterialCreateAssign(bpy.types.Operator, MaterialCreateAssignMethods):
    """Creates and assigns a material to the selected objects/faces"""
    bl_idname = "object.material_create_assign"
    bl_label = "Create / Assign Material"
    bl_options = {'REGISTER', 'UNDO'}
         
    def name_update(self, context):
        self.name = create_unique_name(self.name)
         
    name: bpy.props.StringProperty(name="Name", default="Material", update=name_update)
    shader: bpy.props.EnumProperty(name="Shader", items=MaterialCreateAssignMethods.shader_types)
    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', min=0, soft_max=1.0, size=4, default=(0.7,0.7,0.7, 1.0))
    cleanup_material_slots: bpy.props.BoolProperty(name="Cleanup material slots", default=False)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def invoke(self, context, event):
        global existing_material_names
        existing_material_names = None

        self.init = False        
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        #this is a bit ugly, but circumvents the _restricted context somehow..
        if not self.init:
            self.name = create_unique_name(self.name)
            self.init = True

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)
        col = flow.column()
   
        col.prop(self, "name")
        col.prop(self, "shader")
        col.prop(self, "color")
       
        if context.mode == "EDIT_MESH":        
            col.prop(self, "cleanup_material_slots")
         
        
    def execute(self, context):        
        if context.mode == "EDIT_MESH":
            material = self.create_material(self.name, self.color, self.shader)
            for object in context.selected_objects:
                if object.type == 'MESH':
                    self.apply_material_to_polygons(object, material, self.cleanup_material_slots)
        
        elif context.mode == "OBJECT":
            material = self.create_material(self.name, self.color, self.shader)
            for object in context.selected_objects:
                if object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}:
                    self.apply_material_to_object(object, material)        
        
        return {'FINISHED'}
    
    
class MaterialPick(bpy.types.Operator, MaterialCreateAssignMethods):
    """Assign a material to your selection by picking from the scene"""
    bl_idname = "object.material_pick"
    bl_label = "Pick Material"
    bl_options = {'REGISTER', 'UNDO'}

    cleanup_material_slots: bpy.props.BoolProperty(name="Cleanup material slots", default=False)

    def material_pick(self, context, event):
        scene = context.scene
        context.view_layer.update()
        
        region = context.region
        rv3d = context.region_data
        
        # get the ray from the viewport and mouse
        coord = event.mouse_region_x, event.mouse_region_y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        depsgraph = context.evaluated_depsgraph_get()       
        result, location, normal, index, object, matrix = scene.ray_cast(depsgraph, ray_origin, view_vector)

        if result and index >= 0:
            eval_obj = object.evaluated_get(depsgraph)
            material_index = eval_obj.data.polygons[index].material_index
            material_eval = eval_obj.data.materials[material_index]
            # do NOT reference an evaulated ID
            material = bpy.data.materials.get(material_eval.name)
            return material

        return None

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def modal(self, context, event):
        context.area.tag_redraw()
        bpy.context.workspace.status_text_set(text="Pick material from scene")

        # allow navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            material = self.material_pick(context, event)

            if material:
                if context.mode == "EDIT_MESH":                   
                    for object in context.selected_objects:
                        if object.type == 'MESH':
                            self.apply_material_to_polygons(object, material, self.cleanup_material_slots)
                
                elif context.mode == "OBJECT":                   
                    for object in context.selected_objects:
                        if object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}:
                            self.apply_material_to_object(object, material)        

                bpy.context.workspace.status_text_set(text=None)
                return {'FINISHED'}

            return {'RUNNING_MODAL'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.context.workspace.status_text_set(text=None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}



class MaterialAssign(bpy.types.Operator, MaterialCreateAssignMethods):    
    '''Assigns a material to current selection'''
    bl_idname = "object.material_assign"
    bl_label = "Assign Material"    
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
        
    material_name: bpy.props.StringProperty(name='Material Name', maxlen=63)
    show_list_dialog: bpy.props.BoolProperty(name="Pick from List", default=False)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def invoke(self, context, event):
        if self.show_list_dialog:
            bpy.types.Scene.material_list = bpy.props.CollectionProperty(type=Material_PG_Collection)
            bpy.types.Scene.material_index = bpy.props.IntProperty()

            context.scene.material_list.clear()
            for m in bpy.data.materials:
                
                if m.is_grease_pencil:
                    continue

                item = context.scene.material_list.add()
                item.name = m.name
                item.material = m

            return context.window_manager.invoke_props_dialog(self, width = 400)
        else:
            return self.execute(context)
        
    def execute(self, context):
        if self.show_list_dialog:
            self.material_name = context.scene.material_list[context.scene.material_index].name
            del bpy.types.Scene.material_list
            del bpy.types.Scene.material_index 
        
        if not self.material_name:
            return {'FINISHED'}

        material = bpy.data.materials.get(self.material_name)

        if context.mode == "EDIT_MESH":                   
            for object in context.selected_objects:
                if object.type == 'MESH':
                    self.apply_material_to_polygons(object, material, False)
        
        elif context.mode == "OBJECT":                   
            for object in context.selected_objects:
                if object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}:
                    self.apply_material_to_object(object, material)        

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.prop_search(self, "material_name", bpy.data, "materials")       
        
        # scene = bpy.context.scene
        # col.template_list("Material_UL_items", "material_list", scene, "material_list", scene, "material_index", rows=12)


# -------------------------------------
# Preferences
# -------------------------------------

class AddonPrefs (bpy.types.AddonPreferences):
    bl_idname = __name__

    def update_menu_state(self, context):
        if self.menu_visible:
            bpy.types.VIEW3D_MT_editor_menus.append(VIEW3D_MT_Material.menu_draw)
        else:
            bpy.types.VIEW3D_MT_editor_menus.remove(VIEW3D_MT_Material.menu_draw) 
      
    menu_visible: bpy.props.BoolProperty(name="Add 'Material' menu to the 3d view menus", default=False, update=update_menu_state)    
    show_material_selection: bpy.props.BoolProperty(name="Show the material selection", default=True)
    max_materials_in_menu: bpy.props.IntProperty(name="Max materials in list", default=50, min=1)
   
    def draw(self, context):
        layout = self.layout
        layout.label(text='The addon creates keymap items to open a regular menu or a pie menu.')
        layout.label(text='Choose whatever you prefer - by default no hotkeys are assigned.')
        layout.label(text='Check the keymap editor in 3D View > 3D View (Global)')
        layout.separator()
        layout.prop(self, "menu_visible")
        layout.separator()
        layout.label(text="Adds a list of materials to the pie or menu. This allows to directly choose an existing material.")
        
        row = layout.row()
        row.prop(self, "show_material_selection")
        row.prop(self, "max_materials_in_menu")

# -------------------------------------
# UI code
# -------------------------------------

class MATERIAL_UL_MaterialCollection(bpy.types.UIList):    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        mat = item.material  
        if mat:
            layout.prop(mat, "name", text=mat.name, emboss=False, icon_value=layout.icon(mat))

class VIEW3D_MT_MaterialList(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_MaterialList"
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout

        addon_prefs = get_preferences()

        box = layout.split()
        column = box.column(align=True)

        op = column.operator("object.material_assign", text="Search", icon = "VIEWZOOM")
        op.show_list_dialog = True
        
        grid_flow_columns = 3
        grid = column.grid_flow(columns=grid_flow_columns)

        material_count = 0
        materials = bpy.data.materials.items()
        for material_name, material in materials:
            if material.is_grease_pencil:
                continue
        
            if (type(material.preview) is bpy.types.ImagePreview):
                op = grid.operator("object.material_assign", text=material_name, icon_value=material.preview.icon_id)
            else:
                op = grid.operator("object.material_assign", text=material_name, icon='MATERIAL_DATA')
            
            op.material_name = material_name
            op.show_list_dialog = False
        
            # stop if list gets very large
            material_count += 1
            if material_count >= addon_prefs.max_materials_in_menu:
                break
      


class VIEW3D_MT_Material(bpy.types.Menu):
    bl_label = "Material"
  
    def draw(self, context):       
        layout = self.layout
       
        layout.operator("object.material_create_assign", text="Create material", icon = "MATERIAL_DATA")
        layout.separator()
        layout.operator("object.material_slot_cleanup", text="Cleanup material slots", icon = "SHADERFX")
        layout.separator()
        layout.operator("object.material_pick", text="Pick material",  icon = "EYEDROPPER")

       
        addon_prefs = get_preferences()
        if addon_prefs.show_material_selection:
            layout.menu(VIEW3D_MT_MaterialList.bl_idname)      

    def menu_draw(self, context):
        self.layout.menu("VIEW3D_MT_Material")


class VIEW3D_MT_Material_PIE(bpy.types.Menu):
    bl_label = 'Material'
    bl_idname = 'VIEW3D_MT_create_assign_pie' 
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()   
    
        addon_prefs = get_preferences()

        # left
        pie.operator("object.material_create_assign", text="Create material", icon = "MATERIAL_DATA")
        # right
        pie.operator("object.material_pick", text="Pick material", icon = "EYEDROPPER")
       
        # bottom
        if addon_prefs.show_material_selection:
            materials = bpy.data.materials.items()
            
            box = pie.split()
            column = box.column(align=False)
            
            row = column.split()
                       
            row.separator(factor=0.2)

            row.scale_y = 1.5
            row.scale_x = 5.0
            op = row.operator("object.material_assign", text="Search material", icon = "VIEWZOOM")
            op.show_list_dialog = True
            
            row.separator(factor=0.2)
            row.scale_x = 1.0

            column.separator()
            grid_flow_columns = 6
            grid = column.grid_flow(columns=grid_flow_columns)

            material_count = 0
            
            for material_name, material in materials:
                if material.is_grease_pencil:
                    continue
            
                if (type(material.preview) is bpy.types.ImagePreview):
                    op = grid.operator("object.material_assign", text=material_name, icon_value=material.preview.icon_id)
                else:
                    op = grid.operator("object.material_assign", text=material_name, icon='MATERIAL_DATA')
                
                op.material_name = material_name
                op.show_list_dialog = False
            
                # stop if list gets very large
                material_count += 1                
                if material_count >= addon_prefs.max_materials_in_menu:
                    break
        else:
            op = pie.operator("object.material_assign", text="Search material", icon = "VIEWZOOM")
            op.show_list_dialog = True
        
        # top
        pie.operator("object.material_slot_cleanup", text="Cleanup material slots", icon = "SHADERFX")
       
 
class Material_PG_Collection(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(name="Material", type=bpy.types.Material)       


class Material_UL_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = item.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(mat, "name", text="", emboss=False, icon_value=layout.icon(mat))
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=layout.icon(mat))


# -------------------------------------
# Addon registering boilerplate     
# -------------------------------------

classes_to_register = {
    # Operators
    MaterialSlotCleanup,
    MaterialCreateAssign,
    MaterialPick,
    MaterialAssign,
    # Prefs
    AddonPrefs,
    # UI
    Material_PG_Collection,
    Material_UL_items,
    VIEW3D_MT_MaterialList,
    VIEW3D_MT_Material,
    VIEW3D_MT_Material_PIE,
}  

addon_keymaps = []

def get_preferences():
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__name__].preferences
    return addon_prefs

def register():    
    for c in classes_to_register:
        bpy.utils.register_class(c)    
  
    # keymaps & prefs   
    addon_prefs = get_preferences()
    if addon_prefs.menu_visible:
        bpy.types.VIEW3D_MT_editor_menus.append(VIEW3D_MT_Material.menu_draw)

    wm = bpy.context.window_manager     
    if  wm.keyconfigs.addon:
        keymap = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')

        keymap_item = keymap.keymap_items.new("wm.call_menu_pie", type="NONE", value='PRESS', ctrl=False)
        keymap_item.properties.name = "VIEW3D_MT_create_assign_pie"         
        addon_keymaps.append((keymap, keymap_item))

        keymap_item = keymap.keymap_items.new("wm.call_menu", type="NONE", value='PRESS', ctrl=False)
        keymap_item.properties.name = "VIEW3D_MT_Material"              
        addon_keymaps.append((keymap, keymap_item))


def unregister():   
    # keymaps & prefs
    addon_prefs = get_preferences()
    if addon_prefs.menu_visible:
        bpy.types.VIEW3D_MT_editor_menus.remove(VIEW3D_MT_Material.menu_draw)

    for keymap, keymap_item in addon_keymaps:
        keymap.keymap_items.remove(keymap_item)
    addon_keymaps.clear()   
    
    for c in classes_to_register:
        bpy.utils.unregister_class(c)       


if __name__ == "__main__":
    register()
    

