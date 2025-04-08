
# pip install tkinter scikit-learn
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import joblib
import time
from collections import deque
import pandas as pd
import os
from feature_extract import extract_features_with_labels, extract_features_with_windowing

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("User Login")
        self.geometry("900x450")
        self.resizable(True, True)

        # Load all user models
        self.user_models = self.load_models()

        # Create main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Username entry
        ttk.Label(main_frame, text="Username:").pack(pady=5)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.pack(pady=5)

        # Login button
        ttk.Button(main_frame, text="Next", command=self.show_password_window).pack(pady=20)


        # przyklad user name
        ttk.Label(main_frame, text=" Example of username: user_user23").pack(pady=5)
    def load_models(self):
        """Load all isolation forest models from the models directory"""
        models = {}
        model_dir = r"C:\Users\Hubert\Desktop\models"  # Use raw string to handle backslashes

        try:
            for file in os.listdir(model_dir):
                # Check for valid extensions
                if file.endswith('.pkl') or file.endswith('.joblib'):
                    # Extract username from the file name
                    username = file.replace('_model.pkl', '').replace('_isolation_forest.joblib', '')
                    # Build the full path to the model file
                    model_path = os.path.join(model_dir, file)
                    # Load the model
                    models[username] = joblib.load(model_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading models: {str(e)}")

        return models
    # ZWORCI CI DICT  O NAZWIE NP user_user8: <IsolationForest model object>, user_user23 .. itd

    def show_password_window(self):
        username = self.username_entry.get().strip()

        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return

        if username not in self.user_models:
            messagebox.showerror("Error", "User not found")
            return

        # Hide login window
        self.withdraw()

        # Create password window
        PasswordWindow(self, username, self.user_models[username])


class PasswordWindow(tk.Toplevel):
    def __init__(self, parent, username, model):
        super().__init__(parent)

        self.parent = parent
        self.username = username
        self.model = model
        self.correct_password = "haslo"

        self.title("Enter Password")
        self.geometry("400x300")
        self.resizable(True, True)

        # Mouse movement collection variables
        self.mouse_data = deque(maxlen=100)
        self.last_position = None
        self.last_time = None

        self.setup_ui()

        # Bind mouse movement to the entire window
        self.bind('<Motion>', self.on_mouse_move)

        # Bind window resize event
        self.bind('<Configure>', self.on_resize)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Create canvas that fills the entire window
        self.canvas = tk.Canvas(
            self,
            bg='white',
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Create a frame for controls with transparent background
        self.control_frame = ttk.Frame(self)
        self.control_frame.place(relx=0.5, rely=0, anchor='n', y=10)

        # Welcome message
        ttk.Label(
            self.control_frame,
            text=f"Welcome {self.username}!",
            font=('Arial', 12, 'bold')
        ).pack(pady=5)

        # Password entry
        ttk.Label(self.control_frame, text="Password:").pack()
        self.password_entry = ttk.Entry(self.control_frame, show="*")
        self.password_entry.pack(pady=2)

        # Login button
        self.login_button = ttk.Button(
            self.control_frame,
            text="Login",
            command=self.authenticate
        )
        self.login_button.pack(pady=5)

    def on_resize(self, event):
        # Update canvas size when window is resized
        if event.widget == self:
            self.canvas.place(x=0, y=0, width=event.width, height=event.height)

    # Rest of the methods remain the same (authenticate, on_mouse_move, on_close)
    def authenticate(self):
        if len(self.mouse_data) < 10:
            messagebox.showerror("Error", "Please move your mouse more")
            return

        # Check password first
        entered_password = self.password_entry.get()
        if entered_password != self.correct_password:
            messagebox.showerror("Error", "Incorrect password")
            self.password_entry.delete(0, tk.END)
            return

        # Convert collected data to DataFrame
        df = pd.DataFrame(self.mouse_data)

        # Extract features using the external module
        features = extract_features_with_labels(df)

        # Get prediction from the model
        score = self.model.score_samples(features)
        is_authentic = score.mean() > -0.5  # Adjust threshold as needed

        if is_authentic:
            messagebox.showinfo("Success", "Authentication successful!")
            self.parent.destroy()  # Close the entire application
        else:
            messagebox.showerror("Error", "Unusual mouse movement detected")
            self.password_entry.delete(0, tk.END)
            self.canvas.delete('all')
            self.mouse_data.clear()

    def on_mouse_move(self, event):
        current_time = time.time()
        current_pos = (event.x, event.y)

        # Get screen coordinates of the event
        screen_x, screen_y = event.x_root, event.y_root

        # Get control_frame's bounding box in screen coordinates
        frame_x1 = self.control_frame.winfo_rootx()
        frame_y1 = self.control_frame.winfo_rooty()
        frame_x2 = frame_x1 + self.control_frame.winfo_width()
        frame_y2 = frame_y1 + self.control_frame.winfo_height()

        # Skip drawing and data collection if mouse is over the control frame
        if frame_x1 <= screen_x <= frame_x2 and frame_y1 <= screen_y <= frame_y2:
            self.last_position = None
            self.last_time = None
            return
        if not hasattr(self, 'start_time'):
            self.start_time = current_time

        record_timestamp = current_time - self.start_time
        client_timestamp = current_time

        button = "NoButton"
        state = "Move"

        if self.last_position and self.last_time:
            time_diff = current_time - self.last_time
            distance = np.sqrt(
                (current_pos[0] - self.last_position[0]) ** 2 +
                (current_pos[1] - self.last_position[1]) ** 2
            )

            if distance == 0:
                state = "Pressed"
            elif time_diff > 1:
                state = "Released"

            if event.state == 256:
                button = "Left"
                state = "Pressed"
            elif event.state == 512:
                button = "Right"
                state = "Pressed"

            self.mouse_data.append({
                'record timestamp': record_timestamp,
                'client timestamp': client_timestamp,
                'button': button,
                'state': state,
                'x': current_pos[0],
                'y': current_pos[1]
            })

            self.canvas.create_line(
                self.last_position[0],
                self.last_position[1],
                current_pos[0],
                current_pos[1],
                fill='blue',
                width=0.5
            )

        self.last_position = current_pos
        self.last_time = current_time

    def on_close(self):
        self.parent.destroy()


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
