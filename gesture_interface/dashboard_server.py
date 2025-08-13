import json
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .dashboard_state import GLOBAL_DASHBOARD_STATE

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # Thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # Index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # Middle
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # Ring
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # Pinky
]


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/state")
    def get_state():
        return JSONResponse(GLOBAL_DASHBOARD_STATE.get())

    @app.get("/")
    def index():
        conns_json = json.dumps(HAND_CONNECTIONS)
        html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>Thesidia Dashboard</title>
  <style>
    body {{ margin: 0; background: #000; color: #fff; font-family: -apple-system, system-ui, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\"; }}
    .hud {{ position: fixed; top: 16px; left: 16px; border: 1px solid #fff; padding: 12px 16px; border-radius: 6px; background: rgba(0,0,0,0.3); backdrop-filter: blur(6px); }}
    canvas {{ display: block; width: 100vw; height: 100vh; }}
  </style>
</head>
<body>
  <div class=\"hud\">
    <div id=\"gesture\">Gesture: -</div>
    <div id=\"symbol\">Symbol: -</div>
    <div id=\"fps\">FPS: -</div>
  </div>
  <canvas id=\"cnv\"></canvas>
  <script>
  const hudG = document.getElementById('gesture');
  const hudS = document.getElementById('symbol');
  const hudF = document.getElementById('fps');
  const cnv = document.getElementById('cnv');
  const ctx = cnv.getContext('2d');

  function resize(){{ cnv.width = window.innerWidth; cnv.height = window.innerHeight; }}
  window.addEventListener('resize', resize); resize();

  let stars = [];
  function initStars(){{
    const N = 120; stars = [];
    for(let i=0;i<N;i++){{
      stars.push({{ x: Math.random()*cnv.width, y: Math.random()*cnv.height, vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3 }});
    }}
  }}
  initStars();

  function drawConstellationField(){{
    // draw stars
    ctx.fillStyle = '#000'; ctx.fillRect(0,0,cnv.width,cnv.height);
    ctx.fillStyle = '#fff';
    for(const s of stars){{ ctx.beginPath(); ctx.arc(s.x, s.y, 1.6, 0, Math.PI*2); ctx.fill(); }}
    for(let i=0;i<stars.length;i++){{
      for(let j=i+1;j<stars.length;j++){{
        const dx = stars[i].x - stars[j].x; const dy = stars[i].y - stars[j].y; const d = Math.hypot(dx,dy);
        if(d < 120){{ ctx.strokeStyle = 'rgba(255,255,255,' + (1 - d/120) + ')'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(stars[i].x, stars[i].y); ctx.lineTo(stars[j].x, stars[j].y); ctx.stroke(); }}
      }}
    }}
    for(const s of stars){{ s.x += s.vx; s.y += s.vy; if(s.x<0||s.x>cnv.width) s.vx*=-1; if(s.y<0||s.y>cnv.height) s.vy*=-1; }}
  }}

  let lastState = {{ landmarks: [] }};

  function drawHandSkeleton(landmarks){{
    if(!Array.isArray(landmarks) || landmarks.length < 21) return;
    const pts = landmarks.map(([x,y]) => [x*cnv.width, y*cnv.height]);
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2;
    // connections
    const CONNS = {conns_json};
    for(const [a,b] of CONNS){{
      const [ax, ay] = pts[a]; const [bx, by] = pts[b];
      ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
    }}
    // points
    ctx.fillStyle = '#fff';
    for(const [x,y] of pts){{ ctx.beginPath(); ctx.arc(x,y,3,0,Math.PI*2); ctx.fill(); }}
  }}

  function render(){{
    ctx.clearRect(0,0,cnv.width,cnv.height);
    drawConstellationField();
    drawHandSkeleton(lastState.landmarks);
    requestAnimationFrame(render);
  }}
  render();

  async function poll(){{
    try{{
      const r = await fetch('/state');
      const j = await r.json();
      hudG.textContent = 'Gesture: ' + (j.gesture || '-');
      hudS.textContent = 'Symbol: ' + (j.symbol || '-');
      hudF.textContent = 'FPS: ' + (j.fps ? j.fps.toFixed(1) : '-');
      lastState = j;
    }}catch(e){{}}
    setTimeout(poll, 100);
  }}
  poll();
  </script>
</body>
</html>
        """
        return HTMLResponse(html)

    return app


def run_server(host: str = "127.0.0.1", port: int = 8765):
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
