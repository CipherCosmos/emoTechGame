#!/usr/bin/env python3
"""
WebSocket Connection Debug Test
"""

import asyncio
import json
import websockets
import uuid

BACKEND_URL = "https://01c20ec6-6f32-4da6-b33e-28aa4ae0e92a.preview.emergentagent.com"
WS_BASE = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")

async def test_websocket_debug():
    """Debug WebSocket connection"""
    connection_id = str(uuid.uuid4())
    ws_url = f"{WS_BASE}/ws/{connection_id}"
    
    print(f"Attempting to connect to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✅ WebSocket connection established!")
            
            # Test basic message
            test_message = {
                "type": "test",
                "data": {"message": "Hello WebSocket"}
            }
            
            await websocket.send(json.dumps(test_message))
            print("✅ Message sent successfully")
            
            # Try to receive a response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response}")
            except asyncio.TimeoutError:
                print("⚠️  No response received (this might be expected for unknown message types)")
            
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"Headers: {e.headers}")
        return False
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timed out")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket_debug())