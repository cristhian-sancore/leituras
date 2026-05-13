// editor.js – funcionalidade do editor CPCL usando Fabric.js
// ---------------------------------------------------------------
// Configurações da etiqueta (ZQ520 – 104mm / ZQ521)
const DOTS_W = 200;               // resolução DPI
const DOTS_H = 1200;              // altura em dots no cabeçalho
const SCALE_X = 8;                // 1 mm = 8px no canvas
const SCALE_Y = 8;                // 1 mm = 8px no canvas

// Inicializa Fabric.js
const canvas = new fabric.Canvas('cvs', {
  backgroundColor: '#fff',
  selection: true,
  preserveObjectStacking: true,
});

/*** UTILIDADES ***/
const $ = selector => document.querySelector(selector);
function showToast(msg){
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),1800);
}

/*** TOOLBAR – criação de objetos ***/
let currentTool = null;
function setTool(tool){
  currentTool = tool;
  // desativa modo de desenho ao mudar ferramenta
  canvas.isDrawingMode = false;
}

// Botões de ferramenta
document.querySelectorAll('.tool-btn').forEach(btn=>{
  btn.addEventListener('click',()=> {
    const tool = btn.dataset.tool;
    const x = 50; // default left
    const y = 50; // default top
    
    if(tool === 'addText'){
      const txt = new fabric.IText('Texto', {
        left:x,
        top:y,
        fontFamily:'Inter',
        fontSize:16,
        fill:'#000',
      });
      canvas.add(txt).setActiveObject(txt);
    }else if(tool === 'addRect'){
      const rect = new fabric.Rect({
        left:x,
        top:y,
        width:80,
        height:40,
        fill:'transparent',
        stroke:'#333',
        strokeWidth:1,
      });
      canvas.add(rect).setActiveObject(rect);
    }else if(tool === 'addLine'){
      const line = new fabric.Line([x, y, x+80, y], {
        stroke:'#333',
        strokeWidth:1,
      });
      canvas.add(line).setActiveObject(line);
    }
    
    showToast('Adicionado!');
  });
});

/*** PROPRIEDADES – aplica a objetos selecionados ***/
function loadProperties(obj){
  if(!obj) { $('#propPanel').classList.add('hidden'); return; }
  $('#propPanel').classList.remove('hidden');
  // fonte (apenas para textos)
  if(obj.type==='i-text'){
    $('#fontFamily').value = obj.fontFamily === 'Inter' ? '5' : '7';
    $('#fontSize').value   = obj.fontSize;
    $('#fontColor').value  = obj.fill;
  }else{
    // para retângulo/linha, apenas cor de preenchimento ou traço
    $('#fontFamily').value = '5';
    $('#fontSize').value   = 12;
    $('#fontColor').value  = obj.stroke || '#000';
  }
}
canvas.on('selection:created', e=> loadProperties(e.target));
canvas.on('selection:updated', e=> loadProperties(e.target));
canvas.on('selection:cleared', ()=> loadProperties(null));

// Aplicar propriedades ao objeto selecionado
$('#applyProps').addEventListener('click',()=>{
  const obj = canvas.getActiveObject();
  if(!obj) return;
  const font = $('#fontFamily').value;
  const size = parseInt($('#fontSize').value,10);
  const color = $('#fontColor').value;
  if(obj.type==='i-text'){
    obj.set({fontFamily:font==='5'?'Inter':'Inter', fontSize:size, fill:color});
  }else if(obj.type==='rect' || obj.type==='line'){
    obj.set({stroke:color});
  }
  canvas.renderAll();
  generateCPCL();
});

/*** GERAÇÃO DO CPCL ***/
let isImporting = false;
function mapCanvasToDots(val){ return Math.round(val / SCALE_X); }
function generateCPCL(){
  if (isImporting) return;
  let cpcl = `! 0 ${DOTS_W} ${DOTS_W} ${DOTS_H} 1\r\nIN-MILLIMETERS\r\nCOUNTRY LATIN9\r\n`;
  // percorre objetos na ordem de criação (stack)
  canvas.getObjects().forEach(obj=>{
    if(obj.type==='i-text'){
      const x = mapCanvasToDots(obj.left);
      const y = mapCanvasToDots(obj.top);
      const txt = obj.text.replace(/\r?\n/g,' ');
      // fonte CPCL: usamos 5 (normal) ou 7 (grande) – mapeamos de acordo com fontSize
      const cpclFont = obj.fontSize>14 ? '7' : '5';
      cpcl += `T ${cpclFont} 0 ${x} ${y} ${txt}\r\n`;
    }else if(obj.type==='rect'){
      const x0 = mapCanvasToDots(obj.left);
      const y0 = mapCanvasToDots(obj.top);
      const x1 = mapCanvasToDots(obj.left + obj.width);
      const y1 = mapCanvasToDots(obj.top + obj.height);
      cpcl += `LINE ${x0} ${y0} ${x1} ${y1} 0.2\r\n`;
    }else if(obj.type==='line'){
      if(obj.stroke === '#e5e7eb') return; // ignora o grid
      const x0 = mapCanvasToDots(obj.left);
      const y0 = mapCanvasToDots(obj.top);
      const x1 = mapCanvasToDots(obj.left + obj.width);
      const y1 = mapCanvasToDots(obj.top + obj.height);
      cpcl += `LINE ${x0} ${y0} ${x1} ${y1} 0.2\r\n`;
    }
  });
  cpcl += 'FORM\r\nPRINT\r\n';
  $('#cpclRaw').textContent = cpcl;
}

