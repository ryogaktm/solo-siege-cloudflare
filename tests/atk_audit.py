# 表示されている攻撃力(liveAtk) と 実際の攻撃(attack_calc の pAtk) が同じかを、いろいろな状態で確かめる
from playwright.sync_api import sync_playwright
import json,sys
JS = """async()=>{
  const out=[]; let cap=null; const _d=dlog; dlog=function(t,d){ if(t==='attack_calc') cap=d; try{ return _d.apply(this,arguments); }catch(e){} };
  const reset=(ch)=>{ CHARACTER=ch; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; waveAdvancing=false; gameEnded=false; enemySched={}; playerHp=playerHpMax=1e9; bossHp=1e12; };
  const T=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()});
  const board=(open)=>{ const cols=GAME_COLORS; flags.forEach((f,i)=>{ f.cards=[]; f.closed=false; f.result=null; });
    const sets=[[['red',2],['red',5],['red',6]],[['red',3],['red',4],['red',9]],[[cols[1],7],[cols[1],8],[cols[1],9]],[[cols[2],1],[cols[3%cols.length],4],[cols[1],9]]];
    flags.forEach((f,i)=>{ const s=sets[i%sets.length]; const n=(open&&i===flags.length-1)?2:3; f.cards=s.slice(0,n).map(([c,v])=>T(c,v)); closeCheck(i); }); };
  const run=(name,ch,prep,open,pre)=>{ try{ reset(ch); if(pre) pre(); board(open); if(prep) prep(); render();
      const disp=liveAtk(); cap=null; Math.random=()=>0.99; checkWaveOutcome(); const act=cap?cap.pAtk:null;
      const ok=act!=null&&Math.abs(Math.round(disp)-Math.round(act))<=1; out.push({name,disp:Math.round(disp),act:act==null?null:Math.round(act),ok}); }catch(e){ out.push({name,err:String(e)}); } };
  const base=CHARACTERS[2];
  run('ふつう',base);
  run('スーパーコンボ持ち越し',base,()=>{ carryMap={red:5}; });
  run('火炎放射',base,()=>{ fireOn=true; carryMap={red:5}; });
  run('闇の誓い',base,()=>{ atkFx.oath=true; });
  run('突進',base,()=>{ atkFx.rush=true; });
  run('急降下',base,()=>{ atkFx.dive=true; });
  run('石の体',base,()=>{ atkFx.golem=true; });
  run('ためる',base,()=>{ monkQ=[0.5,2]; });
  run('攻撃倍率plAtkMult',base,()=>{ plAtkMult=3; });
  run('敵の防御(半減)',base,()=>{ dis.halfNext=true; });
  run('毒',base,()=>{ poisonPenalty=40; });
  run('防御カード',base,()=>{ defendOn=true; });
  run('突撃（未完成の旗あり）',base,null,true);
  ACC_DEFS_ALL.forEach(d=>{ if(d.id==='gambler') return; run('アクセ:'+d.name,base,()=>{ carryMap={red:5}; refreshClosedFlags&&refreshClosedFlags(); },false,()=>{ accOwned=[{aid:1,id:d.id}]; accEq=[1]; try{ recalcHpMax(); }catch(e){} playerHp=playerHpMax; }); });
  WAVES.forEach((w,i)=>{ try{ const ch=makeMonChar(i,w.baseId); run('体:'+dispName(w.baseId),ch,()=>{ carryMap={red:3}; }); }catch(e){ out.push({name:'体:'+i,err:String(e)}); } });
  return out; }"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1')")
    pg.goto('file:///home/claude/solo-siege-cloudflare/public/index.html'); pg.wait_for_timeout(800)
    r=pg.evaluate(JS)
    bad=[x for x in r if not x.get('ok')]
    print('cases',len(r),'bad',len(bad))
    for x in bad: print(json.dumps(x,ensure_ascii=False))
    print('pageerr',len(errs),errs[:3])
    # 「旗の攻撃力」に効く技は、旗に出ている数字（スーパーコンボこみ）を基準にしているか
    r2=pg.evaluate("""()=>{ const o={};
      const reset=()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; waveAdvancing=false; enemySched={}; playerHp=playerHpMax=1e9; bossHp=1e12;
        const T=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()}); flags.forEach(f=>{ f.cards=[]; f.closed=false; f.result=null; });
        [[['red',2],['red',5],['red',6]],[['red',3],['red',4],['red',9]],[[GAME_COLORS[1],7],[GAME_COLORS[1],8],[GAME_COLORS[1],9]]].forEach((s,i)=>{ flags[i].cards=s.map(([c,v])=>T(c,v)); closeCheck(i); }); carryMap={red:5}; };
      const shown=()=>flags.map(f=>f.closed?Math.round(flagShown(f)):0);
      const skPay0=skPay; skPay=()=>true;
      reset(); let a=shown(), l0=liveAtk(); fireOn=true; o.fire=Math.round(liveAtk()-l0)===a[0]+a[1];
      reset(); a=shown(); const mxI=a.indexOf(Math.max(...a)); NEWMON_FX.stampede[1](); let b=shown(); o.stampede=b[mxI]===a[mxI]*2;
      reset(); a=shown(); SKFN.lead({}); b=shown(); const mnI=a.indexOf(Math.min(...a.slice(0,3))); o.lead=Math.abs(b[mnI]-Math.max(...a))<=Math.max(2,flagMul(flags[mnI]));
      reset(); const sc0=score; o.openBefore=liveAtk(); flags[3].cards=[{kind:'troop',color:'red',value:10,uid:uid()},{kind:'troop',color:'red',value:10,uid:uid()}]; o.open=Math.round(liveAtk()-o.openBefore)===20;
      hand=[{kind:'tactics',...TACTICS.find(t=>t.type==='conscript'),uid:uid()}]; const e0=enemyTurn; useTacticByIdx(0,hand[0]); o.confirm=document.getElementById('confirmModal').style.display==='flex'&&hand.length===1&&!waveAdvancing;
      skPay=skPay0; return o }""")
    print('semantic',r2)
    if bad or not all(r2.values()): print('FAILED'); sys.exit(1)
    print('ALL OK')
