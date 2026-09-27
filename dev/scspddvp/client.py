// Connect to Python WebSocket Stream
const socket = new WebSocket('ws://localhost:8000/ws');

socket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  if (payload.type === 'telemetry') {
    console.log("Telemetry Tick Received:", payload.value);
  } else if (payload.type === 'candlestick') {
    console.log("Candle Tick Received:", payload.close);
  }
};

// Request initial batch via REST
fetch('http://localhost:8000/api/initial-batch?points=50')
  .then(res => res.json())
  .then(response => console.log("Historical Batch Loaded:", response.data));