// Atualiza CPCL ao mudar o canvas
canvas.on('object:added', generateCPCL);
canvas.on('object:modified', generateCPCL);
canvas.on('object:removed', generateCPCL);

/*** AÇÕES DE EXPORTAÇÃO ***/
$('#exportBtn').addEventListener('click',()=>{ generateCPCL(); showToast('✅ CPCL atualizado'); });
$('#copyBtn').addEventListener('click',()=>{
  generateCPCL();
  navigator.clipboard.writeText($('#cpclRaw').textContent).then(()=>showToast('📋 CPCL copiado'));
});
$('#importBtn').addEventListener('click', loadOriginalCpcl);
$('#downloadBtn').addEventListener('click',()=>{
  generateCPCL();
  const blob = new Blob([$('#cpclRaw').textContent],{type:'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'layout_zq520.cpcl';
  a.click();
  showToast('⬇ Arquivo baixado');
});

$('#applyPaperSize').addEventListener('click', () => {
  const w = parseFloat($('#paperWidth').value) || 105;
  const h = parseFloat($('#paperHeight').value) || 250;
  
  canvas.setWidth(w * SCALE_X);
  canvas.setHeight(h * SCALE_Y);
  
  // Re-draw grid
  const objs = canvas.getObjects();
  objs.filter(o => o.stroke === '#e5e7eb').forEach(o => canvas.remove(o));
  drawGrid();
  
  showToast(`Bobina ajustada para ${w}x${h} mm`);
});

// Inicializa canvas vazio com grid opcional
function drawGrid(){
  const step = 20; // 20px ~ 10 dots
  for(let i=0;i<canvas.width;i+=step){
    canvas.add(new fabric.Line([i,0,i,canvas.height],{stroke:'#e5e7eb',strokeWidth:0.5, selectable:false, evented:false}));
  }
  for(let j=0;j<canvas.height;j+=step){
    canvas.add(new fabric.Line([0,j,canvas.width,j],{stroke:'#e5e7eb',strokeWidth:0.5, selectable:false, evented:false}));
  }
}
drawGrid();
generateCPCL();

function loadOriginalCpcl(){
  fetch('/orig_cpcl.txt?t=' + Date.now())
    .then(r => r.text())
    .then(cpcl => {
      $('#cpclRaw').textContent = cpcl;
      parseCpclToCanvas(cpcl);
      showToast('Layout original carregado!');
    })
    .catch(err => {
      console.error(err);
      showToast('Falha ao carregar layout original');
    });
}

function parseCpclToCanvas(cpcl) {
  isImporting = true;
  canvas.clear();
  canvas.backgroundColor = '#fff';
  drawGrid();

  const lines = cpcl.split(/\r?\n/);
  
  lines.forEach(line => {
    line = line.trim();
    if (!line) return;

    if (line.startsWith('T ')) {
      // T <font> <size> <x> <y> <text...>
      const parts = line.split(' ');
      if (parts.length < 6) return;
      const font = parts[1]; // '5' ou '7'
      const x = parseFloat(parts[3]) * SCALE_X;
      const y = parseFloat(parts[4]) * SCALE_Y;
      const text = parts.slice(5).join(' ');
      
      const fontSize = font === '7' ? 18 : 14;

      const txtObj = new fabric.IText(text, {
        left: x,
        top: y,
        fontFamily: 'Inter',
        fontSize: fontSize,
        fill: '#000'
      });
      canvas.add(txtObj);
    } 
    else if (line.startsWith('LINE ')) {
      // LINE <x0> <y0> <x1> <y1> <width>
      const parts = line.split(' ');
      if (parts.length < 5) return;
      const x0 = parseFloat(parts[1]) * SCALE_X;
      const y0 = parseFloat(parts[2]) * SCALE_Y;
      const x1 = parseFloat(parts[3]) * SCALE_X;
      const y1 = parseFloat(parts[4]) * SCALE_Y;
      
      const lineObj = new fabric.Line([x0, y0, x1, y1], {
        stroke: '#333',
        strokeWidth: 1
      });
      canvas.add(lineObj);
    }
    else if (line.startsWith('B ')) {
      // Código de Barras (exemplo B I2OF5 0.245 25 8 0 212 data)
      const parts = line.split(' ');
      if (parts.length > 7) {
        const x = parseFloat(parts[5]) * SCALE_X;
        const y = parseFloat(parts[6]) * SCALE_Y;
        
        const rectObj = new fabric.Rect({
          left: x,
          top: y,
          width: 320,
          height: 40,
          fill: 'transparent',
          stroke: '#333',
          strokeWidth: 1,
          strokeDashArray: [4, 4]
        });
        canvas.add(rectObj);
        
        const txtObj = new fabric.IText('[CÓDIGO DE BARRAS]', {
          left: x + 10,
          top: y + 12,
          fontFamily: 'Inter',
          fontSize: 14,
          fill: '#555',
          fontWeight: 'bold'
        });
        canvas.add(txtObj);
      }
    }
  });
  
  canvas.renderAll();
  isImporting = false;
}
