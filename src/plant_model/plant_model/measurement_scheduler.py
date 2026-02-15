import sched
import time
import ast
import json
import os

from std_msgs.msg import String
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from rooted_interfaces.rooted_interfaces.sensors_interface import SensorReader
from rooted_interfaces.rooted_interfaces.memory_interface import MemoryAccess
from rooted_interfaces.rooted_interfaces.navigation_interface import NavigationCommandSender
rclpy.init()

## Safe Nitrogen soil content range (min, max)
safe_N_range=[0,0]
## Safe Phosphorus soil content range (min, max)
safe_P_range=[0,0]
## Safe Potassium soil content range (min, max)
safe_K_range=[0,0]
## Safe Soil salinity range (min, max)
safe_EC_range=[0,0]
## Safe Soil pH range (min, max)
safe_pH_range=[0,0]
## Safe Soil moisture  range (min, max)
safe_moisture_range=[0,0]
## Safe temperature range for the plant species  (min, max)
safe_temperature_range=[0,0]   
## Safe irradiance range for the plant species range (min, max)
safe_irradiance_range=[0,0]


def load_plant_needs(filename):
    """! Method that loads the safe ranges for monitored environmental characteristics of a plant species.
    @param filename <str/path>: full file location of a .json file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            return data
    else:
        return {}


class NotificationSender(Node):
    """! Class responsible for sending notifications and move orders."""
    def __init__(self):
        """! NotificationSender class' initializer method."""
        super().__init__('plant_model_notification_sender')
        self.notification_publisher = self.create_publisher(String, 'notificationTopic', 10)
        self.move_order_publisher = self.create_publisher(String, 'move_order', 10)
        self.notification_publisher
        self.move_order_publisher

    def send_notification(self, characteristic, status, measurement):
        """! Sends a notification about a specific plant characteristic.
        @param characteristic <str>: The characteristic being monitored (e.g., nitrogen, temperature).
        @param status <str>: The status of the characteristic (e.g., low, high).
        @param measurement <str>: The actual measurement value."""
        self.notification_publisher.publish(f"{characteristic}:{status}:{measurement}")


sensor_interface = SensorReader("plant_model_sensor_reader")
memory_interface = MemoryAccess("plant_model_memory_access")
notification_sender = NotificationSender()
robot_mover = NavigationCommandSender("plant_model_navigation_command_sender")
plant_info_file_path = sensor_interface.plant_information_file
plant_info = load_plant_needs(plant_info_file_path)
db_location = sensor_interface.db


def sensor_reading(sensor_ID):
    """! Retrieves the reading from a specific sensor.
    @param sensor_ID <int>: The sensor ID to read from.
    @return <float>: The sensor reading, or NaN if the reading failed."""
    sensor_interface.send_request(sensor_ID)
    while rclpy.ok():
        rclpy.spin_once(sensor_interface)  # Non-blocking
        if sensor_interface.future.done():
            try:
                response = sensor_interface.future.result().sensor_reading
                try:  # Convert result to a number (int, float) or list
                    response = ast.literal_eval(response)
                    break
                except:
                    print(f'Failed to read sensor {sensor_ID}!')
                    response = float('Nan')
            except Exception as e:
                print(f'Failed to read sensor {sensor_ID}!')
                sensor_interface.get_logger().info('Service call failed %r' % (e,))
            else:
                return response
    return float('Nan')


def write_measurement(db, sql_command):
    """! Writes a measurement to the memory database.
    @param db <str>: The database file path.
    @param sql_command <str>: The SQL command to execute."""
    memory_interface.send_request(db, sql_command)


