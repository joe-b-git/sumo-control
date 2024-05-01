import logging
from pynput import keyboard
from controller import SumoController
import os

# Initialize speed and turn
speed, turn = 0, 0

# Create a set to hold the currently pressed keys
current_keys = set()

def on_press(key):
    global speed, turn

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
    global speed, turn

    if key == keyboard.Key.up or key == keyboard.Key.down:
        speed = 0
    elif key == keyboard.Key.left or key == keyboard.Key.right:
        turn = 0

    current_keys.remove(key)

    if key == keyboard.Key.esc:
        # Stop listener
        return False

def main():
    ctrl = SumoController()
    ctrl.connect()

    # Start the listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        while True:
            if keyboard.Key.esc in current_keys:
                break

            # Use the lock when reading shared data
            with ctrl.display.lock:
                print('Person detected:', ctrl.display.person_detected)
                print('Position of the most centered person:', ctrl.display.person_position)

                turn = 0  # Initialize turn

                if ctrl.display.person_detected:
                    # Assuming the center of the image is at x = 320
                    if ctrl.display.person_position[0] < 100:
                        turn = -40
                    elif ctrl.display.person_position[0] < 180:
                        turn = -20
                    elif ctrl.display.person_position[0] < 260:
                        turn = -10  # Turn left
                    elif ctrl.display.person_position[0] > 540:
                        turn = 30
                    elif ctrl.display.person_position[0] > 460:
                        turn = 20
                    elif ctrl.display.person_position[0] > 380:
                        turn = 40  # Turn right

            ctrl.move(speed, turn)

            os.system('clear')  # Clear the terminal screen

if __name__ == '__main__':
    logging.basicConfig(filename='sumo.log', level=logging.INFO)
    main()