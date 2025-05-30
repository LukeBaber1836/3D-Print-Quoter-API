import json
from pathlib import Path
from app.schemas.responses import PrinterConfig
from app.constants import LOCAL_DIR

FILAMENT_PROFILES = {
    "PLA": {
        "filament_type": "PLA",
        "temperature": 210,
        "first_layer_temperature": 215,
        "bed_temperature": 60,
        "first_layer_bed_temperature": 75,
        "fan_always_on": 1,
        "fan_below_layer_time": 60,
        "filament_density": 1.24,
        "filament_cost": 25,
        "filament_diameter": 1.75
    },
    "PETG": {
        "filament_type": "PETG",
        "temperature": 230,
        "first_layer_temperature": 230,
        "bed_temperature": 70,
        "first_layer_bed_temperature": 80,
        "fan_always_on": 1,
        "fan_below_layer_time": 60,
        "filament_density": 1.27,
        "filament_cost": 30,
        "filament_diameter": 1.75
    },
    "ABS": {
        "filament_type": "ABS",
        "temperature": 240,
        "first_layer_temperature": 240,
        "bed_temperature": 100,
        "first_layer_bed_temperature": 100,
        "fan_always_on": 0,
        "fan_below_layer_time": 60,
        "filament_density": 1.04,
        "filament_cost": 25,
        "filament_diameter": 1.75
    }
}

SPEED_RATIOS = {
    'default_speed': 1.0,
    'perimeter_speed': 0.8,
    'small_perimeter_speed': 0.5,
    'external_perimeter_speed': 0.6,
    'infill_speed': 1.2,
    'solid_infill_speed': 0.8,
    'support_material_speed': 0.8,
    'bridge_speed': 0.5,
    'travel_speed': 2,
    'first_layer_speed': 0.5
}

def get_filament_profile_section(filament_type):
    """Generate a filament profile section for the INI file based on filament type."""
    if filament_type not in FILAMENT_PROFILES:
        filament_type = "PLA"
    
    profile = FILAMENT_PROFILES[filament_type]
    section = ""
    for key, value in profile.items():
        section += f"{key} = {value}\n"
    
    return section

def create_ini_config(
        user_id: str,
        stl_file_path: str,
        printer_config: PrinterConfig,
    ):
    """
    Create a configuration file for the slicer.
    
    Args:
        printer_config: Dictionary containing printer configuration settings
        
    Returns:
        str: The path to the created configuration file
    """
    default_config_path = Path("./app/services/configs/default_config.json")
    
    if not default_config_path.exists():
        raise FileNotFoundError(f"Default configuration file not found at: {default_config_path}")

    with open(default_config_path, 'r') as f:
        config_content = f.read()
    
    config_dict = json.loads(config_content)
    config_dict['bed_shape'] = f"0x0,{printer_config.bed_size_x}x0,{printer_config.bed_size_x}x{printer_config.bed_size_y},0x{printer_config.bed_size_y}"
    
    for key, value in dict(printer_config).items():
        if key == 'bed_size_z':
            config_dict['max_print_height'] = value

        elif key == 'print_speed':
            for speed_key, ratio in SPEED_RATIOS.items():
                config_dict[speed_key] = round(value * ratio)

        elif key == 'filament_type':
            config_dict.update(FILAMENT_PROFILES[value])
            config_dict['first_layer_temperature'] = round(printer_config.temperature * 1.05)
            config_dict['first_layer_bed_temperature'] = round(printer_config.bed_temperature * 1.25)
        
        elif key == 'support_material':
            config_dict['support_material'] = '1' if value else '0'

        elif key == 'fill_density':
            config_dict['infill_density'] = f'{value}%'

        elif key in config_dict:
            config_dict[key] = value

    
    # Convert the updated dictionary back to a string for the INI file
    config_string = ""
    for key, value in config_dict.items():
        config_string += f"{key} = {value}\n"
    
    file_path_parts = stl_file_path.split('/')
    output_name = file_path_parts[-1].rsplit('.', 1)[0] + '.ini'

    job_output_dir = Path(LOCAL_DIR / user_id)
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the modified configuration to a new file in the user's job output directory
    with open(job_output_dir / output_name, 'w') as f:
        f.write(config_string)
    
    return {
        'output_dir' : job_output_dir / output_name
    }