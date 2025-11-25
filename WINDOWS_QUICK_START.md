# Deadlock Detection & Recovery Toolkit
# Quick Start Guide for Windows

## 🚀 One-Click Setup & Run

### Option 1: Double-Click Run (Recommended)
1. **Double-click** `run.bat` in File Explorer
2. Wait for automatic setup (first time only)
3. Dashboard opens at http://localhost:8000

### Option 2: PowerShell Script
1. Right-click `run.ps1`
2. Select "Run with PowerShell"
3. Dashboard opens at http://localhost:8000

### Option 3: Command Line
```cmd
run.bat
```

## 📋 What Happens Automatically

1. ✅ Checks Python installation
2. ✅ Creates virtual environment (if needed)
3. ✅ Installs all required packages:
   - FastAPI (Web framework)
   - Uvicorn (ASGI server)
   - WebSockets (Real-time communication)
   - NetworkX (Graph algorithms)
   - Pydantic (Data validation)
   - Click (CLI framework)
   - PyYAML (YAML parser)
   - Pytest (Testing)
4. ✅ Starts the web dashboard
5. ✅ Opens at http://localhost:8000

## 🎯 Using the Dashboard

1. **Select a Scenario** from the dropdown:
   - Simple Deadlock
   - Dining Philosophers
   - Banker Safe State
   - Banker Unsafe State

2. **Click "Load"** to connect to simulation

3. **Control Simulation**:
   - **Step** - Execute one event at a time
   - **Run All** - Execute all events automatically
   - **Reset** - Restart the simulation

4. **Watch AI Insights** update in real-time:
   - Risk score analysis
   - Performance metrics
   - Smart recommendations
   - Deadlock predictions

## ⚠️ Requirements

- **Windows 10/11**
- **Python 3.9+** installed
- Internet connection (first run only, for downloading packages)

## 🔧 Manual Setup (If Needed)

If the automatic scripts don't work:

```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python -m visualizer.app
```

## 🌐 Access Dashboard

Once running, open your browser to:
**http://localhost:8000**

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal window

## 📂 Project Structure

```
niki/
├── run.bat              ← Double-click this!
├── run.ps1              ← PowerShell alternative
├── engine/              ← Core detection algorithms
├── simulator/           ← Simulation engine
├── visualizer/          ← Web dashboard
├── examples/            ← Demo scenarios
└── tests/               ← Test suite
```

## 🎨 Features

✨ **AI-Powered Intelligence**
- Real-time pattern recognition
- Predictive risk scoring
- Smart recommendations

📊 **Advanced Analytics**
- Resource utilization tracking
- Performance metrics
- Deadlock history analysis

🎯 **Interactive Dashboard**
- Beautiful white theme
- Smooth animations
- Fully responsive design
- Real-time updates

## 🆘 Troubleshooting

**Python not found?**
- Install from https://www.python.org/
- Make sure "Add Python to PATH" is checked

**Port 8000 already in use?**
```cmd
# Find and stop the process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**Dependencies failed to install?**
```cmd
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing again
pip install -r requirements.txt
```

## 📞 Need Help?

Check the main README.md or QUICKSTART.md for more details.

---

**Made with 💜 by the Deadlock Detection Team**
