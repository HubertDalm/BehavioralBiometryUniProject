import numpy as np
import pandas as pd


# TO  SA FUNKCJE Z  Z COLLABA
def extract_features_with_labels(df):
    features = {}

    # Sort by timestamp
    df = df.sort_values(by="record timestamp")

    # Calculate time differences
    df['time_diff'] = df['record timestamp'].diff().fillna(0)

    # Movement-based features
    df['distance'] = np.sqrt((df['x'].diff()**2 + df['y'].diff()**2).fillna(0))
    df['speed'] = (df['distance'] / df['time_diff']).replace([np.inf, -np.inf], 0).fillna(0)
    df['acceleration'] = df['speed'].diff().fillna(0)

    features['avg_speed'] = df['speed'].mean()
    features['max_speed'] = df['speed'].max()
    features['avg_acceleration'] = df['acceleration'].mean()

    # Frequency of each state
    state_counts = df['state'].value_counts()
    for state in ['Move', 'Pressed', 'Released', 'Drag']:
        features[f'state_count_{state}'] = state_counts.get(state, 0)

    # Frequency of each button
    button_counts = df['button'].value_counts()
    for button in ['NoButton', 'Left', 'Right']:
        features[f'button_count_{button}'] = button_counts.get(button, 0)

    # State transition counts
    df['state_transition'] = df['state'].shift() + '->' + df['state']
    transition_counts = df['state_transition'].value_counts()
    for transition in ['Move->Pressed', 'Pressed->Released', 'Drag->Released']:
        features[f'state_transition_{transition}'] = transition_counts.get(transition, 0)

    # Average time spent in each state
    state_durations = df.groupby('state')['time_diff'].mean().to_dict()
    for state in ['Move', 'Pressed', 'Released', 'Drag']:
        features[f'avg_duration_{state}'] = state_durations.get(state, 0)

    # Drag-specific features
    drag_data = df[df['state'] == 'Drag']
    features['drag_distance'] = drag_data['distance'].sum()
    features['drag_avg_speed'] = drag_data['speed'].mean() if not drag_data.empty else 0

    # Overall temporal and spatial features
    features['idle_time'] = df['time_diff'][df['time_diff'] > 1].sum()
    time_range = df['record timestamp'].max() - df['record timestamp'].min()
    features['actions_per_second'] = len(df) / time_range if time_range > 0 else 0
    features['avg_x'] = df['x'].mean()
    features['avg_y'] = df['y'].mean()

    return pd.DataFrame([features])

def extract_features_with_windowing(df, window_size=1.0):
    df = df.sort_values(by="record timestamp")
    features_list = []
    start_time = df['record timestamp'].min()
    end_time = df['record timestamp'].max()

    current_start = start_time
    while current_start < end_time:
        current_end = current_start + window_size
        window_data = df[(df['record timestamp'] >= current_start) &
                         (df['record timestamp'] < current_end)]

        if len(window_data) == 0:
            current_start = current_end
            continue

        features = extract_features_with_labels(window_data)
        if 'is_illegal' in window_data.columns:
            majority_label = window_data['is_illegal'].mode()[0]
            features['is_illegal'] = majority_label

        features['start_time'] = current_start
        features_list.append(features)
        current_start = current_end

    features_df = pd.concat(features_list, ignore_index=True)
    return features_df




