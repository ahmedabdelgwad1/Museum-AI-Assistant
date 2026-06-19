"""
robot_core.py — The Maestro (Hardware Bridge)
==============================================

Standalone FastAPI server (port 8001) that receives robot action commands
from rag_bridge.py and translates them to physical hardware signals.

Start with:
    python backend/app/robot_core.py

Architecture:
    rag_bridge.py  --HTTP POST /action-->  robot_core.py  --Serial/ROS2-->  Arduino/Motors

This process is COMPLETELY INDEPENDENT from the LiveKit agent and FastAPI backend.
If this process crashes or the Arduino is disconnected, the AI conversation
(voice + TTS) continues without any interruption.

Hardware connection options (choose one):
    OPTION A — Direct Serial (simple, no ROS 2 needed):
        Set USE_ROS2 = False
        Set SERIAL_PORT to your Arduino port (e.g. "/dev/ttyUSB0" on Linux,
        "/dev/cu.usbmodem..." on macOS, "COM3" on Windows)

    OPTION B — ROS 2 (full robotics stack):
        Set USE_ROS2 = True
        Make sure ROS 2 is sourced and rclpy is installed.
        The node will publish Twist messages to /cmd_vel.
"""

import json
import logging
import os
import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration — edit these to match your hardware setup
# ---------------------------------------------------------------------------

USE_ROS2 = False                 # True = ROS 2 Twist publisher | False = direct Serial

# Serial settings (used only when USE_ROS2 = False)
SERIAL_PORT = os.getenv("ROBOT_SERIAL_PORT", "/dev/ttyUSB0")
SERIAL_BAUD = int(os.getenv("ROBOT_SERIAL_BAUD", "115200"))

# ROS 2 settings (used only when USE_ROS2 = True)
ROS2_NODE_NAME = "horus_maestro"
ROS2_CMD_VEL_TOPIC = "/cmd_vel"

# Movement speeds (m/s for ROS 2, or used as labels for Serial)
MOVE_LINEAR_SPEED = 0.3          # forward speed when action = "move"
ROTATE_ANGULAR_SPEED = 0.5      # rotation speed when action = "rotate_to_exhibit"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("robot_core")

# ---------------------------------------------------------------------------
# Hardware interface (Serial or ROS 2)
# ---------------------------------------------------------------------------

_serial_conn = None
_ros2_publisher = None
_ros2_node = None


def _init_serial():
    """Open the serial connection to Arduino. Called on startup."""
    global _serial_conn
    try:
        import serial
        _serial_conn = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        logger.info("Serial connection opened: %s @ %d baud", SERIAL_PORT, SERIAL_BAUD)
    except Exception as exc:
        logger.warning("Could not open serial port %s: %s — running in DRY-RUN mode", SERIAL_PORT, exc)
        _serial_conn = None


def _send_serial(command: str):
    """Send a single-line command string to the Arduino."""
    if _serial_conn and _serial_conn.is_open:
        payload = (command.strip() + "\n").encode()
        _serial_conn.write(payload)
        logger.info("→ Arduino serial: %s", command)
    else:
        logger.info("[DRY-RUN] Would send to Arduino: %s", command)


def _init_ros2():
    """Initialise ROS 2 node and /cmd_vel publisher."""
    global _ros2_node, _ros2_publisher
    try:
        import rclpy
        from rclpy.node import Node
        from geometry_msgs.msg import Twist

        rclpy.init()

        class MaestroNode(Node):
            def __init__(self):
                super().__init__(ROS2_NODE_NAME)
                self.pub = self.create_publisher(Twist, ROS2_CMD_VEL_TOPIC, 10)

        _ros2_node = MaestroNode()
        _ros2_publisher = _ros2_node.pub
        logger.info("ROS 2 node '%s' started, publishing to %s", ROS2_NODE_NAME, ROS2_CMD_VEL_TOPIC)
    except Exception as exc:
        logger.warning("ROS 2 init failed: %s — running in DRY-RUN mode", exc)
        _ros2_node = None
        _ros2_publisher = None


