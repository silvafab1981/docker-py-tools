// ===== Banner sin intercalado: hora fija en cuadro rojo, solo rota Ciudad • Temp =====
const $  = sel => document.querySelector(sel);
const cityEl  = $('#b-city');
const tempEl  = $('#b-temp');
const clockEl = $('#b-clock');

function hhmm(){
  return new Date().toLocaleTimeString('es-AR', {hour:'2-digit', minute:'2-digit', hour12:false});
}
function setText(el, txt){
  if (!el) return;
  const s = String(txt);
  if (el.textContent !== s) {
    el.textContent = s;
    el.classList.remove('text-tick');
    void el.offsetWidth;     // reflow para re-aplicar animación
    el.classList.add('text-tick');
  }
}

async function fetchJSON(url, {timeoutMs=8000}={}){
  const ctrl = new AbortController();
  const t = setTimeout(()=>ctrl.abort(), timeoutMs);
  try{
    const r = await fetch(url, {cache:'no-store', signal: ctrl.signal});
    if(!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

async function getConfig(){
  const cfg = await fetchJSON('/api/overlay/config').catch(()=>({}));
  return {
    cities: cfg.cities || [],
    labels: cfg.labels || {},
    cycle: Math.max(2, parseInt(cfg.cycle || 15, 10)),  // segundos entre tarjetas
  };
}
function displayNameFor(it, labels){ return (labels && labels[it.ciudad]) || it.ciudad; }

async function getItems(cities){
  const qs = new URLSearchParams({ cities: (cities||[]).join(',') });
  const data = await fetchJSON('/api/weather?' + qs).catch(()=>({}));
  return (data && data.items) ? data.items : [];
}

(async function main(){
  const cfg    = await getConfig();
  const cities = cfg.cities, labels = cfg.labels;
  const cycle  = cfg.cycle;

  // obtener y ordenar datos según el orden de cities
  let items = await getItems(cities);
  const order = new Map(cities.map((c,i)=>[String(c).toLowerCase(), i]));
  items.sort((a,b)=> (order.get((a.ciudad||'').toLowerCase()) ?? 999) -
                     (order.get((b.ciudad||'').toLowerCase()) ?? 999));

  let idx = 0;

  // Primer render
  if (items.length){
    const it   = items[0];
    const city = displayNameFor(it, labels);
    const temp = (it.temperatura ?? '—') + '°C';
    setText(cityEl, city);
    setText(tempEl, temp);
    idx = 1 % items.length;
  } else {
    setText(cityEl, '—');
    setText(tempEl, '—');
  }

  // Reloj del cuadro rojo (fijo)
  setText(clockEl, hhmm());
  setInterval(()=> setText(clockEl, hhmm()), 5_000);

  // Rotación contínua de Ciudad • Temp (sin intercalado)
  setInterval(()=>{
    if (!items.length) return;
    const it   = items[idx % items.length];
    const city = displayNameFor(it, labels);
    const temp = (it.temperatura ?? '—') + '°C';
    setText(cityEl, city);
    setText(tempEl, temp);
    idx = (idx + 1) % Math.max(items.length, 1);
  }, cycle * 1000);

  // Refresco de datos cada 60s (sin alterar el DOM si no hay cambios)
  setInterval(async ()=>{
    try{
      const fresh = await getItems(cities);
      if (fresh && fresh.length){
        fresh.sort((a,b)=> (order.get((a.ciudad||'').toLowerCase()) ?? 999) -
                           (order.get((b.ciudad||'').toLowerCase()) ?? 999));
        items = fresh;
        idx = idx % items.length;
      }
    }catch(e){ console.warn('refresh error', e); }
  }, 60_000);

  // Mantener dataset del backend fresco (silencioso)
  setInterval(async ()=>{ try{ await fetch('/api/tiepre'); }catch{} }, 5*60_000);
})();
