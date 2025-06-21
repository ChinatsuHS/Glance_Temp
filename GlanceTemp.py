import sys
import math
import time
import psutil
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect # Import QRect for drawing text
from PyQt5.QtGui import QPainter, QLinearGradient, QColor

# Global flag for GPU temperature monitoring (NVIDIA only)
GPU_MONITOR_AVAILABLE = False
try:
    import pynvml
    GPU_MONITOR_AVAILABLE = True
except ImportError:
    # This message will only appear in the console if running directly,
    # but the application will now show a visual indicator.
    print("NVIDIA monitoring not available - install pynvml for GPU temperature or use an NVIDIA GPU.")


class TemperatureGlowOverlay(QWidget):
    """
    A transparent, always-on-top overlay that displays CPU usage and GPU temperature
    as color-coded glow bars on the edges of the screen, with visual feedback for errors.
    """
    def __init__(self):
        super().__init__()
        # Window setup for a transparent, frameless overlay that stays on top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput | # Allows clicks to pass through
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground) # Makes background transparent
        self.setAttribute(Qt.WA_NoSystemBackground)    # Prevents drawing system background
        
        # Get screen dimensions to make the overlay cover the entire screen
        screen_rect = QApplication.desktop().screenGeometry()
        self.setGeometry(screen_rect)
        
        # Temperature and usage ranges for color mapping
        self.min_temp = 15 # Minimum expected temperature (e.g., idle)
        self.max_temp = 50 # Maximum "normal" temperature before critical (e.g., under load)
        
        # Initial sensor values
        self.gpu_temp = 30
        self.cpu_usage = 10
        
        # Breathing effect parameters for animation
        self.gpu_breath_phase = 0.0
        self.cpu_breath_phase = 0.0
        self.breath_speed = 0.05  # Base breathing speed, increases with load
        
        # Track GPU sensor availability (set during initialization)
        self.gpu_monitor_available = GPU_MONITOR_AVAILABLE
        
        # Status messages for display on the overlay
        # Permanent messages (e.g., no GPU detected)
        self.gpu_permanent_na_message = ""
        # Temporary messages (e.g., transient read errors)
        self.gpu_read_error_message = ""
        self.cpu_read_error_message = ""

        # Timer to clear temporary error messages after a duration
        self.temp_error_clear_timer = QTimer(self)
        self.temp_error_clear_timer.setSingleShot(True) # Timer fires once
        self.temp_error_clear_timer.timeout.connect(self.clear_temporary_errors)
        
        # Initialize hardware sensors (NVIDIA NVML and psutil)
        self.init_sensors()
        
        # Setup update timer to fetch sensor values periodically
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(1000)  # Update every second (1000 ms)
        
        # Animation timer to update breathing effect and repaint
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_breathing)
        self.animation_timer.start(50)  # ~20 FPS animation (50 ms)

    def init_sensors(self):
        """
        Initializes hardware monitoring libraries (NVIDIA NVML) and sets permanent
        GPU status messages if monitoring is not possible.
        """
        if self.gpu_monitor_available:
            try:
                pynvml.nvmlInit() # Initialize NVML
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count > 0:
                    # Get handle to the first GPU device
                    self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                else:
                    # No NVIDIA GPU found, set permanent N/A message
                    self.gpu_permanent_na_message = "No NVIDIA GPU Found"
                    self.gpu_monitor_available = False # Disable further GPU attempts
            except Exception as e:
                # Error during NVML initialization, set permanent N/A message
                self.gpu_permanent_na_message = f"GPU Init Error: {e.__class__.__name__}"
                self.gpu_monitor_available = False # Disable further GPU attempts
        else:
            # pynvml was not imported, set permanent N/A message
            self.gpu_permanent_na_message = "NVIDIA Driver/pynvml Missing"

    def update_values(self):
        """
        Fetches current GPU temperature and CPU usage from system sensors.
        Updates internal values and sets temporary error messages on failure.
        """
        # Clear previous temporary error messages before fetching new values
        self.gpu_read_error_message = ""
        self.cpu_read_error_message = ""

        # Get GPU temperature
        if self.gpu_monitor_available:
            try:
                self.gpu_temp = pynvml.nvmlDeviceGetTemperature(
                    self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except Exception as e:
                # Set temporary GPU read error message
                self.gpu_read_error_message = "GPU Read Fail!"
                print(f"GPU temp read error: {e}") # Log to console for debugging
                self.temp_error_clear_timer.start(3000) # Show error for 3 seconds
        
        # Get CPU usage
        try:
            self.cpu_usage = psutil.cpu_percent(interval=0.5) # Non-blocking call
        except Exception as e:
            # Set temporary CPU read error message
            self.cpu_read_error_message = "CPU Read Fail!"
            print(f"CPU usage read error: {e}") # Log to console for debugging
            self.cpu_usage = 10  # Fallback to default value
            self.temp_error_clear_timer.start(3000) # Show error for 3 seconds
        
        self.update() # Request a repaint to reflect new values or error states

    def clear_temporary_errors(self):
        """
        Clears any temporary GPU or CPU read error messages.
        Called by self.temp_error_clear_timer.
        """
        self.gpu_read_error_message = ""
        self.cpu_read_error_message = ""
        self.update() # Request repaint to clear messages from the screen

    def update_breathing(self):
        """
        Updates the phase of the breathing animation for GPU and CPU based on their load.
        """
        # Update GPU breathing phase based on temperature (if available)
        if self.gpu_monitor_available and not self.gpu_read_error_message:
            # Normalize temperature to 0-1 range for speed calculation
            gpu_norm = (self.gpu_temp - self.min_temp) / (self.max_temp - self.min_temp)
            gpu_norm = max(0.0, min(1.0, gpu_norm)) # Clamp between 0 and 1
            
            # Breathing speed increases with temperature
            gpu_speed = self.breath_speed * (1.0 + gpu_norm * 2.0)
            self.gpu_breath_phase = (self.gpu_breath_phase + gpu_speed) % (2 * math.pi)
        
        # Update CPU breathing phase based on usage
        if not self.cpu_read_error_message:
            cpu_norm = self.cpu_usage / 100.0
            cpu_norm = max(0.0, min(1.0, cpu_norm)) # Clamp between 0 and 1
            
            # Breathing speed increases with CPU usage
            cpu_speed = self.breath_speed * (1.0 + cpu_norm * 2.0)
            self.cpu_breath_phase = (self.cpu_breath_phase + cpu_speed) % (2 * math.pi)
        
        # Trigger repaint for animation frames
        self.update()

    def value_to_color(self, value, is_temp=True, is_available=True):
        """
        Converts a sensor value (temperature or usage) to a QColor.
        Color transitions from green (low) to yellow (medium) to red (high).
        If 'is_available' is False, returns a gray color.
        """
        if not is_available:
            return QColor(100, 100, 100, 150) # Grayed out with some transparency

        # Normalize value between 0 and 1 based on its range
        if is_temp:
            normalized = (value - self.min_temp) / (self.max_temp - self.min_temp)
        else:  # CPU usage
            normalized = value / 100
            
        normalized = max(0.0, min(1.0, normalized)) # Clamp normalized value

        # Define color components based on normalized value for a smooth gradient
        r, g, b = 0, 0, 0
        if normalized < 0.3:  # Green to Yellow transition (0-30% of range)
            r = int(255 * (normalized / 0.3)) # Red component increases
            g = 255
            b = 0
        else:  # Yellow to Red transition (30-100% of range)
            r = 255
            g = int(255 * (1 - (normalized - 0.3) / 0.7)) # Green component decreases
            b = 0
        
        # Adjust alpha (transparency) to be more visible and increase with load
        alpha = 150 + int(80 * normalized)
        
        return QColor(r, g, b, alpha)

    def paintEvent(self, event):
        """
        Draws the glow bars and any status messages on the overlay.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Define bar and glow characteristics
        bar_width = 1 # The initial thin bar width
        glow_width = 25 # The extent of the glowing effect

        # --- Draw GPU related display (left half of the screen) ---
        gpu_display_rect = QRect(0, 0, self.width() // 2, self.height())

        if self.gpu_permanent_na_message or self.gpu_read_error_message:
            # Draw a gray background for the GPU half and display the message
            na_or_error_color = self.value_to_color(0, is_temp=True, is_available=False)
            painter.fillRect(gpu_display_rect, na_or_error_color)
            
            # Set text color and font for the message
            painter.setPen(Qt.white) # White text for contrast
            painter.setFont(painter.font()) # Use default font size for now
            
            # Choose which message to display
            message_to_display = self.gpu_permanent_na_message if self.gpu_permanent_na_message else self.gpu_read_error_message
            painter.drawText(
                gpu_display_rect, # Draw text within the GPU half
                Qt.AlignCenter,   # Center the text
                message_to_display
            )
        else:
            # Draw the normal GPU temperature gradient bar and glow
            gpu_color = self.value_to_color(self.gpu_temp, is_temp=True, is_available=True)
            gpu_gradient = QLinearGradient(0, 0, bar_width, 0)
            gpu_gradient.setColorAt(0.0, gpu_color)
            gpu_gradient.setColorAt(1.0, Qt.transparent)
            painter.fillRect(0, 0, bar_width, self.height(), gpu_gradient)
            
            # Add soft glow to GPU strip with breathing effect
            for i in range(glow_width):
                base_alpha = int(120 * (1 - i/glow_width) * (gpu_color.alpha()/255))
                breath_intensity = (math.sin(self.gpu_breath_phase) + 1) / 2
                breath_intensity = 0.5 + breath_intensity * 0.5
                alpha = int(base_alpha * breath_intensity)
                glow_color = QColor(gpu_color)
                glow_color.setAlpha(alpha)
                painter.setPen(glow_color)
                painter.drawLine(bar_width + i, 0, bar_width + i, self.height())
        
        # --- Draw CPU related display (right half of the screen) ---
        cpu_display_rect = QRect(self.width() // 2, 0, self.width() // 2, self.height())

        if self.cpu_read_error_message:
            # Draw a gray background for the CPU half and display the message
            error_color = self.value_to_color(0, is_temp=False, is_available=False)
            painter.fillRect(cpu_display_rect, error_color)
            
            # Set text color and font for the message
            painter.setPen(Qt.white)
            painter.setFont(painter.font())
            painter.drawText(
                cpu_display_rect, # Draw text within the CPU half
                Qt.AlignCenter,   # Center the text
                self.cpu_read_error_message
            )
        else:
            # Draw the normal CPU usage gradient bar and glow
            cpu_color = self.value_to_color(self.cpu_usage, is_temp=False, is_available=True)
            cpu_gradient = QLinearGradient(self.width(), 0, self.width() - bar_width, 0)
            cpu_gradient.setColorAt(0.0, cpu_color)
            cpu_gradient.setColorAt(1.0, Qt.transparent)
            painter.fillRect(self.width() - bar_width, 0, bar_width, self.height(), cpu_gradient)
            
            # Add soft glow to CPU strip with breathing effect
            for i in range(glow_width):
                base_alpha = int(120 * (1 - i/glow_width) * (cpu_color.alpha()/255))
                breath_intensity = (math.sin(self.cpu_breath_phase) + 1) / 2
                breath_intensity = 0.5 + breath_intensity * 0.5
                alpha = int(base_alpha * breath_intensity)
                glow_color = QColor(cpu_color)
                glow_color.setAlpha(alpha)
                painter.setPen(glow_color)
                painter.drawLine(self.width() - bar_width - i, 0, self.width() - bar_width - i, self.height())

    def closeEvent(self, event):
        """
        Cleans up timers and NVML resources when the application is closed.
        """
        self.update_timer.stop()
        self.animation_timer.stop()
        self.temp_error_clear_timer.stop() # Stop the error clear timer as well
        if self.gpu_monitor_available:
            try:
                pynvml.nvmlShutdown() # Shut down NVML to release resources
            except Exception as e:
                print(f"Error during NVML shutdown: {e}")
        super().closeEvent(event)

# Entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv) # Create the QApplication instance
    overlay = TemperatureGlowOverlay() # Create an instance of our overlay widget
    overlay.show() # Display the overlay
    sys.exit(app.exec_()) # Start the PyQt event loop