def _publish_twist(linear_x: float = 0.0, angular_z: float = 0.0):
    """Publish a Twist message to /cmd_vel."""
    if _ros2_publisher is None:
        logger.info("[DRY-RUN] Twist: linear_x=%.2f angular_z=%.2f", linear_x, angular_z)
        return
    try:
        from geometry_msgs.msg import Twist
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        _ros2_publisher.publish(msg)
        logger.info("→ /cmd_vel Twist: linear_x=%.2f angular_z=%.2f", linear_x, angular_z)
    except Exception as exc:
        logger.error("Failed to publish Twist: %s", exc)


# ---------------------------------------------------------------------------
# Action dispatcher
# ---------------------------------------------------------------------------

def dispatch_action(action_dict: dict):
    """
    Translate a robot_action dict into hardware commands.

    Expected action_dict shape:
        {
            "action": "stop_and_talk" | "move" | "rotate_to_exhibit",
            "target_location": "hall_B" | null,
            "listen_after_action": true | false
        }
    """
    action = action_dict.get("action", "stop_and_talk")
    target = action_dict.get("target_location")
    listen = action_dict.get("listen_after_action", True)

    logger.info("Dispatching action=%s | target=%s | listen=%s", action, target, listen)

    if action == "stop_and_talk":
        # ---- Stop all motors ----
        if USE_ROS2:
            _publish_twist(0.0, 0.0)
        else:
            _send_serial("STOP")

    elif action == "move":
        # ---- Move towards target ----
        target_label = target or "unknown"
        if USE_ROS2:
            _publish_twist(linear_x=MOVE_LINEAR_SPEED, angular_z=0.0)
        else:
            _send_serial(f"MOVE:{target_label}")

    elif action == "rotate_to_exhibit":
        # ---- Rotate to face exhibit ----
        if USE_ROS2:
            _publish_twist(linear_x=0.0, angular_z=ROTATE_ANGULAR_SPEED)
        else:
            _send_serial("ROTATE:EXHIBIT")

    else:
        logger.warning("Unknown action '%s' — defaulting to STOP", action)
        if USE_ROS2:
            _publish_twist(0.0, 0.0)
        else:
            _send_serial("STOP")

    # Note: listen_after_action is informational for now.
    # When integrated with the LiveKit agent, this flag can be used
    # to trigger re-enabling the microphone after the motion completes.
    if listen:
        logger.info("listen_after_action=True — microphone should re-open after motion")


# ---------------------------------------------------------------------------
# FastAPI endpoint
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Horus Robot Maestro",
    description="Receives structured action commands from the AI and dispatches them to hardware.",
    version="1.0.0",
)


class RobotAction(BaseModel):
    action: str
    target_location: Optional[str] = None
    listen_after_action: bool = True


@app.post("/action", summary="Execute a robot hardware action")
async def execute_action(body: RobotAction):
    """
    Called by rag_bridge.py whenever the LLM emits a robot action.
    Dispatches the command to Arduino (via Serial) or ROS 2 (/cmd_vel).
    """
    action_dict = body.model_dump()
    logger.info("Received action: %s", action_dict)

    # Run the (potentially blocking) serial/ROS write in a thread pool
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, dispatch_action, action_dict)

    return {"status": "ok", "dispatched": action_dict}


@app.get("/health", summary="Health check")
async def health():
    return {
        "status": "running",
        "mode": "ROS2" if USE_ROS2 else "Serial",
        "serial_port": SERIAL_PORT if not USE_ROS2 else None,
        "serial_connected": (_serial_conn is not None and _serial_conn.is_open) if not USE_ROS2 else None,
        "ros2_ready": _ros2_publisher is not None if USE_ROS2 else None,
    }


# ---------------------------------------------------------------------------
# Startup / Shutdown lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    logger.info("robot_core.py starting up...")
    if USE_ROS2:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _init_ros2)
    else:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _init_serial)
    logger.info("robot_core.py ready. Listening on http://localhost:8001")


@app.on_event("shutdown")
async def on_shutdown():
    global _serial_conn
    if _serial_conn and _serial_conn.is_open:
        _serial_conn.close()
        logger.info("Serial connection closed.")
    if USE_ROS2 and _ros2_node:
        try:
            import rclpy
            _ros2_node.destroy_node()
            rclpy.shutdown()
            logger.info("ROS 2 node shut down.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "robot_core:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