# class PasswordWindow(tk.Toplevel):
#     def __init__(self, parent, username, model):
#         super().__init__(parent)
#
#         self.parent = parent
#         self.username = username
#         self.model = model
#         self.correct_password = "haslo"
#
#         self.title("Enter Password")
#         self.geometry("400x300")
#         self.resizable(True, True)  # Allow window resizing
#
#         # Mouse movement collection variables
#         self.mouse_data = deque(maxlen=100)
#         self.last_position = None
#         self.last_time = None
#
#         self.setup_ui()
#
#         # Bind mouse movement to the entire window
#         self.bind('<Motion>', self.on_mouse_move)
#
#         # Bind window resize event
#         self.bind('<Configure>', self.on_resize)
#
#         # Handle window close
#         self.protocol("WM_DELETE_WINDOW", self.on_close)
#
#     def setup_ui(self):
#         # Create main frame that fills the window
#         self.main_frame = ttk.Frame(self)
#         self.main_frame.pack(fill=tk.BOTH, expand=True)
#
#         # Create top frame for controls
#         top_frame = ttk.Frame(self.main_frame)
#         top_frame.pack(fill=tk.X, padx=10, pady=5)
#
#         # Welcome message
#         ttk.Label(
#             top_frame,
#             text=f"Welcome {self.username}!",
#             font=('Arial', 12, 'bold')
#         ).pack(side=tk.TOP, pady=5)
#
#         # Password entry
#         ttk.Label(top_frame, text="Password:").pack(side=tk.TOP)
#         self.password_entry = ttk.Entry(top_frame, show="*")
#         self.password_entry.pack(side=tk.TOP, pady=2)
#
#         # Login button
#         self.login_button = ttk.Button(
#             top_frame,
#             text="Login",
#             command=self.authenticate
#         )
#         self.login_button.pack(side=tk.TOP, pady=5)
#
#         # Create canvas that fills the remaining space
#         self.canvas = tk.Canvas(
#             self.main_frame,
#             bg='white',
#             highlightthickness=0  # Remove border
#         )
#         self.canvas.pack(fill=tk.BOTH, expand=True)
#
#     def on_resize(self, event):
#         # Update canvas size when window is resized
#         if event.widget == self:
#             self.canvas.config(width=event.width, height=event.height)
#     def authenticate(self):
#         if len(self.mouse_data) < 10:
#             messagebox.showerror("Error", "Please move your mouse more")
#             return
#
#         # Check password first
#         entered_password = self.password_entry.get()
#         if entered_password != self.correct_password:
#             messagebox.showerror("Error", "Incorrect password")
#             self.password_entry.delete(0, tk.END)
#             return
#
#         # Convert collected data to DataFrame
#         df = pd.DataFrame(self.mouse_data)
#
#         # Extract features using the external module
#         features = extract_features_with_labels(df)
#
#         # Get prediction from the model
#         score = self.model.score_samples(features)
#         is_authentic = score.mean() > -0.5  # Adjust threshold as needed
#
#         if is_authentic:
#             messagebox.showinfo("Success", "Authentication successful!")
#             self.parent.destroy()  # Close the entire application
#         else:
#             messagebox.showerror("Error", "Unusual mouse movement detected")
#             self.password_entry.delete(0, tk.END)
#             self.canvas.delete('all')
#             self.mouse_data.clear()
#
#     def on_mouse_move(self, event):
#         current_time = time.time()
#         current_pos = (event.x, event.y)
#
#         if not hasattr(self, 'start_time'):
#             self.start_time = current_time
#
#         record_timestamp = current_time - self.start_time
#         client_timestamp = current_time
#
#         button = "NoButton"
#         state = "Move"
#
#         if self.last_position and self.last_time:
#             time_diff = current_time - self.last_time
#             distance = np.sqrt(
#                 (current_pos[0] - self.last_position[0]) ** 2 +
#                 (current_pos[1] - self.last_position[1]) ** 2
#             )
#
#             if distance == 0:
#                 state = "Pressed"
#             elif time_diff > 1:
#                 state = "Released"
#
#             if event.state == 256:
#                 button = "Left"
#                 state = "Pressed"
#             elif event.state == 512:
#                 button = "Right"
#                 state = "Pressed"
#
#             self.mouse_data.append({
#                 'record timestamp': record_timestamp,
#                 'client timestamp': client_timestamp,
#                 'button': button,
#                 'state': state,
#                 'x': current_pos[0],
#                 'y': current_pos[1]
#             })
#
#             #Draw movement trail on the entire window area
#             self.canvas.create_line(
#                 self.last_position[0],
#                 self.last_position[1],
#                 current_pos[0],
#                 current_pos[1],
#                 fill='blue',
#                 width=0.5
#             )
#
#         self.last_position = current_pos
#         self.last_time = current_time
#
#     def on_close(self):
#         self.parent.destroy()
