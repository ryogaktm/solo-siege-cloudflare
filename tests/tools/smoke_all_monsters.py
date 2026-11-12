import sys,json
from playwright.sync_api import sync_playwright
JS="""async(idx)=>{
 const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const hide=()=>document.querySelectorAll('.modal-bg').forEach(m=>{ if(m.id) m.style.display='none'; else m.remove(); });
 const w=WAVES[idx]; CHARACTER=makeMonChar(idx,w.baseId); init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; hide();
 const log=[]; 
 for(let wv=0;wv<2;wv++){
   waveAdvancing=false; busy=false; pending=null; gold=500; playerHp=playerHpMax=Math.max(playerHpMax,5000); carryMap={red:3,green:3,yellow:3,blue:3,purple:3};
   // 特殊技
   try{ const m=CHARACTER.monSkill; if(m&&m.kind&&SKFN[m.kind]){ SKFN[m.kind](m); await sleep(120); const pk=document.querySelector('[data-i="0"]'); if(pk){ pk.click(); await sleep(150); } hide(); busy=false; pending=null; }
        else if(m&&m.kind){ try{ monSkillUse(); await sleep(150); hide(); busy=false; pending=null; }catch(e){ log.push('skill '+e.message); } } }catch(e){ log.push('SKFN '+(CHARACTER.monSkill&&CHARACTER.monSkill.kind)+': '+e.message); }
   let guard=0;
   while(flags.some(f=>!f.closed) && guard<80 && !gameEnded){ guard++;
     const T=hand.map((c,i)=>({c,i})).filter(x=>x.c&&x.c.kind==='troop');
     const open=flags.map((f,i)=>i).filter(i=>!flags[i].closed&&!isLocked(flags[i]));
     let placed=false; busy=false;
     for(const t of T){ for(const fi of open){ try{ if(playOnFlag(t.i,fi,null,true)){ placed=true; break; } }catch(e){ log.push('place '+e.message); } } if(placed) break; }
     await sleep(25); hide();
     if(!placed){ busy=false; try{ const i=hand.findIndex(c=>!isCurse(c)); if(i<0) break; discardDraw(i); }catch(e){ log.push('discard '+e.message); break; } await sleep(25); }
   }
   await sleep(2600); hide(); busy=false; waveAdvancing=false; pending=null;
   if(gameEnded) { log.push('ended'); break; }
   try{ if(inPrep||document.getElementById('prepModal')){ hide(); inPrep=false; advanceToNextStage(); hide(); } }catch(e){ log.push('adv '+e.message); }
   await sleep(200); hide();
 }
 return log }"""
start,end=int(sys.argv[1]),int(sys.argv[2])
with sync_playwright() as p:
    b=p.chromium.launch(); out={}
    for idx in range(start,end):
        pg=b.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
        pg.on('console',lambda m: errs.append('console:'+m.text[:200]) if m.type=='error' and 'net::' not in m.text and 'Failed to load' not in m.text else None)
        pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1')")
        pg.goto('file:///home/claude/solo-siege-cloudflare/public/index.html'); pg.wait_for_timeout(300)
        try:
            name=pg.evaluate("i=>dispName(WAVES[i].baseId)",idx); log=pg.evaluate(JS,idx)
        except Exception as e:
            log=['EVAL '+str(e)[:300]]; name=str(idx)
        if errs or [l for l in log if l!='ended']: print(idx,name,json.dumps({'log':log,'errs':list(dict.fromkeys(errs))[:5]},ensure_ascii=False),flush=True)
        pg.close()
    print('done',start,end,flush=True)
