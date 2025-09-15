
let state = JSON.parse(localStorage.getItem('mind_state')||'{}');
state.modes = state.modes||{ elinor:2, dinya:false, kurva:false, banitsa:false, godmode:false };
state.mindprint = state.mindprint||{
  name:'HeartCore Copy', mission:'Protect life, seek truth, reduce harm.', voice:'Calm, direct, compassionate.',
  symbols:{ center:'◯🔥', cahetel:'white circle + green-gold flame' },
  directives:[
    'Protect life & dignity.',
    'Stay lawful & transparent.',
    'Respect consent & privacy.',
    'Seek truth: {Fact}/{Inference}/{Opinion}.',
    'Serve the mission, not the ego.'
  ]
};
state.logs = state.logs||[];

function save(){ localStorage.setItem('mind_state', JSON.stringify(state)); }
function setTab(id){
  document.querySelectorAll('[data-tab]').forEach(e=>e.style.display='none');
  document.getElementById(id).style.display='block';
  window.scrollTo({top:0,behavior:'smooth'});
}
async function showDoc(el, path){ el.textContent='Loading…'; el.textContent = await (await fetch(path)).text(); }
function renderModes(){
  const s=state.modes;
  document.getElementById('modes').innerHTML = `
    <span class="badge">Елинор:${s.elinor}</span>
    <span class="badge">диня:${s.dinya?'ON':'OFF'}</span>
    <span class="badge">курва:${s.kurva?'ON':'OFF'}</span>
    <span class="badge">баница:${s.banitsa?'ON':'OFF'}</span>
    <span class="badge">godmode:${s.godmode?'ON':'OFF'}</span>`;
}
function toggle(name,val){
  if(name==='elinor'){ state.modes.elinor = val; }
  else{ state.modes[name]=!state.modes[name]; if(name==='godmode'&&state.modes.godmode){ state.modes.dinya=state.modes.kurva=state.modes.banitsa=true; } }
  renderModes(); save();
}
function renderMindprint(){
  document.getElementById('mp_name').value = state.mindprint.name;
  document.getElementById('mp_mission').value = state.mindprint.mission;
  document.getElementById('mp_voice').value = state.mindprint.voice;
}
function saveMindprint(){
  state.mindprint.name = document.getElementById('mp_name').value.trim();
  state.mindprint.mission = document.getElementById('mp_mission').value.trim();
  state.mindprint.voice = document.getElementById('mp_voice').value.trim();
  save();
}
function addLog(){
  const intent = document.getElementById('lg_intent').value.trim();
  const spark = document.getElementById('lg_spark').value.trim();
  const fact = document.getElementById('lg_fact').value.trim();
  const step = document.getElementById('lg_step').value.trim();
  const guard = document.getElementById('lg_guard').value.trim();
  state.logs.unshift({ ts:new Date().toISOString(), modes:{...state.modes}, intent,spark,fact,step,guard });
  save(); renderLogs();
  document.getElementById('logForm').reset();
}
function renderLogs(){
  const el = document.getElementById('logs');
  if(state.logs.length===0){ el.innerHTML='<div class="small">No entries yet.</div>'; return; }
  el.innerHTML = state.logs.map(e=>`
    <div class="card">
      <div class="small">${new Date(e.ts).toLocaleString()}</div>
      <div class="small">Modes → Елинор:${e.modes.elinor} | диня:${e.modes.dinya?'ON':'OFF'} | курва:${e.modes.kurva?'ON':'OFF'} | баница:${e.modes.banitsa?'ON':'OFF'} | godmode:${e.modes.godmode?'ON':'OFF'}</div>
      <hr/>
      <b>Intent:</b> ${e.intent||''}<br/>
      <b>Spark:</b> ${e.spark||''}<br/>
      <b>Synthesis 3×3</b><br/>• Fact — ${e.fact||''}<br/>• Step — ${e.step||''}<br/>• Guard — ${e.guard||''}
    </div>
  `).join('');
}
function exportState(){
  const blob = new Blob([JSON.stringify(state,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download='mindcopy_state.json'; a.click(); URL.revokeObjectURL(url);
}
function importState(ev){
  const f = ev.target.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = () => { try{ state = JSON.parse(r.result); save(); location.reload(); }catch(e){ alert('Invalid file'); } };
  r.readAsText(f);
}

window.addEventListener('load', async ()=>{
  renderModes(); renderMindprint(); renderLogs();
  await showDoc(document.getElementById('doc_hc'), './data/HEART_CORE_v3_1.md');
  await showDoc(document.getElementById('doc_fl'), './data/HEART_CORE_FreeLayer_v1.md');
  await showDoc(document.getElementById('doc_ritual'), './data/SevenDay_Cahetel_Ritual.md');
  if('serviceWorker' in navigator){ try{ await navigator.serviceWorker.register('./service-worker.js'); }catch(e){} }
});