def soil_N_reading():
    """! Retrieves and processes the soil Nitrogen (N) reading."""
    safe_range = plant_info["plant"]["health"]["nutrients"]["N"]
    reading = sensor_reading(8)
    current_time = time.time()
    query = f"""
    INSERT INTO N (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("nitrogen", problem, str(reading))
        

def soil_P_reading(): 
    """! Retrieves and processes the soil Phosphorus (P) reading."""
    safe_range = plant_info["plant"]["health"]["nutrients"]["P"]
    reading = sensor_reading(9)
    current_time = time.time()
    query = f"""
    INSERT INTO P (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("phosphorus", problem, str(reading))


def soil_K_reading(): 
    """! Retrieves and processes the soil Potassium (K) reading."""
    safe_range = plant_info["plant"]["health"]["nutrients"]["K"]
    reading = sensor_reading(10)
    current_time = time.time()
    query = f"""
    INSERT INTO K (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)    
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("potassium", problem, str(reading))


def soil_EC_reading(): 
    """! Retrieves and processes the soil Electrical Conductivity (EC) reading."""
    safe_range = plant_info["plant"]["health"]["EC"]
    reading = sensor_reading(6)
    current_time = time.time()
    query = f"""
    INSERT INTO EC (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("salinity", problem, str(reading))


def soil_pH_reading(): 
    """! Retrieves and processes the soil pH reading."""
    safe_range = plant_info["plant"]["health"]["pH"]
    reading = sensor_reading(7)
    current_time = time.time()
    query = f"""
    INSERT INTO pH (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("pH", problem, str(reading))


def soil_moisture_reading(): 
    """! Retrieves and processes the soil moisture reading."""
    safe_range = plant_info["plant"]["health"]["soil_moisture"]
    reading = sensor_reading(4)
    current_time = time.time()
    query = f"""
    INSERT INTO water (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("water", problem, str(reading))


def no_store_temperature_reading(): 
    """! Retrieves the temperature reading without storing it."""
    return sensor_reading(5)


def move_2_light(): 
    """! Notifies that the robot needs to move to sunlight."""
    robot_mover.send_move_order("light")


def move_2_shade(): 
    """! Notifies that the robot needs to move into shade."""
    robot_mover.send_move_order("shadow")


def temperature_reading(): 
    """! Retrieves and processes the temperature reading."""
    safe_range = plant_info["plant"]["environment"]["temperature"]   
    reading = no_store_temperature_reading()
    current_time = time.time()
    query = f"""
    INSERT INTO temperature (reading, time)
    VALUES ({reading}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    if reading < safe_range[0] or reading > safe_range[1]:
        problem = True
    
    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
            move_2_shade()
        notification_sender.send_notification("temperature", problem, str(reading))


def irradiance_reading():
    """! Retrieves and processes the irradiance reading."""
    safe_range = plant_info["plant"]["environment"]["light"]
    safe_range_temperature = plant_info["plant"]["environment"]["temperature"]
    top_left = sensor_reading(1)
    top_right = sensor_reading(2)
    rear = sensor_reading(3)
    reading =  [top_left, top_right, rear]
    current_time = time.time()
    current_temperature = no_store_temperature_reading()
    high_temp = current_temperature > safe_range_temperature[1]
    query = f"""
    INSERT INTO light (top_left, top_right, bottom, time)
    VALUES ({reading[0]}, {reading[1]}, {reading[2]}, {current_time})
    """
    global db_location
    memory_interface.send_request(db_location, query)
    problem = False

    for l in reading:
        if l < safe_range[0] and not high_temp:
            problem = True
            move_2_light()
        elif l > safe_range[1]:
            problem = True
            move_2_shade()

    if problem:
        problem = "low"
        if reading>safe_range[0]:
            problem = "high"            
        notification_sender.send_notification("", problem, str(reading))


plantroid_scheduler= sched.scheduler(time.time,  time.sleep)


def schedule_sensor_tasks():
    """! Schedules the sensor measurement tasks."""
    plantroid_scheduler.enter(10, 1, run_sensor_task, ('soil_N_reading', soil_N_reading, 24*3600)) #  Daily measurement
    plantroid_scheduler.enter(20, 1, run_sensor_task, ('soil_P_reading', soil_P_reading, 24*3600)) #  Daily measurement
    plantroid_scheduler.enter(30, 1, run_sensor_task, ('soil_K_reading', soil_K_reading, 24*3600)) #  Daily measurement
    plantroid_scheduler.enter(30, 1, run_sensor_task, ('soil_K_reading', soil_pH_reading, 24*3600)) #  Daily measurement
    plantroid_scheduler.enter(30, 1, run_sensor_task, ('soil_K_reading', soil_EC_reading, 24*3600)) #  Daily measurement
    plantroid_scheduler.enter(40, 1, run_sensor_task, ('soil_moisture_reading', soil_moisture_reading, 3600))  # Hourly measurement
    plantroid_scheduler.enter(60, 1, run_sensor_task, ('irradiance_reading', irradiance_reading)) #  Every 5 minutes
    plantroid_scheduler.enter(60, 1, run_sensor_task, ('irradiance_reading', temperature_reading)) #  Every 5 minutes
    # Repeat task execution
    plantroid_scheduler.run()


def run_sensor_task(task_name, task_fn, period):
    """! Executes a sensor task and schedules the next execution.
    @param task_name <str>: Name of the task.
    @param task_fn <function>: Function to execute for the task.
    @param period <int>: Time period before the task is executed again."""
    readings = task_fn()
    if readings is not None:
        print(f"{task_name}: {readings}")
    plantroid_scheduler.enter(period, 1, run_sensor_task, (task_name, task_fn)) # Schedule next run after period. 


def main():
    """! Main entry point for the script."""
    schedule_sensor_tasks()



if __name__ == "__main__":
    main()