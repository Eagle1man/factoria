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