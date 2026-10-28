"""収支シミュレーション：簡易ボット（同色・同数字・連番を狙って置く）で1WAVEあたりに何Gたまるかを測る。使い方: python3 tests/tools/economy_sim.py [WAVE数]
結果は目安（人間より弱いボット）。"""
import sys,os,json
from playwright.sync_api import sync_playwright
GAME='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','public','index.html'))
JS="""async(n)=>{
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 CHARACTER=CHARACTERS[1]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display='';
 document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none');
 const res=[]; 
 for(let w=0;w<n;w++){
   waveAdvancing=false; busy=false; pending=null; gold=0; bossHp=1e9; displayedBossHp=bossHp; playerHp=playerHpMax=1e9;
   const g0=gold; let guard=0, tries=0;
   while(flags.some(f=>!f.closed) && guard<200){ guard++;
     let placed=false;
     const T=hand.map((c,i)=>({c,i})).filter(x=>x.c&&x.c.kind==='troop'&&!x.c.mixed);
     const open=flags.map((f,i)=>i).filter(i=>!flags[i].closed&&!isLocked(flags[i]));
     const sc=(f,c)=>{ const cs=f.cards.filter(x=>x.kind==='troop'); if(!cs.length) return 0.5;
        const col=cs.every(x=>x.color===c.color), val=cs.every(x=>x.value===c.value);
        const vs=cs.map(x=>x.value).concat(c.value).sort((x,y)=>x-y), seq=vs.every((v,k)=>k==0||v-vs[k-1]===1);
        let s=0; if(col) s+=2; if(val) s+=2; if(seq) s+=1.5; if(cs.length===2&&(col||val||seq)) s+=5; return s; };
     let best=null; for(const fi of open){ for(const t of T){ const s2=sc(flags[fi],t.c)+(flags[fi].cards.length)*0.3; if(!best||s2>best.s) best={s:s2,fi,hi:t.i}; } }
     if(best&&best.s>=1.5||(best&&flags.every(f=>f.closed||f.cards.length>0))){ busy=false; placed=playOnFlag(best.hi,best.fi,null,true); }
     if(!placed&&best){ const e=open.filter(i=>flags[i].cards.length===0); if(e.length){ busy=false; placed=playOnFlag(best.hi,e[0],null,true); } }
     if(!placed&&best){ busy=false; placed=playOnFlag(best.hi,best.fi,null,true); }
     await sleep(30);
     if(!placed){ // 置けない：手札を1枚捨てて引く（ゲーム同様）
       busy=false; try{ const c=hand.splice(0,1)[0]; graveyard.push(c); drawToHand&&drawToHand(); }catch(e){ break; } tries++; if(tries>60) break; }
   }
   await sleep(100);
   const roles=flags.filter(f=>f.closed&&f.result).map(f=>f.result.name);
   res.push({gold:gold-g0,roles});
   busy=false; waveAdvancing=false; pending=null; try{ showPrep(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); inPrep=false; advanceToNextStage(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); }catch(e){ res.push({err:String(e)}); break; }
 }
 return res }"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':420,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1')")
    pg.goto(GAME); pg.wait_for_timeout(500)
    r=pg.evaluate(JS,int(sys.argv[1]) if len(sys.argv)>1 else 30)
    from collections import Counter
    c=Counter(x for w in r for x in w.get('roles',[])); g=[w['gold'] for w in r if 'gold' in w]
    print('waves',len(g),'avg gold/wave',sum(g)/max(1,len(g)),'min',min(g),'max',max(g)); print(dict(c)); print(errs[:3])
