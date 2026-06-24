import bpy
import gpu
import json
from gpu_extras.batch import batch_for_shader
from .. import core

# Global handle to remove the drawing when finished
_draw_handle = None

def get_2d_uniform_shader():
    """Returns the correct shader name based on Blender Version"""
    if bpy.app.version >= (4, 0, 0):
        # Blender 4.0, 4.1, 4.2, 5.0+
        return gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        # Blender 3.6 and older
        return gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    
class SYNTHGEN_OT_DrawVisualBox(bpy.types.Operator):
    """Draw a 2D Bounding Box overlay in the 3D Viewport"""
    bl_idname = "synthgen.draw_visual_box"
    bl_label = "Toggle BBox Overlay"
    
    def modal(self, context, event):
        if event.type == 'ESC':
            self.stop_drawing(context)
            return {'CANCELLED'}
        
        if context.area:
            context.area.tag_redraw()
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global _draw_handle
        
        if _draw_handle is not None:
            self.stop_drawing(context)
            return {'CANCELLED'}
        
        props = context.scene.synthgen_props
        if not props.target_camera:
            self.report({'ERROR'}, "Select a camera first.")
            return {'CANCELLED'}

        # Init Annotator
        self.anno = core.BoundingBoxGenerator(props.target_camera.name, context.scene.name)
        
        # Start drawing callback
        args = (self, context)
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def stop_drawing(self, context):
        global _draw_handle
        if _draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
            _draw_handle = None

def draw_callback(self, context):
    """The function that handles the actual GPU drawing of the rectangle"""
    props = context.scene.synthgen_props
    
    # We need the current randomization objects
    # For preview, we just grab the target objects defined in the scene
    for obj_name in context.scene.get("synthgen_targets", []):
        obj = bpy.data.objects.get(obj_name)
        if not obj: continue
        
        bbox = self.anno.get_2d_bbox(obj)
        if not bbox: continue
        
        # Convert 0-1 normalized coords to actual Screen Pixels
        width = context.region.width
        height = context.region.height
        
        x_min, y_min, x_max, y_max = bbox
        px_min_x, px_max_x = x_min * width, x_max * width
        px_min_y, px_max_y = y_min * height, y_max * height

        # Define coordinates for a hollow rectangle
        coords = [
            (px_min_x, px_min_y), (px_max_x, px_min_y),
            (px_max_x, px_min_y), (px_max_x, px_max_y),
            (px_max_x, px_max_y), (px_min_x, px_max_y),
            (px_min_x, px_max_y), (px_min_x, px_min_y)
        ]

        shader = get_2d_uniform_shader()
        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        
        shader.bind()
        shader.uniform_float("color", (0.0, 1.0, 0.0, 1.0)) # Bright Green
        batch.draw(shader)