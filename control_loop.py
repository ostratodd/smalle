import subprocess
import signal
import time
import RPi.GPIO as GPIO
import threading
import logging
from datetime import datetime

from pump.pump_system import pump_system


# Get the current date and time and format the date and time for log file name
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H.%M.%S")
logfile = "LOG_" + formatted_datetime + ".log"
# Configure logging
logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Interrupts gstreamer processes after given hours. Runs in background.
def delayed_interrupt_gstreamer(hours):
    def delayed_execution():
        time.sleep(hours * 3600)  # Convert hours to seconds
        subprocess.Popen(["./cam/interrupt_gstreamer.sh"])

    thread = threading.Thread(target=delayed_execution)
    thread.daemon = True
    thread.start()

# 1st Button Switch Crude Power On/Power Off
# 2nd Button Toggle Camera Preview and Start Recording
# 3rd Graceful emergency shutoff

class smalle():
    def __init__(self):

        # CONFIGURATION VARIABLES
        self.deployment_duration = 0.03 # in hours
        self.preview_state = .5 # minutes to stay in preview state before starting record
        self.pump_time_cooldowns = [3,3,3] # The time in between collections ie: for [3,3,3], pump will trigger at hours 3, 6, and 9 
        self.use_pump_sys = False
        self.use_sipm_sys = False
        self.logintro = "Southwater Belize 2023. Initial setup smalle 4. Fixed lenses. July 1."
        self.dirname = "Southwater2023smalle4"


        # SYSTEM VARIABLES
        self.filters_sampled = 0
        self.pump = pump_system()
        self.graceful_shutoff_toggle_count = 0

        # PIN DEFINITION
        self.preview_toggle = 32
        self.graceful_shutoff_toggle = 31

        self.setUp()

    # Sets up all of the GPIO pins required for the cam system
    def setUp(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.preview_toggle, GPIO.IN)
        GPIO.setup(self.graceful_shutoff_toggle, GPIO.IN)
        GPIO.add_event_detect(self.graceful_shutoff_toggle, GPIO.RISING, callback=self.gracefulShutoff, bouncetime=50)

    # Trigger light beacon
    def lightbeacon(self):
        lightbeacon_proc = subprocess.Popen(["./lightbeacon.sh"])
        lightbeacon_proc.wait()

    # signals the camera process to end while preserving the video footage
    def gracefulShutoff(self, channel):
        self.graceful_shutoff_toggle_count += 1
        if (self.graceful_shutoff_toggle_count > 3):
            subprocess.run(["xset", "-display", ":0.0", "dpms", "force", "on"])
            subprocess.Popen(["./cam/interrupt_gstreamer.sh"])
            self.recording_process.wait()
            self.lightbeacon()
            exit(0)

    def run(self):

    # Preview State
        # Intializes a camera preview
        # Use switch to exit and proceed to recording state
        preview_proc = subprocess.Popen(["./cam/cams_preview.sh"])
        print("Preview Mode")
        print(self.logintro)
        logging.info(self.logintro)

        # Hold in preview mode for the time specified in the setup parameter       
        time.sleep(60 * self.preview_state)
        subprocess.Popen(["./cam/interrupt_gstreamer.sh"])
        preview_proc.wait()
        print("Transitioning to record mode")
        current_datetime = datetime.now()
        logging.info('Transitioning to record mode')
        logging.info(current_datetime)

        ## Run commands to shutoff display
        #subprocess.run(["xset", "-display", ":0.0", "dpms", "force", "off"])
               
        # Original version waited for switch to trigger recording 
        # Could make this a different option at some point, to use switch instead
        ## Waits for the switch trigger to interrupt the preview process
        #GPIO.wait_for_edge(self.preview_toggle, GPIO.FALLING)
        #print("Waiting")
        #subprocess.Popen(["./cam/interrupt_gstreamer.sh"])
        #preview_proc.wait()
        #print("Done!")

        ## Run commands to shutoff display
        #subprocess.run(["xset", "-display", ":0.0", "dpms", "force", "off"])

    # Recording State
        # Camera recording is initialized
        self.recording_process = subprocess.Popen(["./cam/cams_recording.sh", self.dirname])

        # Thread in background that waits for the set deployment duration, which after interrupts the recording process
        delayed_interrupt_gstreamer(self.deployment_duration)

        if self.use_sipm_sys:
            sipm_proc = subprocess.Popen(["./command/to/sipm"]) ## TODO: create callable SiPM python script
        
        # Sleeps until it is time to collect DNA samples (3 in total)
        if self.use_pump_sys:
            for i in range(3):
                time.sleep(3600*self.pump_time_cooldowns[i])
                print("Starting pump " + i)
                current_datetime = datetime.now()
                logging.info('Starting pump ' + i + ' at time: ')
                logging.info(current_datetime)
                self.pump.collectSample(i+1, logfile)
        
        # Waits until recording process ends. delayed_interrupt_gstreamer will interrupt the process.
        self.recording_process.wait()
        if self.use_sipm_sys:
            sipm_proc.terminate()
	
        subprocess.run(["xset", "-display", ":0.0", "dpms", "force", "on"])
        #self.lightbeacon()


# driver code
if __name__ == '__main__':
    s = smalle()
    s.run()
