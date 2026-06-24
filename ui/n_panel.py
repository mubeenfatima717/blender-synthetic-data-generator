from email import generator

import bpy
import json
import os
from .. import core

# 1. UPDATED DATA STORAGE
class SynthGenSettings(bpy.types.PropertyGroup):
    json_path: bpy.props.StringProperty(name="JSON Config", subtype='FILE_PATH')
    target_camera: bpy.props.PointerProperty(name="Camera", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'CAMERA')
    
    # NEW: Progress Tracking
    current_frame: bpy.props.IntProperty(name="Current Frame", default=0)
    total_frames: bpy.props.IntProperty(name="Total Frames", default=0)
    is_running: bpy.props.BoolProperty(name="Is Running", default=False)
    stop_requested: bpy.props.BoolProperty(name="Stop Requested", default=False)

# 2. MODAL OPERATOR (The Logic with Stop/Progress)
class SYNTHGEN_OT_RunGenerator(bpy.types.Operator):
    bl_idname = "synthgen.run_generator"
    bl_label = "Generate Dataset"
    bl_options = {'REGISTER', 'UNDO'} # UNDO support added here

    _timer = None
    rand = None
    rend = None
    anno = None
    expt = None
    config = None

    def modal(self, context, event):





        #  for anonator --- Concept of your main loop script ---

        # Get the dependency graph exactly ONCE at the start of your frame
        current_depsgraph = bpy.context.evaluated_depsgraph_get()

        # Reuse that same graph for every single calculation on this frame
        for obj in self.target_objects:
            bbox = generator.get_2d_bbox(obj, depsgraph=current_depsgraph)
            occlusion = generator.check_occlusion(obj, depsgraph=current_depsgraph) 
            
            #end of annotator 






        props = context.scene.synthgen_props

        # Handle Stop Request
        if event.type in {'ESC'} or props.stop_requested:
            self.cancel(context)
            self.report({'INFO'}, "Generation Forcefully Stopped.")
            return {'CANCELLED'}

        # Timer-based loop (One frame per timer tick)
        if event.type == 'TIMER':
            if props.current_frame < props.total_frames:
                
                # --- ACTUAL WORK (One Frame) ---
                i = props.current_frame
                self.rand.apply_lighting_randomization()
                for obj in self.target_objects:
                    self.rand.apply_random_transform(obj)
                    self.rand.shuffle_materials(obj)
                
                context.view_layer.update()
                image_path = self.rend.render_frame(i)
                
                frame_labels = []
                for obj in self.target_objects:
                    bbox = self.anno.get_2d_bbox(obj)
                    if bbox:
                        yolo_line = self.expt.convert_to_yolo(bbox)
                        frame_labels.append(yolo_line)
                
                if frame_labels:
                    self.expt.save_label("\n".join(frame_labels), os.path.basename(image_path))
                
                # Update UI Counter
                props.current_frame += 1
                return {'RUNNING_MODAL'}
            else:
                # Finished naturally
                self.cancel(context)
                self.report({'INFO'}, "Generation Complete.")
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        props = context.scene.synthgen_props
        
        # Load JSON and Setup (Same as before)
        try:
            with open(props.json_path, 'r') as f:
                self.config = json.load(f)
            
            self.rand = core.RandomizerEngine(self.config)
            self.rend = core.RenderController(self.config)
            self.anno = core.BoundingBoxGenerator(props.target_camera.name, context.scene.name)
            self.expt = core.FormatPackager(self.config)
            self.target_objects = self.rand.target_objects
            
            self.rend.setup_engine()
            
            props.total_frames = self.config.get("randomization_parameters", {}).get("total_images", 10)
            props.current_frame = 0
            props.is_running = True
            props.stop_requested = False

            # START MODAL TIMER
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        except Exception as e:
            self.report({'ERROR'}, f"Init Failed: {str(e)}")
            return {'CANCELLED'}

    def cancel(self, context):
        props = context.scene.synthgen_props
        props.is_running = False
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

# 3. STOP OPERATOR (A simple button to set the stop flag)
class SYNTHGEN_OT_StopGenerator(bpy.types.Operator):
    bl_idname = "synthgen.stop_generator"
    bl_label = "STOP"
    
    def execute(self, context):
        context.scene.synthgen_props.stop_requested = True
        return {'FINISHED'}

# 4. UPDATED UI PANEL
class SYNTHGEN_PT_MainPanel(bpy.types.Panel):
    bl_label = "SynthGen Pro"
    bl_idname = "SYNTHGEN_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SynthGen"

    def draw(self, context):
        layout = self.layout
        props = context.scene.synthgen_props

        if not props.is_running:
            # --- SECTION 1: CONFIGURATION ---
            col = layout.column(align=True)
            col.label(text="Setup Config:", icon='SETTINGS')
            col.prop(props, "json_path", text="")
            col.prop(props, "target_camera")
            
            layout.separator()

            # --- SECTION 2: CALIBRATION (The Preview Tools) ---
            col = layout.column(align=True)
            col.label(text="Calibration Tools:", icon='VIEWZOOM')
            row = col.row(align=True)
            row.operator("synthgen.draw_visual_box", text="Show BBox Overlay", icon='VIS_SEL_1')
            
            layout.separator()

            # --- SECTION 3: PRODUCTION ---
            col = layout.column()
            col.scale_y = 1.5
            col.operator("synthgen.run_generator", text="GENERATE DATASET", icon='PLAY')
        else:
            # --- SECTION 4: PROGRESS (When running) ---
            box = layout.box()
            box.label(text=f"Progress: {props.current_frame} / {props.total_frames}")
            progress = props.current_frame / props.total_frames
            box.progress(text="Rendering...", factor=progress)
            box.operator("synthgen.stop_generator", icon='CANCEL', text="STOP")