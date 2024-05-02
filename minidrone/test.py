import logging
from pynput import keyboard
from controller import SumoController
import os

# Initialize speed and turn
speed, turn = 0, 0

# Create a set to hold the currently pressed keys
current_keys = set()

manual_mode = False

def on_press(key):
    global speed, turn, manual_mode

    if manual_mode == True:
        if key == keyboard.Key.up:
            speed = 40
        elif key == keyboard.Key.down:
            speed = -25
        elif key == keyboard.Key.left:
            turn = -25
        elif key == keyboard.Key.right:
            turn = 25

    current_keys.add(key)

def on_release(key):
    global speed, turn, manual_mode

    if key == keyboard.KeyCode(char='m') or key == keyboard.KeyCode(char='M'):
        manual_mode = not manual_mode  # Toggle manual_mode

    if manual_mode == True:
        if key == keyboard.Key.up or key == keyboard.Key.down:
            speed = 0
        elif key == keyboard.Key.left or key == keyboard.Key.right:
            turn = 0

    current_keys.remove(key)

    if key == keyboard.Key.esc:
        # Stop listener
        return False

def main():
    global speed, turn, manual_mode  # Declare speed and turn as global variables

    ctrl = SumoController()
    ctrl.connect()

    # speed, turn = 0, 0  # Initialize turn

    # Start the listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        while True:
            if keyboard.Key.esc in current_keys:
                break

            if manual_mode == False:
                # Use the lock when reading shared data
                with ctrl.display.lock:
                    print('Person detected:', ctrl.display.person_detected)
                    print('Position of the most centered person:', ctrl.display.person_position)

                    # speed, turn = 0, 0  # Initialize turn

                    if ctrl.display.person_detected:
                        # Assuming the center of the image is at x = 320
                        if ctrl.display.person_position[0] < 60:
                            turn = -60
                        elif ctrl.display.person_position[0] < 120:
                            turn = -40
                        elif ctrl.display.person_position[0] < 180:
                            turn = -20
                        elif ctrl.display.person_position[0] < 260:
                            turn = -10  # Turn left
                        elif ctrl.display.person_position[0] > 580:
                            turn = 60
                        elif ctrl.display.person_position[0] > 520:
                            turn = 40
                        elif ctrl.display.person_position[0] > 460:
                            turn = 20
                        elif ctrl.display.person_position[0] > 380:
                            turn = 10  # Turn right
                        else:
                            turn = 0

                        if ctrl.display.person_position[1] < 400:
                            speed = 60
                        if ctrl.display.person_position[1] < 440:
                            speed = 40
                        elif ctrl.display.person_position[1] > 460:
                            speed = -30
                        else:
                            turn = 0
                    else:
                        speed, turn = 0, 0
                    
                    # P-controller attempt
                    # if ctrl.display.person_detected:
                    #     # Assuming the center of the image is at x = 320
                    #     error = ctrl.display.person_position[0] - 320
                    #     turn = int(error * 0.1)  # Proportional control

                    #     # # Assuming the center of the image is at y = 450
                    #     # error_y = ctrl.display.person_position[1] - 450
                    #     # speed = -error_y * 0.1  # Proportional control

            if speed > 100: speed = 100
            if speed < -100: speed = -100
            if turn > 100: turn = 100
            if turn < -100: turn = -100

            ctrl.move(speed, turn)

            os.system('clear')  # Clear the terminal screen

if __name__ == '__main__':
    logging.basicConfig(filename='sumo.log', level=logging.INFO)
    main()