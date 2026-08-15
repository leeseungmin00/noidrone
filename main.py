import tkinter as tk
import GUI

if __name__ == "__main__":
    root = tk.Tk()
    app = GUI.DroneMissionGUI(root, "Integrated Tello Drone Mission Control Station")
    root.mainloop()