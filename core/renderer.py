import bpy
import os

class RenderController:
    def __init__(self,  json_data):
        #It assigns self.settings = json_data["render_configuration"].
        #It assigns self.output_path = json_data["output_management"]["export_path"]
        """
        Initializes the controller with hardware and file path settings.
        """
        # Assign settings from the specific JSON slices
        self.settings = json_data.get("render_configuration", {})
        relative_path = json_data.get("output_management", {}).get("export_path", "//renders/")
        self.output_path = bpy.path.abspath(relative_path)
        # Ensure the directory exists
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def setup_engine(self):
        #Takes: None.
        #Does: Switches Blender to Cycles/Eevee, sets GPU/CPU, and sets resolution based on JSON.
        #Returns: None
        """
        Switches Blender engine, sets hardware device, and configures resolution.
        """
        scene = bpy.context.scene
        render = scene.render
        # 1. Set the Engine (CYCLES or BLENDER_EEVEE)
        render.engine = self.settings.get("engine", "CYCLES")
        # 2. Hardware Configuration (Only for Cycles)
        if render.engine == 'CYCLES':
            scene.cycles.device = self.settings.get("device", "GPU")
            # Refresh devices to ensure GPU is activated
            if scene.cycles.device == 'GPU':
                prefs = bpy.context.preferences.addons['cycles'].preferences
                prefs.get_devices()
                # Set the first available compute device type (CUDA, OPTIX, etc.)
                for type in ('OPTIX', 'CUDA', 'OPENCL'):
                    try:
                        prefs.compute_device_type = type
                        break
                    except:
                        continue
                for device in prefs.devices:
                    device.use = True
        # 3. Set Resolution
        res = self.settings.get("resolution", [1920, 1080])
        render.resolution_x = res[0]
        render.resolution_y = res[1]
        render.resolution_percentage = 100
        # 4. Samples and Denoising
        if render.engine == 'CYCLES':
            scene.cycles.samples = self.settings.get("samples", 128)
            scene.cycles.use_denoising = self.settings.get("denoising", True)

    def render_frame(self, frame_index):
        #Takes: Integer (The current image number).
        #Does: Sets the file path and name (e.g., img_001.png) and triggers bpy.ops.render.render().
        #Returns: String (The full path to the saved image)
        """
        Sets the file name and triggers the render.
        Returns: The absolute file path of the saved image.
        """
        scene = bpy.context.scene
        # Format the file name (e.g., img_0001.png)
        file_name = f"img_{str(frame_index).zfill(4)}.png"
        full_path = os.path.join(self.output_path, file_name)
        # Set Blender's internal output path
        scene.render.filepath = full_path
        # Execute Render (write_still=True saves it to disk)
        bpy.ops.render.render(write_still=True)
        return full_path