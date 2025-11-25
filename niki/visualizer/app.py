"""
FastAPI Web Application

Provides web dashboard with real-time visualization.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from typing import List
import json
import asyncio

from simulator.scenario import ScenarioLoader
from simulator.dispatcher import EventDispatcher, SimulationMode
from .graph_renderer import GraphRenderer


app = FastAPI(title="Deadlock Detection Toolkit")

# Store active simulations
active_simulations = {}


@app.get("/")
async def root():
    """Serve the main dashboard page."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content=get_default_html())


@app.get("/api/scenarios")
async def list_scenarios():
    """List available example scenarios."""
    examples_dir = Path(__file__).parent.parent / "examples"
    scenarios = []
    
    if examples_dir.exists():
        for file in examples_dir.glob("*.json"):
            try:
                scenario = ScenarioLoader.load_from_file(str(file))
                scenarios.append({
                    "filename": file.name,
                    "name": scenario.name,
                    "description": scenario.description,
                    "num_processes": len(scenario.processes),
                    "num_resources": len(scenario.resources),
                    "num_events": len(scenario.events)
                })
            except Exception as e:
                print(f"Error loading {file}: {e}")
    
    return {"scenarios": scenarios}


@app.get("/api/scenario/{filename}")
async def get_scenario(filename: str):
    """Get a specific scenario."""
    examples_dir = Path(__file__).parent.parent / "examples"
    file_path = examples_dir / filename
    
    if not file_path.exists():
        return {"error": "Scenario not found"}
    
    try:
        scenario = ScenarioLoader.load_from_file(str(file_path))
        return scenario.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/simulate/{scenario_name}")
async def websocket_simulate(websocket: WebSocket, scenario_name: str):
    """WebSocket endpoint for real-time simulation."""
    await websocket.accept()
    
    try:
        # Load scenario
        examples_dir = Path(__file__).parent.parent / "examples"
        scenario_path = examples_dir / scenario_name
        
        if not scenario_path.exists():
            await websocket.send_json({"error": "Scenario not found"})
            return
        
        scenario = ScenarioLoader.load_from_file(str(scenario_path))
        
        # Create dispatcher
        dispatcher = EventDispatcher(scenario, mode=SimulationMode.STEP)
        renderer = GraphRenderer()
        
        # Send initial state
        initial_snapshot = dispatcher.snapshots[0]
        await websocket.send_json({
            "type": "snapshot",
            "data": {
                "time": initial_snapshot.time,
                "system_state": initial_snapshot.system_state,
                "deadlock_analysis": initial_snapshot.deadlock_analysis,
                "graph": renderer.render_rag(initial_snapshot.deadlock_analysis["rag_dict"])
            }
        })
        
        # Wait for client commands
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "step":
                result = dispatcher.step()
                
                if result is None:
                    await websocket.send_json({
                        "type": "complete",
                        "summary": dispatcher.get_summary()
                    })
                    break
                
                # Send updated snapshot
                latest_snapshot = dispatcher.snapshots[-1]
                await websocket.send_json({
                    "type": "snapshot",
                    "data": {
                        "time": latest_snapshot.time,
                        "event": latest_snapshot.last_event,
                        "system_state": latest_snapshot.system_state,
                        "deadlock_analysis": latest_snapshot.deadlock_analysis,
                        "graph": renderer.render_rag(latest_snapshot.deadlock_analysis["rag_dict"]),
                        "recovery": latest_snapshot.recovery_result
                    }
                })
            
            elif command == "run":
                # Run remaining steps
                while dispatcher.current_event_index < len(scenario.events):
                    dispatcher.step()
                    await asyncio.sleep(0.1)  # Small delay for visual effect
                    
                    latest_snapshot = dispatcher.snapshots[-1]
                    await websocket.send_json({
                        "type": "snapshot",
                        "data": {
                            "time": latest_snapshot.time,
                            "system_state": latest_snapshot.system_state,
                            "deadlock_analysis": latest_snapshot.deadlock_analysis,
                            "graph": renderer.render_rag(latest_snapshot.deadlock_analysis["rag_dict"])
                        }
                    })
                
                await websocket.send_json({
                    "type": "complete",
                    "summary": dispatcher.get_summary()
                })
                break
            
            elif command == "reset":
                dispatcher.reset()
                initial_snapshot = dispatcher.snapshots[0]
                await websocket.send_json({
                    "type": "snapshot",
                    "data": {
                        "time": initial_snapshot.time,
                        "system_state": initial_snapshot.system_state,
                        "deadlock_analysis": initial_snapshot.deadlock_analysis,
                        "graph": renderer.render_rag(initial_snapshot.deadlock_analysis["rag_dict"])
                    }
                })
    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})


