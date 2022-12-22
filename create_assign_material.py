import bpy
import bmesh


bl_info = {
    "name": "Create Assign Material",
    "author": "Benjamin Sauder",
    "blender": (3, 1, 0),
    "description": "Creates and assigns a material to the selected objects/faces.",
    "category": "Object"
}

def check_name(name):
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
    

class CreateAssignMaterial(bpy.types.Operator):
    """Creates and assigns a material to the selected objects/faces"""
    bl_idname = "object.create_assign_material"
    bl_label = "Create / Assign Material"
    bl_options = {'REGISTER', 'UNDO'}
    
   
    shader_types = [
        ("Principled", "Principled BSDF", "", "", 0),
        ("Diffuse", "Diffuse BSDF", "", "", 1),
        ("Emission", "Emission", "", "", 2)
    ]
    
    def name_update(self, context):
        self.name = check_name(self.name)
        
    def shader_update(self, context):
        #print(self.shader)
        pass
        
    name: bpy.props.StringProperty(name="Name", default="Material", update=name_update)
    shader: bpy.props.EnumProperty(name="Shader", items=shader_types, update=shader_update)
    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', min=0, soft_max=1.0, size=4, default=(0.7,0.7,0.7, 1.0))
    cleanup_material_slots: bpy.props.BoolProperty(name="Cleanup material slots", default=False)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def invoke(self, context, event):
        self.init = False        
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        #this is a bit ugly, but circumvents the _restricted context somehow..
        if not self.init:
            self.name = check_name(self.name)
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
            material = self.create_material()
            for object in context.selected_objects:
                if object.type == 'MESH':
                    self.apply_material_to_polygons(object, material)
        
        elif context.mode == "OBJECT":
            material = self.create_material()
            for object in context.selected_objects:
                if object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}:
                    self.apply_material_to_object(object, material)        
        
        return {'FINISHED'}
    
    
    def apply_material_to_object(self, object, material):
        object.data.materials.clear()
        object.data.materials.append(material)
    

    def apply_material_to_polygons(self, object, material):
        object.data.materials.append(material)
        material_index = len(object.data.materials) - 1
        
        bm = bmesh.from_edit_mesh(object.data)    
        
        selected_faces = [f.index for f in bm.faces if f.select]
        
        for index in selected_faces:
            bm.faces[index].material_index = material_index
            
        bmesh.update_edit_mesh(object.data)
        
        if self.cleanup_material_slots:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.material_slot_remove_unused()
            bpy.ops.object.mode_set(mode='EDIT')


    def create_material(self):
        material = bpy.data.materials.new(name=self.name)
        material.use_nodes = True
        material.diffuse_color = self.color
        
        material_output = material.node_tree.nodes.get('Material Output')
              
        shader_node = material.node_tree.nodes.get('Principled BSDF')      
        if self.shader == "Diffuse":
            material.node_tree.nodes.remove(shader_node)
            shader_node = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            shader_node.inputs[0].default_value = self.color
            material.node_tree.links.new(material_output.inputs[0], shader_node.outputs[0])
        elif self.shader == "Emission":
            material.node_tree.nodes.remove(shader_node)
            shader_node = material.node_tree.nodes.new('ShaderNodeEmission')            
            shader_node.inputs[0].default_value = self.color
            material.node_tree.links.new(material_output.inputs[0], shader_node.outputs[0])     
        else:
            #principled is default
            shader_node.inputs[0].default_value = self.color
        
        return material
        


def register():
    bpy.utils.register_class(CreateAssignMaterial)


def unregister():
    bpy.utils.unregister_class(CreateAssignMaterial)


if __name__ == "__main__":
    register()
    
