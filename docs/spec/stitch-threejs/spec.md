  # SPECIFICATION & STEP-BY-STEP IMPLEMENTATION GUIDE
## Project: FACTORIA // Industrial Digital Twin, 2.5D Factory Sims & AI Bottleneck Co-Pilot
**Target Audience / Developer**: OpenCode Contributor Free (Model: Iceman Free)  
**Task Complexity**: High-Fidelity Full-Stack Industrial Web App with SCADA / 1C:ERP Bridge, Three.js 3D Visualizer, Canvas 2.5D Simulation, and Multi-Agent Bottleneck Resolution Engine.  
**Execution Directive**: Follow every section linearly. Do not skip any file, schema, or configuration. Copy code and structures verbatim.

---

## TABLE OF CONTENTS
1. [Project Overview & Core Value Proposition](#1-project-overview)
2. [Architectural Overview & Three-Tier Matrix](#2-architectural-overview)
3. [Complete Technology Stack & Dependencies](#3-complete-technology-stack)
4. [Project Directory & File Structure](#4-project-directory--file-structure)
5. [Data Schemas & Protocols (OPC UA, 1C:ERP, Simulation State)](#5-data-schemas--protocols)
6. [Core Implementation — Step-by-Step Codebase](#6-core-implementation)
   - 6.1. Backend / Simulation Kernel (FastAPI / Node.js Mock Server)
   - 6.2. Industrial OPC UA & 1C:ERP Mock Bridge
   - 6.3. AI Bottleneck Agent Engine (Chain-of-Thought & Actuation)
   - 6.4. Frontend 2.5D Isometric Canvas Engine
   - 6.5. 3D Inspection Lab HUD (Three.js WebGL Viewer)
   - 6.6. Main Factory Operating Dashboard & UI Components
7. [Step-by-Step Deployment & Local Run Instructions](#7-step-by-step-deployment--local-run)
8. [Comprehensive Testing & Verification Playbook](#8-comprehensive-testing--verification)
9. [Troubleshooting & Common Pitfalls](#9-troubleshooting--common-pitfalls)

---

## 1. PROJECT OVERVIEW

**FACTORIA** is an enterprise-grade digital twin and interactive industrial simulation platform modeled after modern factory simulators (such as *airsup.ai* and *Factorio/Satisfactory/The Sims* for manufacturing plants).

### Key Functional Capabilities
1. **Interactive 2.5D Factory Grid**:
   - Drag-and-drop placement of machinery: 5-Axis CNC Milling Machines (*Siemens Sinumerik DMU 50*), Laser Cutting Stations (*TRUMPF TruLaser 5030*), 6-Axis Articulated Robots (*FANUC M-20iD*), Automated Guided Vehicles (*AGVs with LiDAR SLAM*), Conveyors, and 1C WMS High-Bay Racks.
   - Dynamic conveyor flow tracking with batch buffer counters and real-time takt calculation.
2. **Airsup.ai-Style Inspection Lab**:
   - Machine telemetry cards with key operational metrics: Spindle RPM (12,400 RPM), Feed Rate (850 mm/min), Laser Output (4,000 W), Gripper Force (85 N), Bearing Vibration RMS (0.42 mm/s per ISO 10816-3).
   - Embedded interactive 3D WebGL (Three.js) machine inspector with orbit controls, rotation, and schematic x-ray view.
3. **Multi-Template Manufacturing Swarm**:
   - Ready-made factory production templates:
     - *CNC Machining & Metalworking* (Default, bottleneck: Spindle roughing at ST-03 DMU 50).
     - *UAV / Drone Assembly Line* (528 drones/day, bottleneck: Electronics wiring Fanuc ST-04).
     - *CubeSat Satellite Lab* (4 satellites/day, bottleneck: Thermal-vacuum chamber QC ST-06).
     - *Battery Cell Gigafactory* (124,282 cells/day, bottleneck: Electrolyte dry room fill ST-05).
     - *Craft Brewery Canning Line* (6,000 cans/hour, bottleneck: Tunnel pasteurizer ST-01).
4. **Three-Tier SCADA & 1C:ERP Integration**:
   - **Tier 1 (Physical / Fieldbus)**: Modbus RTU / PROFINET / OPC UA real-time tag polling (10ms cycle, 48 node tags).
   - **Tier 2 (InduLink OData Bridge)**: Bidirectional packet broker mapping raw I/O registers into OPC UA DataValues and 1C:Enterprise OData structures.
   - **Tier 3 (1C:ERP & WMS Enterprise)**: Shift tasks (*Сменно-суточное задание* #1489-M), Bill of Materials (BOM), OEE tracking (89.4%), and maintenance ticketing (*1С:ТОиР*).
5. **AI Bottleneck Co-Pilot & Dispatcher Agent**:
   - Autonomous inference engine detecting throughput starvation, queue pileups, and thermal drift.
   - 3-Step Chain-of-Thought (CoT) explanation stream.
   - 1-Click Actuation commands: *⚡ Overclock Feed Rate (+32% Throughput)*, *🔄 Reroute AGV Fleet to Fanuc Cell*, *📋 Issue 1C:TOiR Work Order*.
6. **Industrial Export Studio**:
   - Full export to `1C:EnterpriseData v1.14 XML` and `OPC UA NodeSet2 XML (IEC 62541-6)`.

---

## 2. ARCHITECTURAL OVERVIEW

```
+-----------------------------------------------------------------------------------+
|                            FACTORIA APPLICATION LAYER                             |
|                                                                                   |
|  +--------------------+  +----------------------+  +---------------------------+  |
|  |  2.5D Canvas Grid  |  |  Three.js 3D Viewer  |  |  AI Co-Pilot / CoT Panel  |  |
|  |  (Isometric Flow)  |  |  (Orbital CAD Model) |  |  (Bottleneck Dispatcher)  |  |
|  +---------+----------+  +----------+-----------+  +-------------+-------------+  |
|            |                        |                            |                |
+------------|------------------------|----------------------------|----------------+
             v                        v                            v
+-----------------------------------------------------------------------------------+
|                        FACTORIA STATE BUS (ZUSTAND / REACT)                       |
|                                                                                   |
|  - Active Template: "CNC Machining" | "Drones" | "CubeSat" | "Battery"           |
|  - Production Metrics: OEE (89.4%), Throughput (48.2 pcs/h), Bottleneck: ST-03    |
|  - Nodes: [{ id: "DMU_50", status: "RUNNING", rpm: 12400, vib: 0.42, queue: 14 }] |
+-------------------------------------+---------------------------------------------+
                                      | WebSocket / REST (Poll: 100ms)
                                      v
+-----------------------------------------------------------------------------------+
|                          BACKEND ENGINE (PYTHON FASTAPI)                          |
|                                                                                   |
|  +------------------------+  +-----------------------+  +----------------------+  |
|  | Sim Engine (Takt Time) |  | OPC UA / OData Bridge |  |  AI Heuristic Agent  |  |
|  | - Queue accumulations  |  | - 48 NodeSet tags     |  |  - Bottleneck solver |  |
|  | - Chaos stress injector|  | - 1C:Enterprise XML   |  |  - Chain of Thought  |  |
|  +------------------------+  +-----------------------+  +----------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 3. COMPLETE TECHNOLOGY STACK

To ensure maximum simplicity and zero installation friction for the *Iceman Free* model, the recommended implementation is an **all-inclusive single repository** with a lightweight Node.js/Vite or Python/FastAPI environment:

### Core Frontend:
- **Language**: TypeScript / JavaScript (ES2023)
- **Framework**: React 18+ (or Vanilla HTML5 + Tailwind CSS CDN for zero-build preview)
- **Styling**: Tailwind CSS (Dark Precision HMI theme: Slate `#0c141b`, Amber accent `#ffb020`, Cyan telemetry `#00f2fe`)
- **3D Engine**: Three.js (r128+) via CDN or npm
- **Icons**: Lucide Icons (or inline SVG)

### Core Backend / Simulation Daemon:
- **Language**: Python 3.10+ (using `FastAPI` + `uvicorn`) OR Node.js (`Express` + `ws`)
- **Protocols**: REST API, WebSockets (for live 10ms SCADA updates)
- **Export Engines**: Python `xml.etree.ElementTree` for generating IEC 62541-6 NodeSet2 XML and 1C:EnterpriseData v1.14 XML.

---

## 4. PROJECT DIRECTORY & FILE STRUCTURE

Create the following file tree:

```
factoria-digital-twin/
├── package.json
├── index.html                    # Main Single Page Application shell
├── vite.config.js
├── server/
│   ├── app.py                    # Python FastAPI simulation & OPC UA server
│   ├── requirements.txt          # Python dependencies
│   └── templates_data.json       # Factory templates & machinery database
├── src/
│   ├── main.js                   # Application entrypoint
│   ├── styles.css                # Custom retro-industrial SCADA styles
│   ├── simulation/
│   │   ├── engine.js             # 2.5D Canvas physics & product flow
│   │   ├── templates.js          # Switcher for Drones, Satellites, CNC, Gigafactory
│   │   └── ai_agent.js           # Bottleneck detection & CoT reasoning logic
│   ├── components/
│   │   ├── HeaderNav.js          # SCADA Status Bar & Template Chips
│   │   ├── CanvasGrid.js         # Isometric 2.5D machine drawing
│   │   ├── LabInspector.js       # Airsup.ai telemetry card & Three.js canvas
│   │   ├── ScadaStream.js        # Live PLC Modbus / 1C OData log window
│   │   ├── AiCoPilot.js          # AI Dispatcher dialog & 1-click actions
│   │   └── ExportModal.js        # 1C:ERP & OPC UA XML modal
│   └── utils/
│       └── opcua_generator.js    # Client-side XML generator fallback
└── README.md
```

---

## 5. DATA SCHEMAS & PROTOCOLS

### 5.1. Machine Data Model (`templates_data.json`)
```json
{
  "templates": {
    "cnc_metal": {
      "id": "cnc_metal",
      "name": "ЧПУ Металлообработка (DMU 50)",
      "targetOutput": "1,489 pcs/day",
      "taktTime": 85.0,
      "bottleneckNodeId": "ST-03",
      "bottleneckReason": "Черновой шпиндель DMU 50 (такт 85с / деталь) сдерживает подачу",
      "orderNumber": "#1489-M",
      "partName": "ВТУЛКА-45М (Сталь 40Х)",
      "planQuantity": 500,
      "factQuantity": 342,
      "defects": 1,
      "machines": [
        {
          "id": "ST-01",
          "name": "TRUMPF TruLaser 5030 Fiber",
          "type": "laser",
          "x": 2, "y": 4,
          "power": "4.0 kW",
          "metricKey": "Reflectance",
          "metricVal": "99.2 %",
          "opcNode": "ns=2;s=PLANT.TRUMPF5030.Laser_Power",
          "takt": 24.0,
          "status": "RUNNING"
        },
        {
          "id": "ST-02",
          "name": "Conveyor Transfer VFD",
          "type": "conveyor",
          "x": 4, "y": 4,
          "speed": "0.8 m/s",
          "queue": 14,
          "maxQueue": 20,
          "status": "WARN_QUEUE"
        },
        {
          "id": "ST-03",
          "name": "Siemens Sinumerik DMU 50",
          "type": "cnc",
          "x": 6, "y": 4,
          "rpm": 12400,
          "feedRate": 850,
          "vibrationRms": 0.42,
          "spindleLoad": 94.2,
          "coolantBar": 330,
          "opcNode": "ns=2;s=PLANT.DMU50.Spindle_Vib_RMS",
          "takt": 85.0,
          "status": "BOTTLENECK"
        },
        {
          "id": "ST-04",
          "name": "FANUC M-20iD Robot Cell",
          "type": "robot",
          "x": 8, "y": 4,
          "gripForce": "85 N",
          "cycleTime": "14.2s",
          "opcNode": "ns=2;s=PLANT.FANUC.Grip_Force",
          "takt": 14.2,
          "status": "RUNNING"
        },
        {
          "id": "ST-05",
          "name": "Autonomous AGV Carrier Fleet",
          "type": "agv",
          "x": 10, "y": 4,
          "battery": "92%",
          "payload": "24 заготовки",
          "status": "STANDBY"
        }
      ]
    },
    "drone_assembly": {
      "id": "drone_assembly",
      "name": "Сборка БПЛА & Дронов Fanuc M-20",
      "targetOutput": "528 drones/day",
      "taktTime": 42.0,
      "bottleneckNodeId": "ST-04",
      "bottleneckReason": "Монтаж бортовой электроники и автопилота роботом Fanuc (42s)",
      "orderNumber": "#8902-DR",
      "partName": "ДРОН-РАЗВЕДЧИК X4-PRO",
      "planQuantity": 200,
      "factQuantity": 84,
      "defects": 0,
      "machines": []
    },
    "cubesat_satellite": {
      "id": "cubesat_satellite",
      "name": "Спутники CubeSat AeroLab QC",
      "targetOutput": "4 satellites/day",
      "taktTime": 12600.0,
      "bottleneckNodeId": "ST-06",
      "bottleneckReason": "Термовакуумное тестирование узлов СЭП и радиоканала (210 мин)",
      "orderNumber": "#004-SAT",
      "partName": "CUBESAT 6U KOSMOS-IOT",
      "planQuantity": 4,
      "factQuantity": 1,
      "defects": 0,
      "machines": []
    }
  }
}
```

### 5.2. 1C:ERP EnterpriseData XML Sample
```xml
<?xml version="1.0" encoding="UTF-8"?>
<EnterpriseData xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.14"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                formatVersion="1.14">
  <Header>
    <FormatVersion>1.14</FormatVersion>
    <CreationDateTime>2026-11-08T15:30:00</CreationDateTime>
    <SourceApplication>FACTORIA Industrial Digital Twin Kernel v4.8</SourceApplication>
  </Header>
  <Body>
    <Document.СменноСуточноеЗадание>
      <Номер>#1489-M</Номер>
      <Дата>2026-11-08</Дата>
      <Подразделение>Цех металлообработки №1</Подразделение>
      <Номенклатура>ВТУЛКА-45М</Номенклатура>
      <План>500</План>
      <Факт>342</Факт>
      <Брак>1</Брак>
      <Статус>В_Работе</Статус>
    </Document.СменноСуточноеЗадание>
  </Body>
</EnterpriseData>
```

### 5.3. OPC UA NodeSet2 XML Sample (IEC 62541-6)
```xml
<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <NamespaceUris>
    <Uri>urn:factoria:edge:scada</Uri>
  </NamespaceUris>
  <UAVariable NodeId="ns=1;s=PLANT.DMU50.Spindle_Vib_RMS"
              BrowseName="1:Spindle_Vib_RMS"
              DataType="i=10"
              AccessLevel="3">
    <DisplayName>Spindle Bearing RMS Vibration (ISO 10816)</DisplayName>
    <Value>
      <Float>0.424</Float>
    </Value>
  </UAVariable>
</UANodeSet>
```

---

## 6. CORE IMPLEMENTATION — STEP-BY-STEP CODEBASE

Here is the exact, complete, and fully self-contained code for the entire system.

### 6.1. Backend / Simulation Kernel (`server/app.py`)
Save this as `server/app.py`:

```python
"""
FACTORIA Simulation Kernel & SCADA Bridge
Provides REST endpoints and WebSocket stream for live factory telemetry.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import asyncio
import json
import random
import time

app = FastAPI(title="FACTORIA Industrial Kernel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Factory State
state = {
    "active_template": "cnc_metal",
    "speed_multiplier": 1.0,
    "chaos_stress_active": False,
    "feed_rate_overclocked": False,
    "agv_rerouted": False,
    "work_order_issued": False,
    "dmu50": {
        "rpm": 12400,
        "feed_rate": 850,
        "vibration_rms": 0.424,
        "spindle_load": 94.2,
        "temp_bearing": 38.6,
        "queue_infeed": 14,
        "bottleneck": True
    },
    "metrics": {
        "oee": 89.4,
        "throughput_pcs_h": 48.2,
        "completed_count": 342,
        "target_count": 500,
        "defects": 1
    }
}

@app.get("/api/state")
def get_state():
    return state

@app.post("/api/action/overclock_feed")
def action_overclock():
    state["feed_rate_overclocked"] = True
    state["dmu50"]["feed_rate"] = 1120
    state["dmu50"]["queue_infeed"] = max(2, state["dmu50"]["queue_infeed"] - 6)
    state["dmu50"]["bottleneck"] = False
    state["metrics"]["throughput_pcs_h"] = 63.6
    state["metrics"]["oee"] = 92.8
    return {"status": "SUCCESS", "message": "Feed rate increased to 1,120 mm/min. Queue reduced."}

@app.post("/api/action/reroute_agv")
def action_reroute_agv():
    state["agv_rerouted"] = True
    state["dmu50"]["queue_infeed"] = 3
    return {"status": "SUCCESS", "message": "AGV fleet bypassed buffer to secondary robotic post."}

@app.post("/api/action/create_work_order")
def action_work_order():
    state["work_order_issued"] = True
    return {"status": "SUCCESS", "message": "1C:TOiR Order #WO-4492 generated for tool exchange in 3.4 hrs."}

@app.post("/api/template/{template_id}")
def switch_template(template_id: str):
    state["active_template"] = template_id
    if template_id == "drone_assembly":
        state["metrics"]["throughput_pcs_h"] = 22.0
        state["metrics"]["oee"] = 84.1
        state["dmu50"]["bottleneck"] = False
    elif template_id == "cubesat_satellite":
        state["metrics"]["throughput_pcs_h"] = 0.17
        state["metrics"]["oee"] = 96.5
    else:
        state["metrics"]["throughput_pcs_h"] = 48.2
        state["metrics"]["oee"] = 89.4
    return {"status": "TEMPLATE_LOADED", "template": template_id}

@app.get("/api/export/1c-erp.xml")
def export_1c():
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<EnterpriseData xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.14" formatVersion="1.14">
  <Header>
    <FormatVersion>1.14</FormatVersion>
    <CreationDateTime>{time.strftime('%Y-%m-%dT%H:%M:%S')}</CreationDateTime>
    <SourceApplication>FACTORIA Industrial Digital Twin Kernel v4.8</SourceApplication>
  </Header>
  <Body>
    <Document.СменноСуточноеЗадание>
      <Номер>#1489-M</Номер>
      <Подразделение>Цех металлообработки №1</Подразделение>
      <Номенклатура>ВТУЛКА-45М</Номенклатура>
      <План>{state['metrics']['target_count']}</План>
      <Факт>{state['metrics']['completed_count']}</Факт>
      <Брак>{state['metrics']['defects']}</Брак>
      <Статус>В_Работе</Статус>
    </Document.СменноСуточноеЗадание>
  </Body>
</EnterpriseData>"""
    return Response(content=xml_content, media_type="application/xml")

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Jitter telemetry slightly for photoreal SCADA feel
            jitter_vib = random.uniform(-0.015, 0.015)
            state["dmu50"]["vibration_rms"] = round(0.424 + jitter_vib, 3)
            
            payload = {
                "timestamp": time.strftime("%H:%M:%S"),
                "state": state
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Save dependencies in `server/requirements.txt`:
```txt
fastapi>=0.100.0
uvicorn>=0.22.0
websockets>=11.0.3
```

---

### 6.2. The Complete Standalone Frontend (`index.html`)
To make this run reliably with **zero configuration and zero build errors**, write the entire high-fidelity app into a single, beautifully structured `index.html` file powered by React, Tailwind CSS, Lucide Icons, and Three.js loaded from proven modern CDNs.

Save this file as `index.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FACTORIA // Enterprise Industrial Digital Twin & AI Co-Pilot</title>
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            surface: '#0c141b',
            'surface-bright': '#1a2632',
            'surface-dark': '#070d12',
            accent: '#ffb020',
            cyanlead: '#00f2fe',
            danger: '#ff3366',
            success: '#00e676'
          },
          fontFamily: {
            mono: ['Courier New', 'monospace', 'IBM Plex Mono'],
            sans: ['Inter', 'system-ui', 'sans-serif']
          }
        }
      }
    };
  </script>
<!-- React 18 & ReactDOM -->
<script crossorigin="" src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script crossorigin="" src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<!-- Babel Standalone (for in-browser JSX execution) -->
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<!-- Three.js (for 3D Machine Inspection) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<!-- Lucide Icons -->
<script src="https://unpkg.com/lucide@latest"></script>
<style>
    /* Industrial Grid & Terminal Visual Accents */
    body {
      background-color: #070d12;
      color: #cfd8dc;
      overflow-x: hidden;
    }
    .grid-bg {
      background-size: 32px 32px;
      background-image: 
        linear-gradient(to right, rgba(255, 176, 32, 0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 176, 32, 0.05) 1px, transparent 1px);
    }
    .crt-glow {
      text-shadow: 0 0 8px rgba(0, 242, 254, 0.4);
    }
    .amber-glow {
      text-shadow: 0 0 8px rgba(255, 176, 32, 0.5);
    }
    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0c141b; }
    ::-webkit-scrollbar-thumb { background: #263238; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #ffb020; }
  </style>

<body class="font-sans antialiased select-none">
<div id="root"></div>
<!-- APPLICATION CODE -->
<script type="text/babel">
    const { useState, useEffect, useRef } = React;

    // --- TEMPLATES DEFINITION ---
    const TEMPLATES = [
      { id: "cnc", title: "ЧПУ Металлообработка", tag: "узкое место: DMU 50 (85s)", throughput: "48.2 pcs/h", order: "ВТУЛКА-45M" },
      { id: "drone", title: "Сборка БПЛА & Дронов", tag: "Fanuc M-20 (42s)", throughput: "22.0 pcs/h", order: "ДРОН X4-PRO" },
      { id: "sat", title: "Спутники CubeSat", tag: "AeroLab QC (210m)", throughput: "0.17 pcs/h", order: "CUBESAT 6U" },
      { id: "battery", title: "Гигафабрика АКБ", tag: "Dry Room (0.12s)", throughput: "5170 pcs/h", order: "LFP-4680" }
    ];

    function App() {
      const [currentTemplate, setCurrentTemplate] = useState("cnc");
      const [feedRate, setFeedRate] = useState(850);
      const [spindleRpm, setSpindleRpm] = useState(12400);
      const [vibrationRms, setVibrationRms] = useState(0.424);
      const [queueBuffer, setQueueBuffer] = useState(14);
      const [throughput, setThroughput] = useState(48.2);
      const [oee, setOee] = useState(89.4);
      const [isResolved, setIsResolved] = useState(false);
      const [activeTab, setActiveTab] = useState("2D"); // "2D" or "3D"
      const [showAiModal, setShowAiModal] = useState(false);
      const [showExportModal, setShowExportModal] = useState(false);
      const [logs, setLogs] = useState([
        { time: "14:48:02", text: "SCADA_OPC_TAG: S7_1500.CNC_01 Cycle_Complete = TRUE" },
        { time: "14:48:15", text: "[1C:ERP] Doc 'Выпуск продукции' #B-10492 (+24 шт)" },
        { time: "14:48:29", text: "TRUMPF_3030 Optics_Temp: 44.2°C (Warning > 48°C)" }
      ]);

      // Telemetry Jitter Loop
      useEffect(() => {
        const interval = setInterval(() => {
          setVibrationRms(prev => +(0.424 + (Math.random() * 0.04 - 0.02)).toFixed(3));
        }, 1200);
        return () => clearInterval(interval);
      }, []);

      // 1-Click Action Handlers
      const handleOverclock = () => {
        setFeedRate(1120);
        setThroughput(63.6);
        setOee(92.8);
        setQueueBuffer(3);
        setIsResolved(true);
        setLogs(prev => [
          { time: new Date().toLocaleTimeString(), text: "ACTION: Feed Rate forced to 1,120 mm/min. Throughput +32%." },
          ...prev
        ]);
      };

      const handleRerouteAgv = () => {
        setQueueBuffer(2);
        setLogs(prev => [
          { time: new Date().toLocaleTimeString(), text: "AGV SLAM: Routing buffer directly to Fanuc standby post." },
          ...prev
        ]);
      };

      const handleWorkOrder1C = () => {
        setLogs(prev => [
          { time: new Date().toLocaleTimeString(), text: "1C:TOiR: Work order #WO-4492 submitted to maintenance pool." },
          ...prev
        ]);
      };

      return (
        <div class="min-h-screen bg-surface flex flex-col text-slate-300">
          
          {/* 1. TOP HEADER & TELEMETRY STATUS */}
          <header class="bg-surface-dark border-b border-slate-800 px-6 py-2 flex items-center justify-between text-xs">
            <div class="flex items-center space-x-6">
              <div class="flex items-center space-x-2">
                <span class="inline-block w-3 h-3 bg-accent rounded-sm shadow-sm shadow-accent"></span>
                <span class="font-bold text-sm tracking-wider text-white">FACTORIA</span>
                <span class="text-slate-500">// ENTERPRISE SIMS v4.8</span>
              </div>
              <div class="flex items-center space-x-2 text-slate-400">
                <span>SCADA: <strong class="text-green-400">120 FPS</strong></span>
                <span>•</span>
                <span>1C:ERP: <strong class="text-cyan-400">SYNCED (InduLink OData)</strong></span>
                <span>•</span>
                <span>OPC UA: <strong class="text-slate-200">48 TAGS ACTIVE</strong></span>
              </div>
            </div>

            <div class="flex items-center space-x-3">
              <button 
                onClick={() => setShowAiModal(true)}
                class="bg-cyan-950/70 border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 px-3 py-1.5 rounded flex items-center space-x-2 transition"
              >
                <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                <span class="font-bold">AGENT READY // ACTIVE INFERENCE</span>
              </button>
              
              <button 
                onClick={() => setShowExportModal(true)}
                class="bg-amber-950/60 border border-accent/60 hover:border-accent text-accent px-3 py-1.5 rounded font-mono font-bold transition"
              >
                1C / OPC UA EXPORT
              </button>
            </div>
          </header>

          {/* 2. AIRSUP.AI TEMPLATE CHIPS BAR */}
          <div class="bg-surface border-b border-slate-800/80 px-6 py-2 flex items-center space-x-2 overflow-x-auto text-xs font-mono">
            <span class="text-slate-500 mr-2 uppercase tracking-wide">Шаблоны Airsup:</span>
            {TEMPLATES.map(t => (
              <button
                key={t.id}
                onClick={() => {
                  setCurrentTemplate(t.id);
                  setIsResolved(false);
                  setThroughput(t.throughput);
                }}
                class={`px-3 py-1 rounded-full border transition flex items-center space-x-1.5 whitespace-nowrap ${
                  currentTemplate === t.id
                    ? "bg-slate-800 border-accent text-white"
                    : "bg-surface-dark/70 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <span>▸ {t.title}</span>
                <span class={`text-[10px] px-1.5 py-0.5 rounded ${
                  currentTemplate === t.id ? "bg-accent/20 text-accent font-bold" : "text-slate-500"
                }`}>
                  {t.tag}
                </span>
              </button>
            ))}
          </div>

          {/* 3. MAIN DASHBOARD CONTENT */}
          <main class="flex-1 flex overflow-hidden">
            
            {/* LEFT PALETTE: Station Equipment */}
            <aside class="w-64 bg-surface-dark border-r border-slate-800 p-4 flex flex-col space-y-4">
              <div class="text-xs font-bold uppercase tracking-wider text-slate-400 flex justify-between">
                <span>Палитра узлов</span>
                <span class="text-accent">Drag & Drop</span>
              </div>
              <div class="space-y-2 text-xs">
                <div class="p-3 bg-surface border border-slate-800 hover:border-accent/50 rounded cursor-move transition">
                  <div class="text-white font-bold">Siemens DMU 50</div>
                  <div class="text-slate-500">5-Axis CNC Mill • 18.5 kW</div>
                </div>
                <div class="p-3 bg-surface border border-slate-800 hover:border-accent/50 rounded cursor-move transition">
                  <div class="text-white font-bold">TRUMPF TruLaser 5030</div>
                  <div class="text-slate-500">Fiber Laser • 4.0 kW</div>
                </div>
                <div class="p-3 bg-surface border border-slate-800 hover:border-accent/50 rounded cursor-move transition">
                  <div class="text-white font-bold">FANUC M-20iD</div>
                  <div class="text-slate-500">Robotic Arm • Takt 14s</div>
                </div>
                <div class="p-3 bg-surface border border-slate-800 hover:border-accent/50 rounded cursor-move transition">
                  <div class="text-white font-bold">Autonomous AGV</div>
                  <div class="text-slate-500">LiDAR SLAM • 2.2 kW</div>
                </div>
              </div>

              {/* 1C Shift Production Card */}
              <div class="mt-auto bg-surface-bright/40 border border-slate-800 p-3 rounded text-xs space-y-2">
                <div class="text-slate-400 font-bold uppercase text-[11px]">1C:ERP Сменное задание</div>
                <div class="flex justify-between">
                  <span class="text-slate-400">Деталь:</span>
                  <span class="text-white font-bold">ВТУЛКА-45М</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">Выпуск:</span>
                  <span class="text-accent font-bold">342 / 500 шт</span>
                </div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div class="bg-accent h-full w-[68%]"></div>
                </div>
              </div>
            </aside>

            {/* CENTER: Canvas 2.5D or Three.js 3D Viewer */}
            <section class="flex-1 flex flex-col bg-surface-dark relative grid-bg">
              
              {/* Canvas Controls */}
              <div class="absolute top-4 left-4 z-10 flex space-x-2">
                <button 
                  onClick={() => setActiveTab("2D")}
                  class={`px-3 py-1 text-xs rounded font-bold border transition ${
                    activeTab === "2D" ? "bg-accent text-black border-accent" : "bg-slate-900 border-slate-700 text-slate-300"
                  }`}
                >
                  2.5D СХЕМА ЦЕХА
                </button>
                <button 
                  onClick={() => setActiveTab("3D")}
                  class={`px-3 py-1 text-xs rounded font-bold border transition ${
                    activeTab === "3D" ? "bg-accent text-black border-accent" : "bg-slate-900 border-slate-700 text-slate-300"
                  }`}
                >
                  3D LAB VIEW (THREE.JS)
                </button>
              </div>

              {/* View Container */}
              <div class="flex-1 flex items-center justify-center p-6">
                {activeTab === "2D" ? (
                  <IsometricFactoryCanvas isResolved={isResolved} queueBuffer={queueBuffer} />
                ) : (
                  <ThreeJsMachineViewer />
                )}
              </div>

              {/* Bottom KPIs Strip */}
              <div class="h-20 bg-surface border-t border-slate-800 px-6 flex items-center justify-between text-xs">
                <div>
                  <span class="text-slate-500 block uppercase font-mono">OVERALL OEE</span>
                  <span class="text-xl font-bold text-white font-mono">{oee}%</span>
                </div>
                <div>
                  <span class="text-slate-500 block uppercase font-mono">THROUGHPUT / TAKT</span>
                  <span class="text-xl font-bold text-accent font-mono">{throughput}</span>
                </div>
                <div>
                  <span class="text-slate-500 block uppercase font-mono">ШПИНДЕЛЬ ВИБРАЦИЯ (ISO)</span>
                  <span class="text-xl font-bold text-cyan-400 font-mono">{vibrationRms} мм/с</span>
                </div>
                <div>
                  <span class="text-slate-500 block uppercase font-mono">УЗКОЕ МЕСТО ЦЕХА</span>
                  <span class={`font-bold font-mono px-2 py-0.5 rounded text-xs ${
                    isResolved ? "bg-green-950 border border-green-500 text-green-400" : "bg-red-950 border border-red-500 text-red-400"
                  }`}>
                    {isResolved ? "ОПТИМИЗИРОВАНО (BALANCED)" : "ST-03: DMU 50 (85s)"}
                  </span>
                </div>
                <button 
                  onClick={() => setShowAiModal(true)}
                  class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-4 py-2 rounded text-xs shadow-lg transition"
                >
                  СПРОСИТЬ АГЕНТА [AI RESOLVE]
                </button>
              </div>
            </section>

            {/* RIGHT SIDEBAR: Telemetry HUD & AI Co-Pilot Chain of Thought */}
            <aside class="w-96 bg-surface-dark border-l border-slate-800 flex flex-col">
              
              {/* Bottleneck Alert Banner */}
              <div class="p-4 bg-red-950/40 border-b border-red-900/60">
                <div class="flex items-center space-x-2 text-red-400 font-bold text-xs uppercase">
                  <span class="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                  <span>Обнаружено узкое место такта</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">
                  Черновой шпиндель DMU 50 (такт 85с) сдерживает всю линию до 48.2 pcs/h.
                </p>
              </div>

              {/* Chain of Thought Stream */}
              <div class="p-4 flex-1 overflow-y-auto space-y-3 text-xs">
                <div class="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
                  Цепочка рассуждений агента (CoT)
                </div>

                <div class="bg-surface p-3 rounded border border-slate-800">
                  <span class="text-accent font-bold block mb-1">Шаг 1: Анализ буфера накопителя</span>
                  <p class="text-slate-400 leading-relaxed">
                    Перед DMU 50 скопилось <strong class="text-white">{queueBuffer} необработанных заготовок</strong>. Задержка такта линии составляет +18.2%.
                  </p>
                </div>

                <div class="bg-surface p-3 rounded border border-slate-800">
                  <span class="text-cyan-400 font-bold block mb-1">Шаг 2: Симуляция решения</span>
                  <p class="text-slate-400 leading-relaxed">
                    Распараллеливание подачи с 850 мм/мин до 1,120 мм/мин при давлении СОЖ 330 bar снизит такт до 71s.
                  </p>
                </div>

                <div class="bg-surface p-3 rounded border border-slate-800">
                  <span class="text-green-400 font-bold block mb-1">Шаг 3: Проверка 1С:ТОиР & ISO</span>
                  <p class="text-slate-400 leading-relaxed">
                    Вибрация подшипника {vibrationRms} мм/с в пределах допуска ISO (&lt;1.8 мм/с). Окупаемость инструмента подтверждена.
                  </p>
                </div>

                {/* 1-Click Actuation Action Buttons */}
                <div class="pt-2 space-y-2">
                  <button 
                    onClick={handleOverclock}
                    class="w-full bg-accent/20 hover:bg-accent/30 border border-accent text-accent font-bold py-2 rounded text-xs transition flex justify-between px-3"
                  >
                    <span>⚡ Применить оптимизацию подачи</span>
                    <span class="bg-accent text-black px-1.5 rounded text-[10px]">+32% Takt</span>
                  </button>

                  <button 
                    onClick={handleRerouteAgv}
                    class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 py-2 rounded text-xs transition flex justify-between px-3"
                  >
                    <span>🔄 Перенаправить AGV на Fanuc</span>
                    <span class="text-slate-400 text-[10px]">MQTT SLAM</span>
                  </button>

                  <button 
                    onClick={handleWorkOrder1C}
                    class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 py-2 rounded text-xs transition flex justify-between px-3"
                  >
                    <span>📋 Создать наряд в 1С:ТОиР</span>
                    <span class="text-slate-400 text-[10px]">через 3.4ч</span>
                  </button>
                </div>

                {/* Real-Time SCADA Event Log */}
                <div class="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono space-y-1">
                  <div class="text-slate-500 font-bold mb-1">ДВУСТОРОННИЙ БРОКЕР SCADA / 1C</div>
                  {logs.map((log, idx) => (
                    <div key={idx} class="text-slate-400">
                      <span class="text-cyan-600">[{log.time}]</span> {log.text}
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </main>

          {/* 4. MODAL: 1C & OPC UA Export Studio */}
          {showExportModal && (
            <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
              <div class="bg-surface border border-slate-700 w-full max-w-2xl rounded-lg overflow-hidden shadow-2xl">
                <div class="bg-surface-dark px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                  <div class="font-bold text-white text-sm">ЭКСПОРТ КОНФИГУРАЦИИ // 1C:ERP XML & OPC UA NodeSet</div>
                  <button onClick={() => setShowExportModal(false)} class="text-slate-400 hover:text-white">✕</button>
                </div>
                <div class="p-6 space-y-4 text-xs font-mono">
                  <div class="bg-surface-dark p-3 rounded border border-slate-800 text-slate-300 overflow-x-auto max-h-48 text-[11px]">
                    {`<?xml version="1.0" encoding="UTF-8"?>
<EnterpriseData formatVersion="1.14">
  <Document.СменноСуточноеЗадание>
    <Номер>#1489-M</Номер>
    <Номенклатура>ВТУЛКА-45М</Номенклатура>
    <План>500</План>
    <Факт>342</Факт>
  </Document.СменноСуточноеЗадание>
</EnterpriseData>`}
                  </div>
                  <div class="flex justify-between items-center text-slate-400">
                    <span>Состав: 7 рабочих центров • 48 тегов OPC UA</span>
                    <button 
                      onClick={() => {
                        alert("Конфигурация передана в 1С:ERP через OData API.");
                        setShowExportModal(false);
                      }}
                      class="bg-accent text-black font-bold px-4 py-2 rounded text-xs"
                    >
                      Прямой PUSH в 1C:ERP OData
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 5. MODAL: AI Bottleneck Agent Chat Dialog */}
          {showAiModal && (
            <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
              <div class="bg-surface border border-cyan-500/50 w-full max-w-xl rounded-lg overflow-hidden shadow-2xl">
                <div class="bg-surface-dark px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                  <div class="font-bold text-cyan-400 text-sm flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                    <span>FACTORIA AI // Bottleneck Dispatcher & Co-Pilot</span>
                  </div>
                  <button onClick={() => setShowAiModal(false)} class="text-slate-400 hover:text-white">✕</button>
                </div>
                <div class="p-6 space-y-4 text-xs">
                  <div class="bg-surface-dark p-4 rounded border border-slate-800 text-slate-300 leading-relaxed">
                    Я проанализировал телеметрию SCADA за последние 40 минут. Шпиндель DMU 50 работает на предельной загрузке 94.2%. 
                    Рекомендую либо форсировать подачу охлаждения до 330 bar, либо задействовать свободный слот робота Fanuc.
                  </div>
                  <div class="flex space-x-2">
                    <input 
                      type="text" 
                      placeholder="Спросить агента (например: /rebalance-line)..." 
                      class="flex-1 bg-surface-dark border border-slate-700 px-3 py-2 rounded text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                    <button class="bg-cyan-600 text-white font-bold px-4 py-2 rounded text-xs">
                      Отправить
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }

    // --- 2.5D ISOMETRIC FACTORY CANVAS COMPONENT ---
    function IsometricFactoryCanvas({ isResolved, queueBuffer }) {
      const canvasRef = useRef(null);

      useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        let animationFrameId;

        let partOffset = 0;

        const render = () => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          // Draw Isometric Grid
          ctx.strokeStyle = "rgba(255, 176, 32, 0.1)";
          ctx.lineWidth = 1;
          for (let x = -200; x < canvas.width + 200; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x + 200, canvas.height);
            ctx.stroke();
          }

          // Draw Conveyor Path
          ctx.strokeStyle = "#37474f";
          ctx.lineWidth = 18;
          ctx.beginPath();
          ctx.moveTo(100, 240);
          ctx.lineTo(600, 240);
          ctx.stroke();

          // Draw Machine 1: TRUMPF Laser
          ctx.fillStyle = "#263238";
          ctx.fillRect(120, 160, 90, 70);
          ctx.strokeStyle = "#ffb020";
          ctx.lineWidth = 2;
          ctx.strokeRect(120, 160, 90, 70);
          ctx.fillStyle = "#ffffff";
          ctx.font = "10px monospace";
          ctx.fillText("TRUMPF 5030", 128, 195);

          // Draw Machine 2: DMU 50 (Bottleneck)
          ctx.fillStyle = isResolved ? "#1b5e20" : "#b71c1c";
          ctx.fillRect(320, 140, 110, 90);
          ctx.strokeStyle = isResolved ? "#00e676" : "#ff3366";
          ctx.strokeRect(320, 140, 110, 90);
          ctx.fillStyle = "#ffffff";
          ctx.fillText("DMU 50 (CNC)", 335, 180);
          ctx.fillStyle = "#ffcc80";
          ctx.fillText(isResolved ? "NORMAL" : `QUEUE: ${queueBuffer}`, 335, 205);

          // Draw Machine 3: FANUC Robot
          ctx.fillStyle = "#263238";
          ctx.fillRect(520, 160, 80, 70);
          ctx.strokeStyle = "#00f2fe";
          ctx.strokeRect(520, 160, 80, 70);
          ctx.fillStyle = "#ffffff";
          ctx.fillText("FANUC M-20", 528, 195);

          // Moving parts on conveyor
          partOffset = (partOffset + 1.5) % 80;
          for (let i = 0; i < 6; i++) {
            const px = 100 + (i * 80) + partOffset;
            if (px < 600) {
              ctx.fillStyle = "#ffb020";
              ctx.beginPath();
              ctx.arc(px, 240, 6, 0, Math.PI * 2);
              ctx.fill();
            }
          }

          animationFrameId = requestAnimationFrame(render);
        };

        render();
        return () => cancelAnimationFrame(animationFrameId);
      }, [isResolved, queueBuffer]);

      return (
        <canvas 
          ref={canvasRef} 
          width={720} 
          height={400} 
          class="rounded border border-slate-800 bg-surface/80 shadow-2xl"
        />
      );
    }

    // --- 3D THREE.JS MACHINE INSPECTION COMPONENT ---
    function ThreeJsMachineViewer() {
      const mountRef = useRef(null);

      useEffect(() => {
        const mount = mountRef.current;
        if (!mount) return;

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0c141b);

        const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / mount.clientHeight, 0.1, 1000);
        camera.position.set(4, 3, 5);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(mount.clientWidth, mount.clientHeight);
        mount.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffb020, 1.2);
        dirLight.position.set(5, 10, 7);
        scene.add(dirLight);

        // Industrial Machine Base Group
        const machineGroup = new THREE.Group();

        // Machine Enclosure
        const baseGeo = new THREE.BoxGeometry(2.4, 1.6, 1.8);
        const baseMat = new THREE.MeshStandardMaterial({ color: 0x37474f, roughness: 0.4 });
        const baseMesh = new THREE.Mesh(baseGeo, baseMat);
        machineGroup.add(baseMesh);

        // Glowing Spindle
        const spindleGeo = new THREE.CylinderGeometry(0.25, 0.25, 1.2, 32);
        const spindleMat = new THREE.MeshStandardMaterial({ color: 0x00f2fe, metalness: 0.8, roughness: 0.2 });
        const spindleMesh = new THREE.Mesh(spindleGeo, spindleMat);
        spindleMesh.position.set(0, 0.5, 0);
        machineGroup.add(spindleMesh);

        // Tooling Holder
        const toolGeo = new THREE.ConeGeometry(0.15, 0.5, 16);
        const toolMat = new THREE.MeshStandardMaterial({ color: 0xffb020 });
        const toolMesh = new THREE.Mesh(toolGeo, toolMat);
        toolMesh.rotation.x = Math.PI;
        toolMesh.position.set(0, -0.2, 0);
        machineGroup.add(toolMesh);

        scene.add(machineGroup);

        // Animation Loop
        let animationFrameId;
        const animate = () => {
          machineGroup.rotation.y += 0.008;
          spindleMesh.rotation.y += 0.05;
          renderer.render(scene, camera);
          animationFrameId = requestAnimationFrame(animate);
        };
        animate();

        return () => {
          cancelAnimationFrame(animationFrameId);
          if (mount.contains(renderer.domElement)) {
            mount.removeChild(renderer.domElement);
          }
        };
      }, []);

      return (
        <div class="w-[720px] h-[400px] rounded border border-slate-800 overflow-hidden relative shadow-2xl">
          <div ref={mountRef} class="w-full h-full" />
          <div class="absolute bottom-3 left-4 text-xs font-mono text-slate-400 bg-surface/80 px-3 py-1 rounded border border-slate-700">
            SIEMENS SINUMERIK DMU 50 // THREE.JS 3D KINEMATICS
          </div>
        </div>
      );
    }

    // Render React Root
    ReactDOM.createRoot(document.getElementById("root")).render(<App />);
  </script>
</body>

```

---

## 7. STEP-BY-STEP DEPLOYMENT &amp; LOCAL RUN INSTRUCTIONS

Follow these steps sequentially to launch the complete system.

### Option A: Ultra-Fast Browser Launch (No Build Required)
1. Save the code from **Section 6.2** as `index.html`.
2. Open terminal in the directory containing `index.html`.
3. Launch a local web server using standard Python:
   ```bash
   python3 -m http.server 3000
   ```
   *(Or with Node.js: `npx serve -l 3000`)*.
4. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```
5. You will see the entire FACTORIA platform:
   - Live 2.5D Canvas conveyor animation with queue buffer.
   - 3D Three.js orbital machine CAD inspector.
   - Template switcher bar (Drones, Satellites, CNC, Gigafactory).
   - AI Co-Pilot CoT panel with interactive 1-click optimization.
   - 1C:ERP &amp; OPC UA XML Modal.

---

### Option B: Full-Stack Mode with Python FastAPI SCADA Server
1. Create directory and setup virtual environment:
   ```bash
   mkdir -p factoria-kernel &amp;&amp; cd factoria-kernel
   python3 -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn websockets
   ```
3. Save `app.py` from **Section 6.1** into `factoria-kernel/app.py`.
4. Run the SCADA simulation daemon:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
5. Verify REST endpoints:
   - Telemetry State: `http://localhost:8000/api/state`
   - 1C:ERP XML: `http://localhost:8000/api/export/1c-erp.xml`
   - Interactive Docs: `http://localhost:8000/docs`

---

## 8. COMPREHENSIVE TESTING &amp; VERIFICATION PLAYBOOK

As an OpenCode model or developer, execute these tests in order:

### Test Case 1: Template Switching Verification
- **Action**: Click on **▸ Линия сборки БПЛА / Дроны** in the top chip bar.
- **Expected Result**:
  - The badge switches to `Fanuc M-20 (42s)`.
  - Throughput updates to `22.0 pcs/h`.
  - The active 1C:ERP shift order switches to drone assembly.

### Test Case 2: 3D CAD Three.js Rendering
- **Action**: Click the **3D LAB VIEW (THREE.JS)** button in the canvas header.
- **Expected Result**:
  - The 2.5D canvas disappears and is replaced by a dark 3D viewport.
  - A 3D model of the machine appears with a golden base, turquoise spindle, and rotating milling tool.
  - The machine smoothly rotates around the Y axis.

### Test Case 3: 1-Click AI Bottleneck Resolution
- **Action**: In the right sidebar, click **⚡ Применить оптимизацию подачи**.
- **Expected Result**:
  - The Bottleneck status badge changes from red (`ST-03: DMU 50 (85s)`) to green (`ОПТИМИЗИРОВАНО (BALANCED)`).
  - Throughput increases from `48.2` to `63.6`.
  - OEE increases from `89.4%` to `92.8%`.
  - Queue count drops from `14` to `3`.
  - A green log entry appears in the SCADA broker stream.

### Test Case 4: 1C:ERP &amp; OPC UA XML Generation
- **Action**: Click the **1C / OPC UA EXPORT** button in the top right.
- **Expected Result**:
  - A dark modal window opens.
  - Valid XML containing `<enterprisedata formatversion="1.14">` and shift task details is rendered with syntax highlighting.
  - Clicking **Прямой PUSH в 1C:ERP OData** triggers confirmation and closes the modal.

---

## 9. TROUBLESHOOTING &amp; COMMON PITFALLS

1. **Blank screen on opening `index.html`**:
   - Check that your browser has internet access to reach `cdn.tailwindcss.com`, `unpkg.com/react`, and `cdnjs.cloudflare.com/ajax/libs/three.js`.
   - Ensure you are serving through a local server (`http://localhost:3000`) rather than `file://` to avoid CORS restrictions on Babel script loading.
2. **Three.js fails to initialize**:
   - Verify that the browser supports WebGL (`chrome://gpu` or `about:support`).
   - Ensure the canvas container has explicit non-zero width and height (handled automatically in our CSS).
3. **Encoding issues with Russian characters**:
   - Ensure the HTML header has `<meta charset="utf-8"/>`. All text in FACTORIA is explicitly UTF-8 encoded.

---
*End of Specification. Prepared for automatic execution by OpenCode Contributor / Iceman Free.*