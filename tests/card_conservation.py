"""カード保存テスト：各カード効果の前後で、カードが勝手に増減しないか（台帳LGも含めて）を調べる。"""
import sys,json,os
GAME='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','public','index.html'))
failed=0
from playwright.sync_api import sync_playwright
LIB="""
window.T={
 sleep:ms=>new Promise(r=>setTimeout(r,ms)),
 gt(){ const m={}; [activeDeck,grandDeck,hand,graveyard,stomach,pendingRewardCards,sealedCards,...flags.map(f=>f.cards),...accOwned.map(o=>o.held||[])].forEach(arr=>(arr||[]).forEach(c=>{ if(c&&!c.temp&&!c.enemyPlaced&&!isCurse(c)&&!(c.uid in m)) m[c.uid]=[c.kind,c.color||'',c.altColor||'',c.mixed?1:0,(c.origValue!==undefined?c.origValue:c.value),c.name||'',c.type||'',c.sub||'',c.purchased?1:0].join('|'); })); return m; },
 diff(a,b){ const o=[]; for(const k in a){ if(!(k in b)){ o.push((a[k].endsWith('|1')?'使い切り(OK) ':'消えた ')+k+' '+a[k]); } else if(a[k]!==b[k]) o.push('変化 '+k+' '+a[k]+' → '+b[k]); } for(const k in b) if(!(k in a)) o.push('増えた '+k+' '+b[k]); return o; },
 hide(){ document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); },
 fresh(ci){ dbgClear(); CHARACTER=makeMonChar(ci); init(); T.hide(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; waveAdvancing=false; busy=false; pending=null; gameEnded=false; bossHp=999999; displayedBossHp=bossHp; playerHp=playerHpMax=99999; lgCheck('start'); activeDeck.push(...hand.splice(0)); render(); },
 take(pred){ for(const arr of [hand,activeDeck,grandDeck,graveyard]){ const i=arr.findIndex(c=>c&&!c.purchased&&!c.temp&&pred(c)); if(i>=0){ return arr.splice(i,1)[0]; } } return null; },
 toHand(...cs){ cs.filter(Boolean).forEach(c=>hand.push(c)); render(); },
 hi(c){ return hand.indexOf(c); },
 cycle(n){ for(let k=0;k<(n||1);k++){ busy=false; waveAdvancing=false; pending=null; lgCheck('battle_end'); showPrep(); T.hide(); inPrep=false; advanceToNextStage(); T.hide(); bossHp=999999; displayedBossHp=bossHp; playerHp=playerHpMax=99999; busy=false; waveAdvancing=false; } },
 place(c,fi){ const i=hand.indexOf(c); if(i<0) return false; const ok=playOnFlag(i,fi,null,true); busy=false; return ok; },
 anomalies(){ return dbgLog.filter(e=>e.type==='card_audit'&&!e.ok).map(e=>e.tag+': '+e.anom.join(' / ')); },
 troop(pred){ return T.take(c=>c.kind==='troop'&&!c.mixed&&(!pred||pred(c))); },
 tac(type){ return T.take(c=>c.kind==='tactics'&&c.type===type); },
};
"""
SC={}
SC['鼓舞']="""async()=>{ const a=T.gt(); const ins=T.tac('inspire'); const t=[T.troop(),T.troop(),T.troop(),T.troop()]; T.toHand(ins,...t); busy=false; useInspire(T.hi(ins)); await T.sleep(300); busy=false; T.place(hand.find(c=>c.kind==='troop'),0); T.place(hand.find(c=>c.kind==='troop'),0); T.cycle(2); return T.diff(a,T.gt()); }"""
SC['複製']="""async()=>{ const a=T.gt(); const d=T.tac('duplicate'); const t=[T.troop(),T.troop()]; T.toHand(d,...t); busy=false; useDuplicate(T.hi(d)); resolveDuplicate(T.hi(t[0])); await T.sleep(200); busy=false; T.place(t[1],0); T.place(hand.find(c=>c.temp),1); T.cycle(2); return T.diff(a,T.gt()); }"""
SC['融合(足して10以下)']="""async()=>{ const a=T.gt(); const f=T.tac('fusion'); const t1=T.troop(c=>c.value<=4), t2=T.troop(c=>c.value<=5&&c.color!==t1.color); T.toHand(f,t1,t2); busy=false; useFusion(T.hi(f)); pending.chosen=[T.hi(t1),T.hi(t2)]; resolveFusion(); await T.sleep(200); busy=false; hand.filter(c=>c.kind==='troop').slice(0,2).forEach(c=>T.place(c,0)); T.cycle(2); return T.diff(a,T.gt()); }"""
SC['融合(10超え分裂)']="""async()=>{ const a=T.gt(); const f=T.tac('fusion'); const t1=T.troop(c=>c.value>=7), t2=T.troop(c=>c.value>=6&&c.color!==t1.color); T.toHand(f,t1,t2); busy=false; useFusion(T.hi(f)); pending.chosen=[T.hi(t1),T.hi(t2)]; resolveFusion(); await T.sleep(200); busy=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['再雇用']="""async()=>{ const a=T.gt(); const r=T.tac('rehire'); const g=[T.troop(),T.troop()]; graveyard.push(...g); T.toHand(r); busy=false; useRehire(T.hi(r)); resolveRehire(graveyard.indexOf(g[0])); await T.sleep(200); busy=false; T.place(g[0],0); T.cycle(2); return T.diff(a,T.gt()); }"""
SC['補充']="""async()=>{ const a=T.gt(); const s=T.tac('scout'); T.toHand(s); busy=false; useScout(T.hi(s)); await T.sleep(700); pending.chosen=[0,1]; confirmDiscard(); await T.sleep(500); busy=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['差し替え']="""async()=>{ const a=T.gt(); const s=T.tac('shuffle'); const t=[T.troop(),T.troop(),T.troop()]; T.toHand(s,...t); busy=false; useShuffle(T.hi(s)); pending.chosen=[T.hi(t[0]),T.hi(t[1])]; confirmReplace(); await T.sleep(900); busy=false; pending=null; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['全滅']="""async()=>{ const a=T.gt(); const w=T.tac('wipe'); const t=[T.troop(),T.troop()]; T.toHand(w,...t); busy=false; T.place(t[0],0); T.place(t[1],0); T.place(w,0); await T.sleep(800); busy=false; pending=null; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['誘導']="""async()=>{ const a=T.gt(); const g=T.tac('guidance'); const t=[T.troop(),T.troop()]; T.toHand(g,...t); busy=false; T.place(t[0],0); T.place(t[1],0); busy=false; useGuidance(T.hi(g)); tapFlag(0); await T.sleep(200); try{ if(pending&&pending.step==='choose'){ guidanceChoose&&0; } }catch(e){} tapFlag(1); await T.sleep(600); busy=false; pending=null; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['青♾️を置く']="""async()=>{ const a=T.gt(); const w=T.tac('alexander'); if(!w) return ['（山札になし）']; const t=[T.troop(),T.troop()]; T.toHand(w,...t); busy=false; T.place(w,0); T.place(t[0],0); T.place(t[1],0); await T.sleep(800); busy=false; T.cycle(3); return T.diff(a,T.gt()); }"""
SC['赤♾️を置く']="""async()=>{ const a=T.gt(); const w=T.tac('darius'); if(!w) return ['（山札になし）']; const t=[T.troop(),T.troop()]; T.toHand(w,...t); busy=false; T.place(t[0],0); T.place(t[1],0); T.place(w,0); await T.sleep(800); busy=false; T.cycle(3); return T.diff(a,T.gt()); }"""
SC['力の装備']="""async()=>{ const a=T.gt(); const e=T.take(c=>c.kind==='monster'&&c.sub==='number'); if(!e) return ['（なし）']; const t=T.troop(c=>c.value>=e.value); T.toHand(e,t); busy=false; T.place(e,2); busy=false; T.place(t,2); await T.sleep(800); busy=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['色の装備（染める）']="""async()=>{ const a=T.gt(); const e=T.take(c=>c.kind==='monster'&&c.sub==='mark'); if(!e) return ['（なし）']; const t=[T.troop(),T.troop()]; T.toHand(e,...t); busy=false; T.place(t[0],3); T.place(t[1],3); busy=false; T.place(e,3); await T.sleep(800); busy=false; T.cycle(3); return T.diff(a,T.gt()); }"""
SC['鍛治職人']="""async()=>{ let n=T.take(c=>c.kind==='monster'&&c.sub==='necro'); if(!n){ n={kind:'monster',sub:'necro',name:'鍛治職人',uid:uid()}; lgOp('テスト:鍛治職人を用意',()=>hand.push(n)); } const a2=T.gt(); const e=[T.take(c=>c.kind==='monster'&&c.sub==='number'),T.take(c=>c.kind==='monster'&&c.sub==='mark')].filter(Boolean); graveyard.push(...e); busy=false; const a=T.gt(); useNecromancer(T.hi(n)); await T.sleep(300); busy=false; T.cycle(2); const z=T.gt(); delete a[n.uid]; delete z[n.uid]; return T.diff(a,z); }"""
SC['モンスター技:一刺し/毒の牙']="""async()=>{ const a=T.gt(); for(const k of ['sting','fang']){ CHARACTER.monSkill={kind:k}; monSkillUse(); } busy=false; T.place(hand.find(c=>c.temp),0); T.cycle(2); return T.diff(a,T.gt()); }"""
SC['モンスター技:飲み込む']="""async()=>{ const a=T.gt(); CHARACTER.monSkill={kind:'swallow'}; monSkillUse(); swallowTap(0); busy=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['モンスター技:悪食']="""async()=>{ const a=T.gt(); CHARACTER.monSkill={kind:'eat'}; monSkillUse(); eatTap(0); busy=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['WAVE進行(盤面あり)']="""async()=>{ const a=T.gt(); const t=[T.troop(),T.troop(),T.troop()]; T.toHand(...t); busy=false; t.forEach(c=>T.place(c,0)); await T.sleep(500); busy=false; try{ advanceWaveAttempt(); }catch(e){ return ['ERR '+e]; } busy=false; waveAdvancing=false; T.cycle(2); return T.diff(a,T.gt()); }"""
SC['山札切れまで引く']="""async()=>{ const a=T.gt(); let n=0; while(activeDeck.length+grandDeck.length>0&&n<200){ const c=drawFromPools(); if(!c) break; graveyard.push(c); n++; } for(let k=0;k<30;k++){ const c=drawFromPools(); if(c) graveyard.push(c); } T.cycle(2); return T.diff(a,T.gt()); }"""
RES={}
with sync_playwright() as p:
    b=p.chromium.launch()
    ci=int(sys.argv[1]) if len(sys.argv)>1 else 5
    for name,js in SC.items():
        pg=b.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1')")
        pg.goto(GAME); pg.wait_for_timeout(400)
        pg.evaluate(LIB)
        pg.evaluate("(ci)=>T.fresh(ci)",ci)
        try:
            d=pg.evaluate(js); an=pg.evaluate("T.anomalies()")
        except Exception as e:
            d=['TEST ERR '+str(e)[:200]]; an=[]
        print(('OK  ' if not d and not an else 'NG  ')+name, ('| 差分: '+' ; '.join(d[:6])) if d else '', ('| 台帳: '+' ; '.join(an[:3])) if an else '', ('| JSERR '+errs[0][:120]) if errs else '')
        if d or an: failed+=1
        pg.close()
    b.close()
print('FAILED' if failed else 'ALL OK', failed)
sys.exit(1 if failed else 0)
