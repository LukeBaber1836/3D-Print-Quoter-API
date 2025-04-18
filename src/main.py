from utilities import fancy_shell



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