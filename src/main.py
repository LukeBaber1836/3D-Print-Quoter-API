import subprocess
import os
from utilities import fancy_shell


def get_print_details(gcode_file_path):
    """
    Extract print details like time and filament usage from a G-code file
    
    Args:
        gcode_file_path (str): Path to the G-code file
        
    Returns:
        dict: Dictionary containing print time, filament length, and weight
    """
    details = {
        'estimated_time': None,
        'filament_length': None,
        'filament_weight': None
    }
    
    try:
        with open(gcode_file_path, 'r') as file:
            for line in file:
                if line.startswith('; estimated printing time'):
                    details['estimated_time'] = line.split('=')[1].strip()
                elif line.startswith('; filament used [mm]'):
                    details['filament_length'] = float(line.split('=')[1].strip())
                elif line.startswith('; filament used [g]'):
                    details['filament_weight'] = float(line.split('=')[1].strip())
                
                # Break after we find the header section
                if line.startswith(';LAYER:0'):
                    break
                    
        return details
    except Exception as e:
        print(f"Error parsing G-code file: {e}")
        return details


def slice_stl(
        stl_file_path, 
        output_gcode_path=None, 
        config_path=None, 
        printer_profile=None,
        layer_height=None,  
    ):
    """
    Slice an STL file using PrusaSlicer's command line interface
    
    Args:
        stl_file_path (str): Path to the STL file
        output_gcode_path (str, optional): Path for output G-code file. Defaults to None.
        config_path (str, optional): Path to PrusaSlicer config file. Defaults to None.
        printer_profile (str, optional): Printer profile to use. Defaults to None.
    
    Returns:
        bool: True if slicing was successful, False otherwise
    """

    if os.name == 'nt':  # Windows
        prusa_slicer_path = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
        # Check if PrusaSlicer exists at the expected path
        if not os.path.exists(prusa_slicer_path):
            raise FileNotFoundError(f"PrusaSlicer executable not found at {prusa_slicer_path}")
        
        # Build command
        command = f'"{prusa_slicer_path}" --export-gcode'
        
    else:  # Linux
        prusa_slicer_path = r"prusa-slicer"
        # Build command
        command = f'{prusa_slicer_path} --export-gcode'

    
    
    
    # Add options if provided
    if output_gcode_path:
        command += f" --output {output_gcode_path}"
    if layer_height:
        command += f" --layer-height {layer_height}"
    if config_path:
        command += f" --load {config_path}"
    if printer_profile:
        command += f" --printer-technology {printer_profile}"
    
    # Add STL file path
    command += f' "{stl_file_path}"'
    
    try:
        # Execute PrusaSlicer
        fancy_shell(command)
        print("Slicing successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Slicing failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

# Example usage
if __name__ == "__main__":
    # Replace with your STL file path
    stl_file = "./stl_files/moon.stl"
    output_file = "./output"
    
    slice_stl(stl_file_path=stl_file, output_gcode_path=output_file, layer_height=0.2)

    details = get_print_details(output_file + "/moon.gcode")

    print("Estimated Time:", details['estimated_time'])
    print("Filament Length:", details['filament_length'])
    print("Filament Weight:", details['filament_weight'])