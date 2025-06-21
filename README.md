# **GlanceTemp: Minimalist System Monitor Overlay**

GlanceTemp is a lightweight, transparent, and always-on-top desktop overlay application that provides a quick visual glance at your system's CPU usage and (NVIDIA) GPU temperature. It displays two subtle, color-coded glowing bars on the edges of your screen, with their color and "breathing" intensity dynamically changing based on the current load.

## **✨ Features**

* **Real-time Monitoring:** Instantly see your CPU usage and GPU temperature.  
* **Visual Feedback:** Color-coded bars (Green to Yellow to Red) indicate load levels.  
* **Breathing Effect:** Bars pulse subtly, with pulse speed increasing based on system activity.  
* **Transparent Overlay:** Designed to be unobtrusive and blend into your desktop background.  
* **Always-on-Top:** Stays visible over other applications.  
* **Resource-Friendly:** Built with efficiency in mind.  
* **Error Indicators:** Clear visual messages if GPU monitoring is unavailable or if sensor readings fail.

## **🚀 Installation**

### **Prerequisites**

* Python 3.x  
* PyQt5  
* psutil  
* pynvml (Optional, for NVIDIA GPU monitoring)

### **Steps**

1. **Clone the repository (or download the GlanceTemp.py file):**  
   git clone https://github.com/ChinatsuHS/Glance_Temp.git  
   cd GlanceTemp

2. **Install the required Python packages:**  
   pip install PyQt5 psutil

3. Install pynvml for NVIDIA GPU monitoring (Optional):  
   If you have an NVIDIA GPU and want to monitor its temperature, install pynvml:  
   pip install pynvml

   * **Note:** If pynvml is not installed or if you don't have an NVIDIA GPU, the GPU section of the overlay will display a "NVIDIA Driver/pynvml Missing" or "No NVIDIA GPU Found" message and will not monitor GPU temperature. The CPU monitoring will still function normally.

## **🏃 Usage**

To run the application directly from the script:

python GlanceTemp.py

The overlay will appear, covering your entire screen. It is transparent and click-through, so it won't interfere with your normal mouse interactions.

## **📦 Building an Executable (Windows/macOS/Linux)**

For a standalone application that doesn't require Python to be installed on the end-user's machine, you can build an executable using [PyInstaller](https://pyinstaller.org/).

1. **Install PyInstaller:**  
   pip install pyinstaller

2. Build the executable:  
   Navigate to the directory containing GlanceTemp.py in your terminal and run:  
   pyinstaller \--onefile \--noconsole GlanceTemp.py

   * \--onefile: Creates a single executable file.  
   * \--noconsole: Prevents a console window from appearing when the application runs (recommended for a background tool).

The executable will be generated in the dist/ folder.

* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)  
* [psutil](https://psutil.readthedocs.io/en/latest/)  
* [pynvml](https://pypi.org/project/nvidia-ml-py/)  
* [PyInstaller](https://pyinstaller.org/)