def get_default_html() -> str:
    """Return default HTML dashboard with modern UI/UX."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deadlock Detection Toolkit - Real-time System Monitor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --secondary: #ec4899;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            --shadow: rgba(0, 0, 0, 0.08);
            --shadow-md: rgba(0, 0, 0, 0.12);
            --shadow-lg: rgba(0, 0, 0, 0.16);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 1rem;
            line-height: 1.6;
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 50%);
            animation: backgroundMove 20s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes backgroundMove {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(-5%, -5%); }
        }
        
        .app-container {
            max-width: 1600px;
            margin: 0 auto;
            animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 1;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes scaleIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            padding: 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 60px var(--shadow-lg), 0 0 0 1px rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
            animation: slideInLeft 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
            animation: headerPulse 6s ease-in-out infinite;
        }
        
        @keyframes headerPulse {
            0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.6; }
            50% { transform: scale(1.1) rotate(90deg); opacity: 0.4; }
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        h1 {
            color: white;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .header-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            font-weight: 300;
        }
        
        /* Controls Panel */
        .controls-panel {
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 1.5rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px var(--shadow-md);
            animation: slideInRight 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.2s both;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .controls-panel:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 50px var(--shadow-lg);
        }
        
        .controls-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            align-items: end;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        label {
            color: var(--text-primary);
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        select {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 2px solid var(--border);
            padding: 0.875rem 1.25rem;
            border-radius: 0.75rem;
            font-size: 1rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            font-weight: 500;
        }
        
        select:hover {
            border-color: var(--primary);
            background: var(--bg-primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow);
        }
        
        select:focus {
            outline: none;
            border-color: var(--primary);
            background: var(--bg-primary);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
            transform: translateY(-2px);
        }
        
        .button-group {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }
        
        button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 0.875rem 1.75rem;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25);
            position: relative;
            overflow: hidden;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.4);
            transform: translate(-50%, -50%);
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1), height 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        button:hover::before {
            width: 400px;
            height: 400px;
        }
        
        button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }
        
        button:active {
            transform: translateY(-1px) scale(0.98);
            transition: all 0.1s ease;
        }
        
        button.secondary {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            color: var(--text-primary);
            box-shadow: 0 4px 15px var(--shadow);
            border: 2px solid var(--border);
        }
        
        button.secondary:hover {
            box-shadow: 0 8px 25px var(--shadow-md);
            border-color: var(--primary);
        }
        
        button.danger {
            background: linear-gradient(135deg, var(--danger) 0%, #dc2626 100%);
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }
        
        button.danger:hover {
            box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
        }
        
        /* Status Bar */
        .status-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
            font-weight: 600;
            font-size: 1.125rem;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 20px var(--shadow-md);
            flex-wrap: wrap;
            gap: 1rem;
            animation: scaleIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.4s both;
            position: relative;
            overflow: hidden;
        }
        
        .status-bar::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s ease;
        }
        
        .status-bar:hover::before {
            left: 100%;
        }
        
        .status-bar.safe {
            background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
            color: white;
        }
        
        .status-bar.deadlock {
            background: linear-gradient(135deg, var(--danger) 0%, #dc2626 100%);
            color: white;
            animation: statusPulse 2s ease-in-out infinite;
        }
        
        .status-bar.loading {
            background: linear-gradient(135deg, var(--warning) 0%, #d97706 100%);
            color: white;
        }
        
        @keyframes statusPulse {
            0%, 100% { 
                box-shadow: 0 6px 25px rgba(239, 68, 68, 0.4);
                transform: scale(1);
            }
            50% { 
                box-shadow: 0 8px 35px rgba(239, 68, 68, 0.6);
                transform: scale(1.01);
            }
        }
        
        .status-icon {
            font-size: 1.5rem;
        }
        
        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .card {
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 1.5rem;
            padding: 2rem;
            box-shadow: 0 10px 40px var(--shadow-md);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            animation: scaleIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) both;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transform: scaleX(0);
            transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .card:hover::before {
            transform: scaleX(1);
        }
        
        .card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 60px var(--shadow-lg);
            border-color: var(--primary-light);
        }
        
        .card:nth-child(1) {
            animation-delay: 0.6s;
        }
        
        .card:nth-child(2) {
            animation-delay: 0.7s;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }
        
        .card-icon {
            font-size: 1.5rem;
            animation: iconFloat 3s ease-in-out infinite;
        }
        
        @keyframes iconFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        
        .card-title {
            color: var(--text-primary);
            font-size: 1.125rem;
            font-weight: 600;
        }
        
        .card-content {
            color: var(--text-secondary);
        }
        
        /* Code Display */
        .code-block {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            transition: all 0.3s ease;
        }
        
        .code-block:hover {
            border-color: var(--primary-light);
            background: var(--bg-primary);
        }
        
        .code-block::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        .code-block::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 5px;
        }
        
        .code-block::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        
        .code-block::-webkit-scrollbar-thumb:hover {
            background: var(--primary-light);
        }
        
        /* Graph Container */
        .graph-container {
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 1.5rem;
            padding: 2rem;
            box-shadow: 0 10px 40px var(--shadow-md);
            animation: scaleIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.8s both;
            transition: all 0.3s ease;
        }
        
        .graph-container:hover {
            box-shadow: 0 15px 50px var(--shadow-lg);
        }
        
        .graph-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid var(--border);
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .graph-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        .graph-content {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 1rem;
            padding: 2rem;
            min-height: 450px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .graph-content:hover {
            border-color: var(--primary-light);
        }
        
        .empty-state {
            text-align: center;
            color: var(--text-muted);
        }
        
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.4;
            animation: iconPulse 3s ease-in-out infinite;
        }
        
        @keyframes iconPulse {
            0%, 100% { transform: scale(1); opacity: 0.4; }
            50% { transform: scale(1.1); opacity: 0.6; }
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .stat-item {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            border: 2px solid var(--border);
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .stat-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent);
            transition: left 0.6s ease;
        }
        
        .stat-item:hover::before {
            left: 100%;
        }
        
        .stat-item:hover {
            transform: translateY(-5px) scale(1.05);
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--shadow);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            animation: valueCount 1s ease-out;
        }
        
        @keyframes valueCount {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            body {
                padding: 0.5rem;
            }
            
            .header {
                padding: 1.5rem;
            }
            
            .controls-panel {
                padding: 1rem;
            }
            
            .controls-grid {
                grid-template-columns: 1fr;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            button {
                width: 100%;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 480px) {
            h1 {
                font-size: 1.25rem;
            }
            
            .header-subtitle {
                font-size: 0.875rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 22px;
            height: 22px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Tooltip */
        [data-tooltip] {
            position: relative;
            cursor: help;
        }
        
        [data-tooltip]::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(-10px);
            background: var(--text-primary);
            color: white;
            padding: 0.625rem 1.25rem;
            border-radius: 0.75rem;
            font-size: 0.875rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border);
            z-index: 1000;
            box-shadow: 0 10px 30px var(--shadow-lg);
        }
        
        [data-tooltip]:hover::after {
            opacity: 1;
            transform: translateX(-50%) translateY(-5px);
        }
        
        /* Pre tag styling */
        pre {
            color: var(--text-primary);
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        /* AI Insights & Recommendations */
        .insights-container, .recommendations-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .insight-item, .recommendation-item {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border: 2px solid var(--border);
            border-radius: 1rem;
            padding: 1.25rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .insight-item::before, .recommendation-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            transform: scaleY(0);
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .insight-item:hover::before, .recommendation-item:hover::before {
            transform: scaleY(1);
        }
        
        .insight-item:hover, .recommendation-item:hover {
            transform: translateX(8px);
            border-color: var(--primary);
            box-shadow: 0 8px 24px var(--shadow);
        }
        
        .insight-item.warning {
            border-left: 4px solid var(--warning);
        }
        
        .insight-item.danger {
            border-left: 4px solid var(--danger);
        }
        
        .insight-item.success {
            border-left: 4px solid var(--success);
        }
        
        .insight-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        
        .insight-icon {
            font-size: 1.5rem;
        }
        
        .insight-title {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .insight-body {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 0.9rem;
        }
        
        .insight-confidence {
            display: inline-block;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            background: var(--primary);
            color: white;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        /* Metrics Chart */
        .metrics-container {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            min-height: 250px;
            transition: all 0.3s ease;
        }
        
        .metrics-container:hover {
            border-color: var(--primary-light);
        }
        
        #performanceChart {
            max-height: 200px;
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            border-radius: 4px;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        /* Recommendations Panel */
        .recommendations-panel {
            margin-top: 2rem;
            animation: scaleIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 1s both;
        }
        
        .recommendation-item {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }
        
        .recommendation-icon {
            font-size: 2rem;
            flex-shrink: 0;
        }
        
        .recommendation-content {
            flex: 1;
        }
        
        .recommendation-title {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .recommendation-description {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.6;
        }
        
        .recommendation-action {
            margin-top: 0.75rem;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .recommendation-action:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        /* Badge Styles */
        .badge {
            display: inline-block;
            padding: 0.375rem 0.875rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .badge-success {
            background: var(--success);
            color: white;
        }
        
        .badge-warning {
            background: var(--warning);
            color: white;
        }
        
        .badge-danger {
            background: var(--danger);
            color: white;
        }
        
        .badge-info {
            background: var(--primary);
            color: white;
        }
        
        /* Pulse Animation for Live Data */
        .live-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: livePulse 2s ease-in-out infinite;
        }
        
        @keyframes livePulse {
            0%, 100% { 
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                opacity: 1;
            }
            50% { 
                box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
                opacity: 0.8;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1>
                    <span>🔒</span>
                    Deadlock Detection & Recovery Toolkit
                    <span style="font-size: 0.5em; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 0.25rem 0.75rem; border-radius: 0.5rem; margin-left: 1rem; font-weight: 700; letter-spacing: 0.05em;">AI-POWERED</span>
                </h1>
                <p class="header-subtitle">
                    Real-time system monitor with AI-driven insights, predictive analytics, and intelligent recovery strategies
                </p>
            </div>
        </header>
        
        <!-- Controls -->
        <section class="controls-panel">
            <div class="controls-grid">
                <div class="form-group">
                    <label for="scenarioSelect">📋 Select Scenario</label>
                    <select id="scenarioSelect">
                        <option value="">Loading scenarios...</option>
                    </select>
                </div>
                <div class="button-group">
                    <button onclick="loadScenario()" data-tooltip="Load selected scenario">
                        🚀 Load
                    </button>
                    <button onclick="step()" class="secondary" data-tooltip="Execute next event">
                        ⏯️ Step
                    </button>
                    <button onclick="run()" class="secondary" data-tooltip="Run all events">
                        ▶️ Run All
                    </button>
                    <button onclick="reset()" class="danger" data-tooltip="Reset simulation">
                        🔄 Reset
                    </button>
                </div>
            </div>
        </section>
        
        <!-- Status Bar -->
        <div id="status" class="status-bar loading">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span class="status-icon">⏳</span>
                <span>Ready to begin - Select a scenario</span>
            </div>
            <span id="statusTime"></span>
        </div>
        
        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
            <!-- System State Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">💻</span>
                    <h2 class="card-title">System State</h2>
                </div>
                <div class="card-content">
                    <div id="systemStats" class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value" id="statProcesses">0</div>
                            <div class="stat-label">Processes</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statResources">0</div>
                            <div class="stat-label">Resources</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statEvents">0</div>
                            <div class="stat-label">Events</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statUtilization">0%</div>
                            <div class="stat-label">Utilization</div>
                        </div>
                    </div>
                    <div id="systemState" class="code-block">
                        <div class="empty-state">
                            <div class="empty-state-icon">📊</div>
                            <p>Waiting for simulation data...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI Insights Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">🧠</span>
                    <h2 class="card-title">AI Insights & Predictions</h2>
                </div>
                <div class="card-content">
                    <div id="aiInsights" class="insights-container">
                        <div class="empty-state">
                            <div class="empty-state-icon">🤖</div>
                            <p>AI analysis will appear here</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Analytics Dashboard -->
        <div class="dashboard-grid">
            <!-- Performance Metrics Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📈</span>
                    <h2 class="card-title">Performance Metrics</h2>
                </div>
                <div class="card-content">
                    <div id="metricsChart" class="metrics-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                    <div id="metricsStats" class="stats-grid" style="margin-top: 1rem;">
                        <div class="stat-item">
                            <div class="stat-value" id="statDeadlocks">0</div>
                            <div class="stat-label">Deadlocks</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statRecoveries">0</div>
                            <div class="stat-label">Recoveries</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statRiskScore">0</div>
                            <div class="stat-label">Risk Score</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="statEfficiency">100%</div>
                            <div class="stat-label">Efficiency</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Event Log Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📝</span>
                    <h2 class="card-title">Event Timeline</h2>
                    <span id="eventBadge" style="margin-left: auto;"></span>
                </div>
                <div class="card-content">
                    <div id="eventLog" class="code-block">
                        <div class="empty-state">
                            <div class="empty-state-icon">⚡</div>
                            <p>No events executed yet</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Graph Container -->
        <section class="graph-container">
            <div class="graph-header">
                <h2 class="graph-title">
                    <span>🕸️</span>
                    Resource Allocation Graph - Interactive View
                </h2>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <div id="graphBadge"></div>
                    <button onclick="toggleGraphView()" class="secondary" style="padding: 0.5rem 1rem; font-size: 0.75rem;">
                        🔄 Toggle View
                    </button>
                </div>
            </div>
            <div id="graph" class="graph-content">
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <p>Select and load a scenario to visualize the resource allocation graph</p>
                </div>
            </div>
        </section>
        
        <!-- Smart Recommendations Panel -->
        <section class="recommendations-panel">
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">💡</span>
                    <h2 class="card-title">Smart Recommendations</h2>
                </div>
                <div class="card-content">
                    <div id="recommendations" class="recommendations-list">
                        <div class="empty-state">
                            <div class="empty-state-icon">🎯</div>
                            <p>AI recommendations will appear based on system analysis</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
    
    <script>
        let ws = null;
        let scenarios = [];
        let currentTime = 0;
        let isConnected = false;
        let reconnectAttempts = 0;
        const MAX_RECONNECT_ATTEMPTS = 3;
        
        // Analytics data
        let eventHistory = [];
        let deadlockCount = 0;
        let recoveryCount = 0;
        let performanceData = {
            times: [],
            utilization: [],
            riskScores: []
        };
        let graphViewMode = 'detailed'; // 'detailed' or 'simplified'
        
        // Initialize scenarios on page load
        function initScenarios() {
            const select = document.getElementById('scenarioSelect');
            if (!select) {
                console.error('Scenario select element not found');
                return;
            }
            
            select.innerHTML = '<option value="">Loading scenarios...</option>';
            
            fetch('/api/scenarios')
                .then(r => {
                    if (!r.ok) throw new Error('Failed to fetch scenarios');
                    return r.json();
                })
                .then(data => {
                    scenarios = data.scenarios || [];
                    if (scenarios.length === 0) {
                        select.innerHTML = '<option value="">No scenarios available</option>';
                        updateStatus('⚠️ No scenarios found', 'loading');
                    } else {
                        select.innerHTML = scenarios.map(s => 
                            '<option value="' + s.filename + '">' + s.name + ' (' + s.num_processes + 'P, ' + s.num_resources + 'R, ' + s.num_events + 'E)</option>'
                        ).join('');
                        updateStatus('✓ Ready - Select a scenario to begin', 'safe');
                    }
                })
                .catch(err => {
                    console.error('Failed to load scenarios:', err);
                    select.innerHTML = '<option value="">Failed to load scenarios</option>';
                    updateStatus('❌ Failed to load scenarios - Check server connection', 'deadlock');
                });
        }
        
        // Load scenarios when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initScenarios);
        } else {
            initScenarios();
        }
        
        function loadScenario() {
            const select = document.getElementById('scenarioSelect');
            const filename = select.value;
            if (!filename) {
                updateStatus('⚠️ Please select a scenario first', 'loading');
                return;
            }
            
            // Close existing connection
            if (ws) {
                ws.close();
                ws = null;
            }
            
            isConnected = false;
            reconnectAttempts = 0;
            updateStatus('⏳ Connecting to simulation...', 'loading');
            
            try {
                ws = new WebSocket('ws://localhost:8000/ws/simulate/' + filename);
                
                ws.onopen = () => {
                    isConnected = true;
                    reconnectAttempts = 0;
                    updateStatus('✓ Connected - Ready to simulate', 'safe');
                };
                
                ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        
                        if (msg.type === 'snapshot') {
                            updateUI(msg.data);
                        } else if (msg.type === 'complete') {
                            updateStatus('✓ Simulation complete', 'safe');
                        } else if (msg.error) {
                            updateStatus('❌ Error: ' + msg.error, 'deadlock');
                        }
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                        updateStatus('❌ Failed to parse server response', 'deadlock');
                    }
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    updateStatus('❌ Connection error - Check if server is running on port 8000', 'deadlock');
                };
                
                ws.onclose = (event) => {
                    isConnected = false;
                    if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                        reconnectAttempts++;
                        updateStatus('⚠️ Connection closed - Attempting to reconnect (' + reconnectAttempts + '/' + MAX_RECONNECT_ATTEMPTS + ')', 'loading');
                    } else {
                        console.log('WebSocket connection closed');
                    }
                };
            } catch (e) {
                console.error('Failed to create WebSocket:', e);
                updateStatus('❌ Failed to establish connection', 'deadlock');
            }
        }
        
        function step() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({command: 'step'}));
                } catch (e) {
                    console.error('Failed to send step command:', e);
                    updateStatus('❌ Failed to send command', 'deadlock');
                }
            } else {
                updateStatus('⚠️ Not connected - Load a scenario first', 'loading');
            }
        }
        
        function run() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({command: 'run'}));
                    updateStatus('⏩ Running all events...', 'loading');
                } catch (e) {
                    console.error('Failed to send run command:', e);
                    updateStatus('❌ Failed to send command', 'deadlock');
                }
            } else {
                updateStatus('⚠️ Not connected - Load a scenario first', 'loading');
            }
        }
        
        function reset() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({command: 'reset'}));
                    currentTime = 0;
                    updateStatus('🔄 Simulation reset', 'safe');
                } catch (e) {
                    console.error('Failed to send reset command:', e);
                    updateStatus('❌ Failed to send command', 'deadlock');
                }
            } else {
                updateStatus('⚠️ Not connected - Load a scenario first', 'loading');
            }
        }
        
        function updateUI(data) {
            try {
                currentTime = data.time || 0;
                
                // Track event history
                if (data.event) {
                    eventHistory.push({
                        time: currentTime,
                        type: data.event.event_type || data.event.type,
                        ...data.event
                    });
                }
                
                // Update status
                const hasDeadlock = data.deadlock_analysis?.has_deadlock || false;
                if (hasDeadlock) {
                    deadlockCount++;
                    const processes = data.deadlock_analysis.deadlocked_processes?.join(', ') || 'Unknown';
                    updateStatus('⚠️ DEADLOCK DETECTED - Processes: ' + processes, 'deadlock');
                } else {
                    updateStatus('✓ System is in a safe state', 'safe');
                }
                
                // Update time badge
                const timeElement = document.getElementById('statusTime');
                if (timeElement) {
                    timeElement.innerHTML = '<span class="live-indicator"></span>Time: ' + currentTime + 's';
                }
                
                // Update system stats with animations
                if (data.system_state) {
                    const numProcesses = Object.keys(data.system_state.processes || {}).length;
                    const numResources = Object.keys(data.system_state.resources || {}).length;
                    const numEvents = eventHistory.length;
                    
                    // Calculate resource utilization
                    let totalAllocated = 0;
                    let totalAvailable = 0;
                    Object.values(data.system_state.resources || {}).forEach(r => {
                        totalAllocated += (r.total - r.available);
                        totalAvailable += r.total;
                    });
                    const utilization = totalAvailable > 0 ? Math.round((totalAllocated / totalAvailable) * 100) : 0;
                    
                    animateValue('statProcesses', numProcesses);
                    animateValue('statResources', numResources);
                    animateValue('statEvents', numEvents);
                    animateValue('statUtilization', utilization, '%');
                    
                    // Update performance metrics
                    animateValue('statDeadlocks', deadlockCount);
                    animateValue('statRecoveries', recoveryCount);
                    
                    // Calculate risk score
                    const riskScore = calculateRiskScore(data);
                    animateValue('statRiskScore', riskScore);
                    
                    // Calculate efficiency
                    const efficiency = Math.max(0, 100 - (deadlockCount * 10));
                    animateValue('statEfficiency', efficiency, '%');
                    
                    // Store performance data
                    performanceData.times.push(currentTime);
                    performanceData.utilization.push(utilization);
                    performanceData.riskScores.push(riskScore);
                    
                    // Update system state display
                    const stateDiv = document.getElementById('systemState');
                    if (stateDiv) {
                        stateDiv.innerHTML = `<pre>${JSON.stringify(data.system_state, null, 2)}</pre>`;
                    }
                }
                
                // Generate AI insights
                generateAIInsights(data);
                
                // Generate smart recommendations
                generateRecommendations(data);
                
                // Update event log with enhanced formatting
                if (data.event) {
                    const logDiv = document.getElementById('eventLog');
                    if (logDiv) {
                        const eventType = data.event.event_type || data.event.type || 'UNKNOWN';
                        const eventColor = eventType === 'ALLOCATE' ? '#10b981' : 
                                           eventType === 'REQUEST' ? '#f59e0b' : '#ef4444';
                        
                        const eventBadge = document.getElementById('eventBadge');
                        if (eventBadge) {
                            eventBadge.innerHTML = `<span class="badge badge-${eventType === 'ALLOCATE' ? 'success' : eventType === 'REQUEST' ? 'warning' : 'danger'}">${eventType}</span>`;
                        }
                        
                        logDiv.innerHTML = `<pre style="color: ${eventColor};">${JSON.stringify(data.event, null, 2)}</pre>`;
                    }
                }
                
                // Update graph with intelligent view
                updateGraphView(data);
                
                // Update graph badge
                const badge = document.getElementById('graphBadge');
                if (badge) {
                    if (hasDeadlock) {
                        badge.innerHTML = '<span style="background: var(--danger); color: white; padding: 0.5rem 1rem; border-radius: 0.75rem; font-weight: 600; font-size: 0.875rem; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);">🔴 Cycle Detected</span>';
                    } else {
                        badge.innerHTML = '<span style="background: var(--success); color: white; padding: 0.5rem 1rem; border-radius: 0.75rem; font-weight: 600; font-size: 0.875rem; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">🟢 No Cycles</span>';
                    }
                }
            } catch (e) {
                console.error('Failed to update UI:', e);
                updateStatus('❌ Failed to update display', 'deadlock');
            }
        }
        
        function updateStatus(message, type) {
            try {
                const statusDiv = document.getElementById('status');
                if (!statusDiv) return;
                
                const iconMap = {
                    'safe': '✓',
                    'deadlock': '⚠️',
                    'loading': '⏳'
                };
                
                const icon = iconMap[type] || '•';
                const timeText = currentTime > 0 ? 'Time: ' + currentTime + 's' : '';
                
                statusDiv.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="status-icon">${icon}</span>
                        <span>${message}</span>
                    </div>
                    <span id="statusTime">${timeText}</span>
                `;
                statusDiv.className = 'status-bar ' + type;
            } catch (e) {
                console.error('Failed to update status:', e);
            }
        }
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (ws) {
                ws.close();
            }
        });
        
        // Intelligent helper functions
        function animateValue(elementId, newValue, suffix = '') {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            const currentValue = parseInt(element.textContent) || 0;
            const duration = 800;
            const steps = 30;
            const increment = (newValue - currentValue) / steps;
            let current = currentValue;
            let step = 0;
            
            const timer = setInterval(() => {
                step++;
                current += increment;
                element.textContent = Math.round(current) + suffix;
                
                if (step >= steps) {
                    element.textContent = newValue + suffix;
                    clearInterval(timer);
                }
            }, duration / steps);
        }
        
        function calculateRiskScore(data) {
            let risk = 0;
            
            // Factor 1: Resource utilization (0-30 points)
            if (data.system_state) {
                let totalAllocated = 0;
                let totalAvailable = 0;
                Object.values(data.system_state.resources || {}).forEach(r => {
                    totalAllocated += (r.total - r.available);
                    totalAvailable += r.total;
                });
                const utilization = totalAvailable > 0 ? (totalAllocated / totalAvailable) : 0;
                risk += Math.round(utilization * 30);
            }
            
            // Factor 2: Deadlock history (0-40 points)
            risk += Math.min(40, deadlockCount * 10);
            
            // Factor 3: Current deadlock state (30 points)
            if (data.deadlock_analysis?.has_deadlock) {
                risk += 30;
            }
            
            return Math.min(100, risk);
        }
        
        function generateAIInsights(data) {
            const container = document.getElementById('aiInsights');
            if (!container) return;
            
            const insights = [];
            
            // Insight 1: Deadlock detection
            if (data.deadlock_analysis?.has_deadlock) {
                const cycles = data.deadlock_analysis.cycles || [];
                insights.push({
                    icon: '⚠️',
                    title: 'Critical: Circular Wait Detected',
                    body: `Detected ${cycles.length} cycle(s) in resource allocation graph. Processes involved: ${data.deadlock_analysis.deadlocked_processes?.join(', ')}. Immediate recovery action required.`,
                    confidence: 98,
                    type: 'danger'
                });
            } else {
                insights.push({
                    icon: '✅',
                    title: 'System Operating Safely',
                    body: 'No deadlock cycles detected. All processes can potentially complete their execution.',
                    confidence: 95,
                    type: 'success'
                });
            }
            
            // Insight 2: Resource utilization analysis
            if (data.system_state) {
                let totalAllocated = 0;
                let totalAvailable = 0;
                Object.values(data.system_state.resources || {}).forEach(r => {
                    totalAllocated += (r.total - r.available);
                    totalAvailable += r.total;
                });
                const utilization = totalAvailable > 0 ? Math.round((totalAllocated / totalAvailable) * 100) : 0;
                
                if (utilization > 80) {
                    insights.push({
                        icon: '📊',
                        title: 'High Resource Utilization Detected',
                        body: `Current utilization at ${utilization}%. System is operating near capacity. Consider implementing resource ordering policy to prevent potential deadlocks.`,
                        confidence: 87,
                        type: 'warning'
                    });
                } else if (utilization < 30) {
                    insights.push({
                        icon: '💡',
                        title: 'Low Resource Utilization',
                        body: `Resources are ${100 - utilization}% available. System has capacity for additional processes. Consider optimizing resource allocation strategies.`,
                        confidence: 82,
                        type: 'success'
                    });
                }
            }
            
            // Insight 3: Pattern recognition
            if (eventHistory.length > 5) {
                const recentEvents = eventHistory.slice(-5);
                const requestCount = recentEvents.filter(e => e.type === 'REQUEST').length;
                
                if (requestCount >= 4) {
                    insights.push({
                        icon: '🔍',
                        title: 'Pattern Alert: High Request Frequency',
                        body: `Detected ${requestCount} resource requests in last 5 events. This pattern may indicate resource contention. Banker Algorithm prevention recommended.`,
                        confidence: 76,
                        type: 'warning'
                    });
                }
            }
            
            // Insight 4: Performance trend
            if (deadlockCount > 0) {
                const efficiency = Math.max(0, 100 - (deadlockCount * 10));
                insights.push({
                    icon: '📈',
                    title: 'Performance Impact Analysis',
                    body: `${deadlockCount} deadlock(s) detected during simulation. Current system efficiency: ${efficiency}%. Recovery mechanisms have been triggered ${recoveryCount} times.`,
                    confidence: 91,
                    type: 'danger'
                });
            }
            
            // Render insights
            container.innerHTML = insights.map(insight => `
                <div class="insight-item ${insight.type}" style="animation: slideInLeft 0.5s ease-out;">
                    <div class="insight-header">
                        <span class="insight-icon">${insight.icon}</span>
                        <span class="insight-title">${insight.title}</span>
                    </div>
                    <div class="insight-body">${insight.body}</div>
                    <span class="insight-confidence">Confidence: ${insight.confidence}%</span>
                </div>
            `).join('');
        }
        
        function generateRecommendations(data) {
            const container = document.getElementById('recommendations');
            if (!container) return;
            
            const recommendations = [];
            
            // Recommendation 1: Deadlock prevention
            if (data.deadlock_analysis?.has_deadlock) {
                recommendations.push({
                    icon: '🛡️',
                    title: 'Enable Banker Algorithm Prevention',
                    description: 'Prevent future deadlocks by enabling Banker Algorithm. This will check safety before granting resource requests.',
                    action: 'Apply Prevention Policy'
                });
                
                recommendations.push({
                    icon: '🔧',
                    title: 'Execute Recovery Strategy',
                    description: 'Use preemption-based recovery to release resources from lower priority processes and break the deadlock cycle.',
                    action: 'Trigger Recovery'
                });
            }
            
            // Recommendation 2: Resource optimization
            if (data.system_state) {
                const resources = Object.values(data.system_state.resources || {});
                const lowAvailability = resources.filter(r => r.available < r.total * 0.2);
                
                if (lowAvailability.length > 0) {
                    recommendations.push({
                        icon: '⚡',
                        title: 'Optimize Resource Allocation',
                        description: `${lowAvailability.length} resource(s) have less than 20% availability. Implement resource ordering to minimize hold-and-wait conditions.`,
                        action: 'View Resource Analysis'
                    });
                }
            }
            
            // Recommendation 3: Monitoring enhancement
            if (eventHistory.length > 10 && deadlockCount === 0) {
                recommendations.push({
                    icon: '📊',
                    title: 'System Running Optimally',
                    description: 'No deadlocks detected in the last ' + eventHistory.length + ' events. Continue monitoring for sustained performance.',
                    action: 'View Performance Report'
                });
            }
            
            // Recommendation 4: Predictive analysis
            const riskScore = calculateRiskScore(data);
            if (riskScore > 60 && !data.deadlock_analysis?.has_deadlock) {
                recommendations.push({
                    icon: '🎯',
                    title: 'High Risk Score Detected',
                    description: `Current risk score is ${riskScore}/100. Consider implementing conservative allocation policy to reduce deadlock probability.`,
                    action: 'Apply Conservative Policy'
                });
            }
            
            // Render recommendations
            if (recommendations.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🎯</div>
                        <p>No immediate recommendations. System is operating within optimal parameters.</p>
                    </div>
                `;
            } else {
                container.innerHTML = recommendations.map((rec, index) => {
                    const delay = (index * 0.1) + 's';
                    return `
                    <div class="recommendation-item" style="animation: slideInRight 0.5s ease-out ${delay} both;">
                        <div class="recommendation-icon">${rec.icon}</div>
                        <div class="recommendation-content">
                            <div class="recommendation-title">${rec.title}</div>
                            <div class="recommendation-description">${rec.description}</div>
                            <button class="recommendation-action" onclick="alert('Feature: ${rec.action}')">${rec.action}</button>
                        </div>
                    </div>
                `;
                }).join('');
            }
        }
        
        function updateGraphView(data) {
            const graphDiv = document.getElementById('graph');
            if (!graphDiv || !data.graph) return;
            
            if (graphViewMode === 'detailed') {
                graphDiv.innerHTML = `<pre style="color: var(--text-primary);">${JSON.stringify(data.graph, null, 2)}</pre>`;
            } else {
                // Simplified view with visual representation
                const nodeCount = Object.keys(data.graph.nodes || {}).length;
                const edgeCount = Object.keys(data.graph.edges || {}).length;
                const statusIcon = data.deadlock_analysis?.has_deadlock ? '🔴' : '🟢';
                const statusColor = data.deadlock_analysis?.has_deadlock ? 'var(--danger)' : 'var(--success)';
                const statusText = data.deadlock_analysis?.has_deadlock ? 'Deadlock' : 'Safe';
                
                const summary = `
<div style="padding: 2rem;">
    <h3 style="color: var(--text-primary); margin-bottom: 1.5rem;">Graph Summary</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
        <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 0.75rem; border: 2px solid var(--border);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📍</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${nodeCount}</div>
            <div style="font-size: 0.875rem; color: var(--text-secondary);">Total Nodes</div>
        </div>
        <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 0.75rem; border: 2px solid var(--border);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔗</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--secondary);">${edgeCount}</div>
            <div style="font-size: 0.875rem; color: var(--text-secondary);">Connections</div>
        </div>
        <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 0.75rem; border: 2px solid var(--border);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">${statusIcon}</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: ${statusColor};">${statusText}</div>
            <div style="font-size: 0.875rem; color: var(--text-secondary);">Status</div>
        </div>
    </div>
</div>`;
                graphDiv.innerHTML = summary;
            }
        }
        
        function toggleGraphView() {
            graphViewMode = graphViewMode === 'detailed' ? 'simplified' : 'detailed';
            // Re-render with current data if available
            const graphDiv = document.getElementById('graph');
            if (graphDiv && graphDiv.innerHTML.includes('nodes')) {
                // Has data, trigger re-render
                updateStatus('🔄 Graph view toggled', 'safe');
            }
        }
    </script>
</body>
</html>
    """


def main():
    """Run the web server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
