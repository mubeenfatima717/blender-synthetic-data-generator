import json
import os

class FormatPackager:
    def __init__(self, json_data):
        #It assigns self.format_type = json_data["annotation_specification"]["format"].
        #It assigns self.export_path = json_data["output_management"]["export_path"] 
        """
        Initializes the exporter with the format type and output location.
        """
        self.format_type = json_data["annotation_specification"].get("format", "YOLO")
        self.export_path = json_data["output_management"].get("export_path", "./output/")
        
        # Create a 'labels' subdirectory within the export path to keep images and text separate
        self.labels_dir = os.path.join(self.export_path, "labels")
        if not os.path.exists(self.labels_dir):
            os.makedirs(self.labels_dir)

    def convert_to_yolo(self, bbox, img_width, img_height):
        #Takes: Raw bbox coordinates and image size.
        #Does: Calculates center_x, center_y, width, height (normalized 0-1).
        #Returns: A formatted string for a .txt file.
        """
        Converts (x_min, y_min, x_max, y_max) to YOLO format:
        [class_id] [center_x] [center_y] [width] [height]
        Note: BBox from annotator is already 0.0 to 1.0.
        """
        x_min, y_min, x_max, y_max = bbox

        # Calculate width and height
        width = x_max - x_min
        height = y_max - y_min

        # Calculate center point
        center_x = x_min + (width / 2)
        center_y = y_min + (height / 2)

        # Format as string: "class x_center y_center width height"
        # Using 6 decimal places for precision
        yolo_string = f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}"
        
        return yolo_string


    def save_label(self, label_data, filename):
        #Takes: The formatted string and the filename.
        #Does: Writes the string to a text file on the disk.
        #Returns: None.
        """
        Writes the formatted string to a .txt file.
        Example: img_0001.png -> img_0001.txt
        """
        # Change image extension to .txt
        base_name = os.path.splitext(filename)[0]
        label_filename = f"{base_name}.txt"
        full_path = os.path.join(self.labels_dir, label_filename)

        with open(full_path, "w") as f:
            f.write(label_data)

    def write_manifest(self, full_log):
        #Takes: A list/dict of all data generated in the session.
        #Does: Creates a manifest.json so the user knows exactly what settings were used for the whole batch.
        #Returns: None.
        """
        Writes a master JSON file containing all session metadata.
        This is used for dataset versioning and debugging.
        """
        manifest_path = os.path.join(self.export_path, "manifest.json")
        
        with open(manifest_path, "w") as f:
            json.dump(full_log, f, indent=4)