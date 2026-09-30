'use strict';
// The Brain — a living neural network rendered on a canvas confined to the
// reactor stage. A neuron cloud drifts around the JARVIS core (drawn in HTML,
// on top of this canvas); the six specialists dock on an outer orbit, wired
// to the core with synapse channels. Pulses travel the cloud and the channels;
// a single "activity" level ramps everything up while the swarm is executing.
const Brain = (() => {
  let canvas, ctx;
  let W = 0, H = 0, CX = 0, CY = 0, R = 0;

  const DEFAULT = '120,140,160';
  let activity = 0.14, targetActivity = 0.14, speakLevel = 0;

  const NEURONS = 70;
  const neurons = [];
  const edges = [];
  const pulses = [];
  const channelPulses = [];
  let nodes = []; // {id, symbol, name, label, color, angle, status, burst}

  function toRgb(color) {
    const el = document.createElement('span');
    el.style.color = color;
    document.body.appendChild(el);
    const rgb = getComputedStyle(el).color.match(/\d+/g).slice(0, 3).join(',');
    document.body.removeChild(el);
    return rgb;
  }

  function resize() {
    if (!canvas) return;
    const rect = canvas.parentElement.getBoundingClientRect();
    W = canvas.width = Math.max(1, rect.width) * devicePixelRatio;
    H = canvas.height = Math.max(1, rect.height) * devicePixelRatio;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    CX = rect.width / 2;
    CY = rect.height / 2;
    R = Math.min(rect.width, rect.height) * 0.15;
    buildCloud();
  }

  function buildCloud() {
    neurons.length = 0; edges.length = 0; pulses.length = 0;
    for (let i = 0; i < NEURONS; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = Math.sqrt(Math.random());
      neurons.push({
        x0: Math.cos(a) * r * R * 3.1,
        y0: Math.sin(a) * r * R * 1.9,
        phase: Math.random() * Math.PI * 2,
        drift: 0.3 + Math.random() * 0.8,
        size: 0.7 + Math.random() * 1.3,
        x: 0, y: 0,
      });
    }
    for (let i = 0; i < neurons.length; i++) {
      const dists = neurons
        .map((n, j) => ({ j, d: (n.x0 - neurons[i].x0) ** 2 + (n.y0 - neurons[i].y0) ** 2 }))
        .filter(o => o.j !== i)
        .sort((a, b) => a.d - b.d)
        .slice(0, 2);
      for (const { j } of dists) {
        if (!edges.some(e => (e.a === i && e.b === j) || (e.a === j && e.b === i))) {
          edges.push({ a: i, b: j });
        }
      }
    }
  }

  function nodePos(n) {
    const a = n.angle * Math.PI * 2;
    return { x: CX + Math.cos(a) * R * 2.55, y: CY + Math.sin(a) * R * 1.65 };
  }
  function statusColor(n) {
    if (n.status === 'running') return n._rgb;
    if (n.status === 'hold') return '240,190,119';
    if (n.status === 'completed') return n._rgb;
    return DEFAULT;
  }

  let t = 0, raf = null;
  function frame() {
    t += 0.016;
    activity += (targetActivity - activity) * 0.05;
    speakLevel *= 0.94;
    const act = Math.min(1, activity + speakLevel);
    ctx.clearRect(0, 0, W / devicePixelRatio, H / devicePixelRatio);
    for (const n of neurons) {
      n.x = CX + n.x0 + Math.sin(t * n.drift + n.phase) * 5;
      n.y = CY + n.y0 + Math.cos(t * n.drift * 0.8 + n.phase) * 5;
    }
    drawEdges(act); spawnPulses(act); drawPulses(); drawNeurons(act);
    drawChannels(act); drawNodes();
    raf = requestAnimationFrame(frame);
  }

  function drawEdges(act) {
    ctx.lineWidth = 0.6;
    for (const e of edges) {
      const a = neurons[e.a], b = neurons[e.b];
      ctx.strokeStyle = `rgba(131,236,223,${0.05 + act * 0.09})`;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
  }
  function spawnPulses(act) {
    const rate = 0.04 + act * 0.4;
    if (Math.random() < rate && pulses.length < 60 && edges.length) {
      pulses.push({ e: edges[(Math.random() * edges.length) | 0], t: 0, speed: 0.02 + Math.random() * 0.03 + act * 0.02 });
    }
  }
  function drawPulses() {
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i]; p.t += p.speed;
      if (p.t >= 1) { pulses.splice(i, 1); continue; }
      const a = neurons[p.e.a], b = neurons[p.e.b];
      const x = a.x + (b.x - a.x) * p.t, y = a.y + (b.y - a.y) * p.t;
      const g = ctx.createRadialGradient(x, y, 0, x, y, 4);
      g.addColorStop(0, 'rgba(131,236,223,0.85)'); g.addColorStop(1, 'rgba(131,236,223,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawNeurons(act) {
    for (const n of neurons) {
      const tw = 0.5 + 0.5 * Math.sin(t * 2 + n.phase);
      ctx.fillStyle = `rgba(131,236,223,${0.18 + tw * (0.18 + act * 0.3)})`;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawChannels(act) {
    for (const n of nodes) {
      const p = nodePos(n);
      const col = statusColor(n);
      const alpha = n.status ? 0.2 + act * 0.15 : 0.08;
      ctx.strokeStyle = `rgba(${col},${alpha + n.burst * 0.4})`;
      ctx.lineWidth = 1 + n.burst * 1.4;
      const mx = (p.x + CX) / 2 + (CY - p.y) * 0.1;
      const my = (p.y + CY) / 2 + (p.x - CX) * 0.1;
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.quadraticCurveTo(mx, my, CX, CY); ctx.stroke();
      n.burst *= 0.95;
      n._mid = { mx, my, px: p.x, py: p.y };
    }
    for (let i = channelPulses.length - 1; i >= 0; i--) {
      const cp = channelPulses[i]; cp.t += 0.02;
      if (cp.t >= 1) { channelPulses.splice(i, 1); continue; }
      const n = cp.node, m = n._mid; if (!m) continue;
      const u = cp.dir === 'in' ? cp.t : 1 - cp.t;
      const x = (1 - u) ** 2 * m.px + 2 * (1 - u) * u * m.mx + u * u * CX;
      const y = (1 - u) ** 2 * m.py + 2 * (1 - u) * u * m.my + u * u * CY;
      const col = statusColor(n);
      const g = ctx.createRadialGradient(x, y, 0, x, y, 6);
      g.addColorStop(0, `rgba(${col},1)`); g.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawNodes() {
    for (const n of nodes) {
      const p = nodePos(n);
      const col = statusColor(n);
      const pu = 0.5 + 0.5 * Math.sin(t * 2 + n.angle * 9);
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 16);
      g.addColorStop(0, `rgba(${col},${0.7 + n.burst})`);
      g.addColorStop(0.5, `rgba(${col},0.25)`);
      g.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, 16, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(${col},0.95)`;
      ctx.beginPath(); ctx.arc(p.x, p.y, 3.5 + pu + n.burst * 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = `rgba(${col},0.55)`; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(p.x, p.y, 8 + n.burst * 3, 0, Math.PI * 2); ctx.stroke();
      ctx.textAlign = 'center';
      ctx.font = 'bold 12px "Segoe UI Symbol", "Apple Color Emoji", ui-monospace, sans-serif';
      ctx.fillStyle = `rgba(${col},1)`;
      const yOffset = p.y < CY ? -14 : 22;
      ctx.fillText(`${n.symbol} ${n.name}`, p.x, p.y + yOffset);
      ctx.font = '8px ui-monospace, monospace';
      ctx.fillStyle = 'rgba(165,195,210,0.8)';
      ctx.fillText(n.label, p.x, p.y + yOffset + (p.y < CY ? -11 : 11));
    }
  }

  return {
    mount(canvasEl, agents) {
      canvas = canvasEl; ctx = canvas.getContext('2d');
      nodes = agents.map((a, i) => ({
        id: a.id, symbol: a.symbol, name: a.name, label: a.label,
        angle: i / agents.length, status: '', burst: 0, _rgb: toRgb(a.color),
      }));
      addEventListener('resize', resize);
      resize();
      if (!raf) raf = requestAnimationFrame(frame);
    },
    setActivity(x) { targetActivity = Math.max(0.12, Math.min(1, x)); },
    speak(level = 0.5) { speakLevel = Math.min(1, speakLevel + level * 0.3); },
    setStatus(id, status) { const n = nodes.find(x => x.id === id); if (n) n.status = status; },
    fire(id, dir = 'in', n = 5) {
      const node = nodes.find(x => x.id === id); if (!node) return;
      node.burst = 1;
      for (let i = 0; i < n; i++) setTimeout(() => channelPulses.push({ node, t: 0, dir }), i * 130);
    },
  };
})();
