import pandas as pd
import time
import numpy as np
import threading
import random
from scipy.stats import truncnorm

# Motor Agent
class Motor:
    def __init__(self, failure_interval=1, amplitude_values_per_failure=30):  # Updated parameters
        self.failure_interval = failure_interval  # Time between failures (in seconds)
        self.amplitude_values_per_failure = amplitude_values_per_failure  # Amplitude values per failure
        self.vibration_data = pd.DataFrame(columns=["time", "amplitude"])
        self.running = True
        self.failure_count = 0
        self.failure_detected = False

    def generate_data(self, total_failures):
        start_time = time.time()
        while self.running and self.failure_count < total_failures:
            current_time = time.time() - start_time
            if current_time >= (self.failure_count + 1) * self.failure_interval:
                # Define the range for the truncated normal distribution
                lower_bound = 80
                upper_bound = 150
                mean = 115
                std_dev = 80

                # Scale the bounds to the standard normal distribution
                a = (lower_bound - mean) / std_dev
                b = (upper_bound - mean) / std_dev

                # Generate a random value from the truncated normal distribution
                peak_amplitude = truncnorm.rvs(a, b, loc=mean, scale=std_dev)
                self.vibration_data.loc[len(self.vibration_data)] = [current_time, peak_amplitude]
                self.failure_count += 1
                self.failure_detected = True
                print(f"Motor: Failure {self.failure_count} detected at {current_time:.2f}s with an amplitude of {peak_amplitude}!")
            else:
                # Generate normal vibration data
                amplitude = np.random.normal(30, 10)  # Normal vibration
                self.vibration_data.loc[len(self.vibration_data)] = [current_time, amplitude]
            time.sleep(self.failure_interval / self.amplitude_values_per_failure)  # Adjusted sleep time

    def get_data(self):
        return self.vibration_data

# Transductor SCADA Display Agent
class TransductorSCADA:
    def __init__(self, motor):
        self.motor = motor
        self.running = True

    def display_data(self):
        while self.running:
            data = self.motor.get_data()
            if not data.empty:
                latest_time = data["time"].iloc[-1]
                latest_amplitude = data["amplitude"].iloc[-1]
                print(f"SCADA Display: Time = {latest_time:.2f}s, Amplitude = {latest_amplitude:.2f}")
            if self.motor.failure_detected:
                self.motor.failure_detected = False  # Reset for the next failure
            if not self.motor.running:
                self.running = False
            time.sleep(0.1)

# Crew Member Agent
class CrewMember:
    def __init__(self, transductor, accuracy=0.8):
        self.transductor = transductor
        self.accuracy = accuracy  # Probability of detecting the failure
        self.correct_predictions = 0  # Counter for correct predictions
        self.last_failure_evaluated = -1  # Track the last failure evaluated

    def monitor(self):
        while self.transductor.running:
            data = self.transductor.motor.get_data()
            if not data.empty:
                latest_time = data["time"].iloc[-1]
                latest_amplitude = data["amplitude"].iloc[-1]
                # Check if a failure has occurred and if it hasn't been evaluated yet
                if latest_amplitude > 50 and self.transductor.motor.failure_count > self.last_failure_evaluated:
                    if random.random() < self.accuracy:
                        print(f"Crew Member: Failure {self.transductor.motor.failure_count} predicted!")
                        self.correct_predictions += 1
                    else:
                        print(f"Crew Member: Missed failure {self.transductor.motor.failure_count}.")
                    self.last_failure_evaluated = self.transductor.motor.failure_count  # Mark this failure as evaluated
            time.sleep(0.1)

# Main Simulation
if __name__ == "__main__":
    # User input
    total_failures = int(input("Enter the number of failures to evaluate: "))
    accuracy = float(input("Enter the accuracy of the Crew Member (0 to 1): "))

    # Initialize agents
    motor = Motor(failure_interval=1, amplitude_values_per_failure=30)  # Updated parameters
    transductor = TransductorSCADA(motor)
    crew_member = CrewMember(transductor, accuracy=accuracy)

    # Start threads
    motor_thread = threading.Thread(target=motor.generate_data, args=(total_failures,))
    transductor_thread = threading.Thread(target=transductor.display_data)
    crew_thread = threading.Thread(target=crew_member.monitor)

    motor_thread.start()
    transductor_thread.start()
    crew_thread.start()

    # Wait for threads to finish
    motor_thread.join()
    transductor.running = False
    crew_thread.join()

    # Final output
    print("\nSimulation Results:")
    print(f"Total failures evaluated: {motor.failure_count}")
    print(f"Correct predictions by Crew Member: {crew_member.correct_predictions}")
    if motor.failure_count > 0:
        prediction_percentage = (crew_member.correct_predictions / motor.failure_count) * 100
        print(f"Prediction accuracy: {prediction_percentage:.2f}%")
    else:
        print("No failures occurred during the simulation.")