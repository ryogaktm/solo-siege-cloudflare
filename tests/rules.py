"""ルールテスト：敵の並び・序盤の妨害・防御の演出・手付金など、決めたルールが守られているかを調べる。"""
import sys,os
from playwright.sync_api import sync_playwright
GAME='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','public','index.html'))
fails=[]
def check(name,ok,detail=''):
    print(('OK  ' if ok else 'NG  ')+name+(' | '+str(detail) if (detail and not ok) else '')); 
    if not ok: fails.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':420,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1');localStorage.setItem('soloSiegeAlienBeat',JSON.stringify(['月の民']))")
    pg.goto(GAME); pg.wait_for_timeout(600)
    ev=lambda js:pg.evaluate(js)
    check('起動でJSエラーが出ない',not errs,errs)
    check('通常の敵が84体',ev("()=>WAVES.filter(w=>!w.boss).length")==84)
    bad=ev("()=>{const n=WAVES.filter(w=>!w.boss);return n.filter((w,i)=>i&&w.hp<n[i-1].hp).map(w=>w.name)}")
    check('敵のHPが下がる箇所がない（順位が上がるほど強い）',not bad,bad)
    bad=ev("()=>{const n=WAVES.filter(w=>!w.boss);return n.filter((w,i)=>i&&w.atk<n[i-1].atk).map(w=>w.name)}")
    check('敵の攻撃力が下がる箇所がない',not bad,bad)
    bad=ev("()=>{const H=HARSH_DIS;return WAVES.filter(w=>!w.boss&&w.lv<DIS_PARAM.harshLv).filter(w=>disList(w).some(k=>H.includes(k))).map(w=>w.lv+w.name)}")
    check('序盤（harshLv未満）に防御・コンボ減らし系の妨害が出ない',not bad,bad)
    bad=ev("()=>WAVES.filter(w=>!w.boss&&w.lv>=DIS_START_LV&&w.lv<DIS_PARAM.harshLv).filter(w=>!disList(w).length).map(w=>w.lv+w.name)")
    check('序盤でも妨害技が1つ以上ある',not bad,bad)
    bad=ev("()=>WAVES.filter(w=>!w.boss&&w.lv>=DIS_START_LV&&w.lv<DIS_PARAM.harshLv).filter(w=>!disList(w).includes('autonum')&&w.lv<24).map(w=>w.lv+w.name)")
    check('レベル24未満の敵は数字カードを置く技（autonum）を持つ',not bad,bad)
    r=ev("""()=>{ dis.halfNext=false; applyEnemyEvent('half'); const a=[dis.halfNext,document.getElementById('fighterMo').classList.contains('guarding'),document.getElementById('evSweep').className.includes('shield')]; dis.halfNext=false; syncGuardFx(); return a.concat([document.getElementById('fighterMo').classList.contains('guarding')]) }""")
    check('防御：発動で半減フラグ・盾マーク・青い帯が出る／解除で盾が消える',r==[True,True,True,False],r)
    r=ev("""()=>{ gold=0; shopOnce={}; rollAccStock(); inPrep=true; openShop('buyacc');
      const id=shopStock[0], full=accPrice(accDef(id)); const out={};
      buyQty['acc_'+id]=1; gold=full+5; renderShop(); out.rich=document.querySelector('.shop-act .btn').textContent;
      gold=Math.ceil(full/2)+1; renderShop(); out.short=document.querySelector('.shop-act .btn').textContent;
      gold=Math.ceil(full/2)-1; renderShop(); out.poor=document.querySelector('.shop-act .btn').disabled;
      gold=Math.ceil(full/2)+1; renderShop(); document.querySelector('.shop-act .btn').click(); document.getElementById('cdYes').click();
      out.res=(shopOnce.res||{})[id]; out.gold=gold; rollAccStock(); out.kept=shopStock[0]===id;
      gold=full; renderShop(); buyQty['acc_'+id]=1; renderShop(); out.rem=document.querySelector('.shop-act .btn').textContent;
      out.id=id; out.full=full; return out}""")
    check('手付金：お金が足りている時は手付金が出ない',('手付金' not in r['rich']),r['rich'])
    check('手付金：足りない時だけ本来額と手付金額が出る',('手付金' in r['short'] and str(r['full']) in r['short']),r['short'])
    check('手付金：半額に届かない時は押せない',r['poor']==True)
    check('手付金：払うと取り置かれ、品揃えが変わっても残る',(r['res'] or {}).get('paid')==-(-r['full']//2) and r['kept'],r)
    check('手付金：取り置き後は残りの金額で買える',('買う' in r['rem'] and str(r['full']-(r['res'] or {}).get('paid',0)) in r['rem']),r['rem'])
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); const o={}; o.none=quickMult(5);
      accOwned.push({aid:accSeq++,id:'quick_boots'}); accEq.push(accOwned[accOwned.length-1].aid);
      o.in12=quickMult(ACC_PARAM.quickTurns); o.out=quickMult(ACC_PARAM.quickTurns+1); o.out16=quickMult(ACC_PARAM.quickTurns2+1);
      accOwned.push({aid:accSeq++,id:'double_x'}); accEq.push(accOwned[accOwned.length-1].aid); o.dbl=quickMult(3); return o}""")
    check('早撃ちのブーツ：持っていなければ等倍',r['none']==1,r)
    check('早撃ちのブーツ：12ターン以内は×5、13〜15ターンは×1.5、16ターン目からは等倍',r['in12']==5 and r['out']==1.5 and r['out16']==1,r)
    check('早撃ちのブーツ：倍の腕輪で増え分が2倍（×9）',r['dbl']==9,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); introOn=false; stageIndex=WAVES.findIndex(w=>w.lv===30); inPrep=false; const o={}; startBattleGoals();
      o.n1=accCond.n; o.cur1=!!accCond.cur; o.bar=document.getElementById('condBar').style.display!=='none'; o.txt=document.getElementById('condBar').textContent;
      // 1つ目をクリア→次の条件がひとつ出る
      accCond.cur='x:role2'; accCond.cur='x_role_2'; accStat.roles={'ウェッジ':2}; checkGoalAnnounce(false); o.picks1=accCond.picks; o.n2=accCond.n; o.next=accCond.cur&&accCond.cur!=='x_role_2';
      // 最後まで（最大3つ）
      accCond.cur='x_role_6'; accStat.roles={'ウェッジ':9}; accStat.super={red:9}; accStat.tac=9; accStat.maxKinds=9; accStat.maxSame=9; accStat.maxDealt=99999; for(let i=0;i<4;i++) checkGoalAnnounce(false);
      o.n3=accCond.n; o.picks3=accCond.picks; o.max=COND_MAX;
      // 最初の2つは「倒した時に判定」の条件にならない
      let bad=0; for(let t=0;t<40;t++){ startBattleGoals(); if(condDef(accCond.cur).final) bad++; checkGoalAnnounce(false); if(accCond.n===2&&accCond.cur&&condDef(accCond.cur).final) bad++; accStat=blankBattleStat(); } o.bad=bad;
      return o}""")
    check('取得条件：戦闘が始まると条件が1つ出て、戦闘画面に常に表示される',r['n1']==1 and r['cur1'] and r['bar'] and '1/3' in r['txt'],r)
    check('取得条件：クリアすると選択権が1回ふえ、次の条件がひとつ出る／最大3つで終わる',r['picks1']==1 and r['n2']==2 and r['next'] and r['n3']==3 and r['picks3']>=2 and r['max']==3,r)
    check('取得条件：最初の2つに「倒した時に判定」の条件は出ない',r['bad']==0,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS.find(c=>c.equipment&&c.tactics&&c.combo); init(); introOn=false; inPrep=false; const o={}; startBattleGoals();
      const txt=condPool().map(x=>x.g.text); o.two=txt.some(t=>/2色以上でスーパーコンボ/.test(t)); o.eq=txt.some(t=>/以上の装備カードを/.test(t)); o.tt=txt.some(t=>/軍師カード「/.test(t)); o.any=txt.some(t=>/^どれかの色でスーパーコンボを戦闘で×2以上決める/.test(t));
      accCond.cur='x_eq_5_1'; advanceTurn({kind:'monster',sub:'number',value:6,uid:uid()}); o.eqOk=accCond.picks===1;
      accCond.cur='x_two_2'; accStat.super={red:2,blue:3}; checkGoalAnnounce(false); o.twoOk=accCond.picks===2;
      const tt=condPool().find(x=>x.key.startsWith('x_tt_')&&x.key.endsWith('_1')); accCond.cur=tt.key; const ty=tt.key.split('_')[2]; advanceTurn({kind:'tactics',type:ty,uid:uid()}); o.ttOk=accCond.picks===3;
      // 難しさ：序盤の1個目は易しく、終盤の3個目は難しい（上がり方はゆるやか）
      o.t0=condTarget(0); stageIndex=LADDER_N-1; o.t2=condTarget(2); stageIndex=0; o.t1=condTarget(1);
      return o}""")
    check('取得条件：色を限定しない／2色以上のコンボ、5以上の装備カードを使う、特定の軍師カードを使う条件がある',r['two'] and r['eq'] and r['tt'] and r['any'] and r['eqOk'] and r['twoOk'] and r['ttOk'],r)
    check('取得条件：2個目・3個目や終盤ほど難しくなる（ゆるやかに）',r['t0']<r['t1'] and r['t1']<r['t2'] and r['t2']-r['t0']<=7,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS.find(c=>c.equipment&&c.tactics&&c.combo); init(); introOn=false; inPrep=false; startBattleGoals(); const o={}; const g1=condDef('x_allsame_1'), g3=condDef('x_allsame_3'); o.pool=condPool().some(x=>x.key==='x_allsame_3'); o.lv=[g1.lv,g3.lv];
      accStat.sameRun=2; accStat.maxSameRun=2; o.no=g3.done(); accStat.maxSameRun=3; o.yes=condDef('x_allsame_3').done(); return o}""")
    check('取得条件：全旗同色（1回）と、3回連続（究極）の条件がある',r['pool'] and r['lv'][1]>r['lv'][0] and r['no']==False and r['yes']==True,r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;inPrep=false; introOn=false; stageIndex=WAVES.findIndex(w=>w.lv===30); const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={};
      startBattleGoals(); accCond.picks=2; accCond.ok=['a','b']; accCond.used=['a','b','c']; accStat.roles={'ウェッジ':1}; const g0=gold; const own0=accOwned.length;
      grantStageReward(); await sleep(300);
      const ch=document.getElementById('chestModal'); o.chest=ch.style.display==='flex'; o.txt=ch.innerText; o.gold=gold-g0; o.total=lastBattleRes.total; o.okSum=lastBattleRes.money.filter(x=>x.ok).reduce((t,x)=>t+x.cash,0);
      ch.querySelector('.btn').click(); await sleep(100);
      const pk=()=>[...document.querySelectorAll('body > .modal-bg:not([id])')].filter(m=>m.style.display==='flex'&&m.innerText.includes('1つ選ぼう'));
      o.want=accCond.picks; o.p1=pk().length; o.opts=pk()[0]?pk()[0].querySelectorAll('.acc-opt').length:0; let k=0; while(pk().length&&k++<9){ pk()[0].querySelector('.acc-opt').click(); await sleep(100); }
      o.after=pk().length; o.owned=accOwned.length-own0; o.picks=accCond.picks; o.prep=document.getElementById('prepModal').style.display==='flex';
      return o}""")
    check('戦闘結果：基本条件のクリア数と合計金額が出て、お金が増える',r['chest'] and '基本条件' in r['txt'] and '合計' in r['txt'] and r['gold']==r['total'] and r['total']==r['okSum'] and r['total']>0,r)
    check('戦闘結果：クリアした回数だけ、3つの中から1つ選べて、終わると準備画面へ',r['want']>=2 and r['p1']==1 and r['opts']==3 and r['after']==0 and r['owned']==r['want'] and r['picks']==0 and r['prep'],r)
    r={'price':ev("()=>accPrice(accDef('quick_boots'))")}
    check('早撃ちのブーツ：値段は標準（150G）',r['price']==150,r)
    r=ev("""()=>{ gold=0; shopOnce={}; rollAccStock(); inPrep=true; openShop('buyacc'); const id=shopStock[0], full=accPrice(accDef(id)); const o={};
      const nm=accDef(id).name, row=()=>[...document.querySelectorAll('.acc-opt')].find(e=>e.querySelector('.reward-name').textContent.startsWith(nm)&&e.textContent.includes(full+'G'));
      gold=full+5; renderShop(); o.rich=/手付金/.test(row().textContent);
      gold=Math.ceil(full/2)+1; renderShop(); o.poor=/手付金/.test(row().textContent);
      o.full=full; return o}""")
    check('手付金：お金が足りている商品の行には手付金が出ない',r['rich']==False,r)
    check('手付金：足りない商品の行に手付金の額が出る',r['poor']==True,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display='';
      const o={}; spec.bullet=0; CHARACTER.sp=CHARACTER.sp||[]; if(!CHARACTER.sp.includes('bullet')) CHARACTER.sp.push('bullet');
      enemyTurn=3; turnCounter=3; bulletLeft=0; enemyFreeze=0;
      specUse('bullet'); o.after1=[bulletLeft,enemyFreeze];
      const t0=turnCounter, e0=enemyTurn; advanceTurn(null); advanceTurn(null); o.frozen=[turnCounter-t0, enemyTurn-e0, bulletLeft];
      const n0=document.querySelectorAll('.modal-bg').length; specUse('bullet'); o.second=bulletLeft; o.alert=[...document.querySelectorAll('.modal-bg')].some(m=>m.style.zIndex==='10001');
      for(let i=0;i<3;i++) advanceTurn(null); o.ended=bulletLeft; const t1=turnCounter,e1=enemyTurn; advanceTurn(null); o.moves=[turnCounter-t1,enemyTurn-e1]; return o}""")
    check('バレットタイム：使うと5ターン止まる',r['after1']==[5,5],r)
    check('バレットタイム中はターンも敵も進まない',r['frozen']==[0,0,3],r)
    check('バレットタイム：連続では使えず、アラートが出る',r['second']==3 and r['alert'],r)
    check('バレットタイム：終わったらターンが進み、また使える',r['ended']==0 and r['moves']==[1,1],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none');
      const i=WAVES.findIndex(w=>w.lv===20); stageIndex=i; nextStageIdx=i; enemyTurn=8; enemySched=genSchedule(); render(); renderUpcoming();
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), disp=()=>{const e=document.getElementById('evPopupBg'); return e?getComputedStyle(e).display:'none'};
      const c=document.querySelector('#upcomingRow2 .fc[data-ev]'); const rc=c.getBoundingClientRect(); const o={bubbles:true,clientX:rc.x+5,clientY:rc.y+5,pointerId:7,pointerType:'touch',isPrimary:true};
      c.dispatchEvent(new PointerEvent('pointerdown',o)); c.dispatchEvent(new PointerEvent('pointerup',o)); await sleep(100); const viaPointer=disp();
      document.getElementById('evPopupBg').style.display='none'; await sleep(800); c.click(); await sleep(100); const viaClick=disp(); return {viaPointer,viaClick}}""")
    check('妨害レーンのマークは、指を離した時（pointerup）でも、click でも、説明が開く',r['viaPointer']=='flex' and r['viaClick']=='flex',r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={};
      // 敵の全滅カード
      hand=[]; applyEnemyEvent('wipe'); o.wipeCard=hand.some(c=>c.type==='curse_wipe');
      // 全滅の使用：旗1にカードを置いて使う
      flags.forEach(f=>{f.cards=[];f.closed=false}); flags[1].cards=[{kind:'troop',color:'red',value:5,uid:uid()},{kind:'troop',color:'red',value:6,uid:uid()}];
      const wi=hand.findIndex(c=>c.type==='curse_wipe'); useCurse(wi); o.pickMode=pending&&pending.wipe===true; flags.forEach((f,i)=>{}); tapFlag(1); await sleep(300); o.wiped=flags[1].cards.length===0; busy=false; pending=null;
      // 聖水：手札の呪いを消す
      hand=[]; applyEnemyEvent('wipe'); applyEnemyEvent('null'); const holy=Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='holy'),{uid:uid()}); hand.push(holy);
      useHoly(hand.findIndex(c=>c.type==='holy')); o.holyPend=pending&&pending.type==='holy'; const ni=hand.findIndex(c=>c.type==='curse_null'); tapHand(ni); await sleep(300);
      o.nullGone=!hand.some(c=>c.type==='curse_null'); o.wipeStay=hand.some(c=>c.type==='curse_wipe'); busy=false; pending=null;
      // 聖水：旗の敵装備・ボムを消す
      flags.forEach(f=>{f.cards=[];f.closed=false;f.bomb=0}); flags[2].cards=[makeMinusEq()]; flags[2].bomb=3;
      hand=[Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='holy'),{uid:uid()})]; useHoly(0); tapFlag(2); await sleep(300);
      o.flagClean=!flags[2].cards.some(isEnemyEq)&&!flags[2].bomb; busy=false; pending=null;
      // 聖水は呪いが無ければ使えない
      flags.forEach(f=>{f.cards=[];f.bomb=0;f.lockedUntil=0}); haunt={}; hand=[Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='holy'),{uid:uid()})]; useHoly(0); o.noTarget=!pending;
      o.noWipeTactic=!TACTICS.some(t=>t.type==='wipe');
      return o}""")
    check('全滅：敵の妨害カードになり、使うと旗のカードが消える',r['wipeCard'] and r['wiped'],r)
    check('聖水：手札の呪いを選んで消せる（他の呪いは残る）',r['holyPend'] and r['nullGone'] and r['wipeStay'],r)
    check('聖水：旗の敵の装備・ボムを消せる／呪いが無ければ使えない／全滅は軍師カードから消えた',r['flagClean'] and r['noTarget'] and r['noWipeTactic'],r)
    r=ev("""()=>{ const sim=(lo,hi)=>{ const o={soft:0,big:0,n:0}; WAVES.filter(w=>!w.boss&&w.lv>=lo&&w.lv<=hi).forEach(w=>{ stageIndex=WAVES.indexOf(w); for(let k=0;k<40;k++){ const s=genSchedule(); Object.values(s).forEach(e=>{ if(e==='rage') return; o.n++; if(SOFT_DIS.includes(e)) o.soft++; else o.big++; }); } }); return o}; return {mid:sim(20,40),hi:sim(50,72)} }""")
    print('妨害の内訳 (soft=カード/場荒らし, big=大きい不可逆)',r)
    check('妨害の出る割合：カード・場荒らし系が半数以上',r['mid']['soft']>r['mid']['big'] and r['hi']['soft']>=r['hi']['big']*0.8,r)
    r=ev("""async()=>{ const i=WAVES.findIndex(w=>w.baseId==='ジャックランタン'); CHARACTER=makeMonChar(i,'ジャックランタン'); init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), rnd=Math.random, o={max:specMax('mon')}; Math.random=()=>0.1; specUse('mon'); await sleep(100); document.getElementById('confirmYes').click(); await sleep(600); o.win=bossHp===0; o.again=specRemain('mon'); Math.random=rnd;
      CHARACTER=makeMonChar(i,'ジャックランタン'); init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      Math.random=()=>0.9; specUse('mon'); await sleep(100); document.getElementById('confirmYes').click(); await sleep(1500); o.lose=gameEnded&&playerHp===0; Math.random=rnd; return o}""")
    check('ジャックランタン：トリックオアトリートは1戦1回・1/2で敵が死に1/2で自分が死ぬ',r['max']==1 and r['win'] and r['again']==0 and r['lose'],r)
    r=ev("""async()=>{ const i=WAVES.findIndex(w=>w.baseId==='何匹かのスライム'); CHARACTER=makeMonChar(i,'何匹かのスライム'); init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const o={kind:CHARACTER.monSkill&&CHARACTER.monSkill.kind, name:CHARACTER.monSkill&&CHARACTER.monSkill.name}; flags.forEach(f=>{f.cards=[];f.closed=false}); const tc={kind:'troop',color:'red',value:5,uid:uid()}; flags[0].cards.push(tc); hand=[]; const t0=turnCounter; specUse('mon'); o.pend=!!(pending&&pending.skillCard); resolveGuidance(0); await new Promise(r=>setTimeout(r,300));
      o.back=hand.some(c=>c.uid===tc.uid); o.turn=turnCounter-t0; o.grave=graveyard.some(c=>c.type==='guidance'&&c.temp); o.uses=spec.mon; return o}""")
    check('スライム：溶かす（ボタンで撤収が発動・ターン消費なし・墓地へ）',r['kind']=='melt' and r['name']=='溶かす' and r['pend'] and r['back'] and r['turn']==0 and r['grave'] and r['uses']==1,r)
    r=ev("""async()=>{ const a=WAVES.findIndex(w=>dispName(w.baseId)==='蚊'); CHARACTER=makeMonChar(a,WAVES[a].baseId); init(); document.getElementById('titleScreen').style.display='none'; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null;
      flags.forEach(x=>{x.cards=[];x.closed=false}); flags[0].cards.push(makePanicField()); const o={}; specUse('mon'); o.pend=pending&&pending.type; tapFlag(0); await new Promise(r=>setTimeout(r,200));
      const c=flags[0].cards.find(c=>c.kind==='troop'); o.val=c&&c.value; o.pf=flags[0].cards.some(c=>c.sub==='pfield'); return o}""")
    check('蚊の一刺し：パニックフィールドの旗では1が10になり、フィールドは1回で消える',r['pend']=='skillplace' and r['val']==10 and not r['pf'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; flags.forEach(x=>{x.cards=[];x.closed=false});
      const m={kind:'monster',sub:'number',value:5,uid:uid(),accumulatedBonus:0,pf:true}; flags[2].cards=[m]; const c={kind:'troop',color:'red',value:3,uid:uid()}; hand=[c]; const o={before:targetsFor(c).includes(2)};
      playOnFlag(0,2,null,true); await new Promise(r=>setTimeout(r,300)); o.val=c.value; o.pf=!!m.pf; return o}""")
    check('パニックフィールドは1回逆転したら効果が消える（装備に乗った場合）',r['before'] and r['val']==8 and not r['pf'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; flags.forEach(x=>{x.cards=[];x.closed=false});
      const t7={kind:'troop',color:'purple',value:7,uid:uid()}; flags[1].cards=[t7,makePanicField()]; const mk={kind:'monster',sub:'mark',color:'red',uid:uid()}; hand=[mk]; const o={ok:targetsFor(mk).includes(1)};
      playOnFlag(0,1,null,true); await new Promise(r=>setTimeout(r,400)); o.col=t7.color; o.pf=flags[1].cards.some(c=>c.sub==='pfield'); return o}""")
    check('パニックフィールドの旗にも色の装備が置けて、奥のカードのマークが変わる',r['ok'] and r['col']=='red' and r['pf'],r)
    r=ev("""async()=>{ const a=WAVES.findIndex(w=>dispName(w.baseId)==='蚊'); CHARACTER=makeMonChar(a,WAVES[a].baseId); init(); document.getElementById('titleScreen').style.display='none'; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; const o={};
      for(const [k,nm] of [['sting','蚊'],['fang','洞窟のヘビ']]){ const ai=WAVES.findIndex(w=>dispName(w.baseId)===nm); CHARACTER=makeMonChar(ai,WAVES[ai].baseId); init(); document.getElementById('titleScreen').style.display='none'; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null; flags.forEach(x=>{x.cards=[];x.closed=false}); dis.poisonUntil=turnCounter+5; spec.mon=0; specUse('mon'); tapFlag(0); await new Promise(r=>setTimeout(r,150)); const c=flags[0].cards.find(c=>c.kind==='troop'); o[k]=c&&c.value; pending=null; }
      dis.poisonUntil=0; return o}""")
    check('蚊・毒の牙：毒の呪い中は数字−1（1は1のまま）',r['sting']==1 and r['fang']==5,r)
    r=ev("""async()=>{ const a=WAVES.findIndex(w=>dispName(w.baseId)==='トロル'), b=WAVES.findIndex(w=>w.baseId==='何匹かのスライム'); const f=fuseChar(makeMonChar(a,WAVES[a].baseId),'何匹かのスライム'); CHARACTER=f; lsSet(FUSE_KEY,'1'); init(); lsSet(FUSE_KEY,''); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; pending=null;
      const o={sp:f.sp.join(','),a:f.monSkill&&f.monSkill.name,b:f.monSkillB&&f.monSkillB.name,slots:ACC_SLOTS,spr:!!SPR[fuseSprKey(monSprKey(WAVES[a]),monSprKey(WAVES[b]))],btn2:document.getElementById('specMon2').style.display};
      flags.forEach(x=>{x.cards=[];x.closed=false}); const tc={kind:'troop',color:'red',value:5,uid:uid()}; flags[0].cards.push(tc); hand=[];
      specUse('mon2'); o.pend=!!(pending&&pending.skillCard); resolveGuidance(0); await new Promise(r=>setTimeout(r,300)); render();
      o.back=hand.some(c=>c.uid===tc.uid); o.u2=spec.mon2; o.u1=spec.mon; o.skillBack=CHARACTER.monSkill.name; return o}""")
    check('合体：トロル＋スライム（特殊技2体分・枠は3つのまま・2つ目の技が使える・1つ目の枠は消費しない）',r['sp']=='mon,mon2' and r['a']=='大巨漢' and r['b']=='溶かす' and r['slots']==3 and r['spr'] and r['btn2']!='none' and r['pend'] and r['back'] and r['u2']==1 and r['u1']==0 and r['skillBack']=='大巨漢',r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); enemySched={5:'rage'}; slowWins=[]; const a=enemyAtkAt(5), a4=enemyAtkAt(4); slowWins=[[0,10]]; const b=enemyAtkAt(5), b4=enemyAtkAt(4); const base=a4/enemyAtkAt(4); return {rageFull:a/a4, rageSlow:(b/ (b4+ (enemyAtkAt(5)-enemyAtkAt(5))))} }""")
    check('殴る：効果中は攻撃力×2も×1.5に抑える',abs(r['rageFull']-2)<0.5 and r['rageSlow']<r['rageFull'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const o={}; flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0}); applyEnemyEvent('assassin'); o.none=true;
      flags[1].cards=[{kind:'troop',color:'red',value:9,uid:uid()},{kind:'troop',color:'red',value:8,uid:uid()},{kind:'troop',color:'red',value:7,uid:uid()}]; const g0=graveyard.length;
      applyEnemyEvent('assassin'); o.left=flags[1].cards.length; o.grave=graveyard.length-g0; o.banner=document.getElementById('evBanner').classList.contains('dis')&&document.getElementById('evBanner').textContent.includes('妨害');
      const w=WAVES.find(x=>!x.boss&&x.lv>=30); o.inList=disList(w).includes('assassin'); const lo=WAVES.find(x=>!x.boss&&x.lv===25); o.early=lo?disList(lo).includes('assassin'):true;
      return o}""")
    check('暗殺：旗のカードが1枚ランダムに墓地へ／妨害の発動を大きな帯で知らせる／中盤以降の敵が出す',r['left']==2 and r['grave']==1 and r['banner'] and r['inList'] and r['early'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={}; hand[0]=Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='scout'),{uid:uid()}); render();
      const h0=hand.map(c=>c.uid).join(), d0=activeDeck.map(c=>c.uid).join(), t0=turnCounter, g0=graveyard.length;
      useScout(0); await sleep(700); o.pend=pending&&pending.type==='discard'&&pending.scout; o.handUp=hand.length; o.turnHeld=turnCounter===t0; o.btn=document.getElementById('cancelPendingBtn').style.display!=='none';
      cancelPending(); await sleep(200); o.restored=hand.map(c=>c.uid).join()===h0 && activeDeck.map(c=>c.uid).join()===d0 && turnCounter===t0 && graveyard.length===g0 && !pending;
      useScout(0); await sleep(700); discardTap(1); discardTap(2); confirmDiscard(); await sleep(700); o.dd=[!!pending,turnCounter,t0,graveyard.length,g0,hand.length,h0.split(',').length]; o.done=!pending && turnCounter===t0+1 && graveyard.length===g0+3 && hand.length===h0.split(',').length;
      return o}""")
    check('補充：捨てるカードを選んでいる間はキャンセルでき（手札・山札・ターンが元に戻る）、確定でターンが進む',r['pend'] and r['turnHeld'] and r['btn'] and r['restored'] and r['done'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false; stageIndex=WAVES.findIndex(w=>w.lv===30); introOn=false; startBattleGoals();
      document.getElementById('cardListModal').style.display='flex'; document.getElementById('specModal').style.display='flex';
      grantStageReward(); await new Promise(r=>setTimeout(r,300));
      return {list:document.getElementById('cardListModal').style.display, spec:document.getElementById('specModal').style.display, chest:document.getElementById('chestModal').style.display}}""")
    check('戦いが終わったら、開きっぱなしのポップアップ（一覧・特殊技など）が閉じて宝箱だけが出る',r['list']=='none' and r['spec']=='none' and r['chest']=='flex',r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;inPrep=false; stageIndex=WAVES.findIndex(w=>w.lv===30); introOn=false;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={}; startBattleGoals(); await sleep(300); o.cond=!document.getElementById('condModal');
      renderBattle(); o.before=document.querySelectorAll('.modal-bg[style*="10003"]').length; const aid=accSeq++; accOwned.push({aid,id:'sp_double'}); accEq.push(aid); renderBattle(); o.alert=document.querySelectorAll('.modal-bg[style*="10003"]').length; o.txt=(document.querySelector('.modal-bg[style*="10003"]')||{}).innerText||'';
      return o}""")
    check('戦闘の最初に条件の一覧ポップアップは出ない／戦闘中に特殊技の回数の上限が上がるとアラートが出る',r['cond'] and r['before']==0 and r['alert']==1 and '回' in r['txt'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); const aid=accSeq++; accOwned.push({aid,id:'quick_boots'}); accEq.push(aid); const o={ok:quickMult(10,false), no:quickMult(10,true), t15:quickMult(15,false), t15n:quickMult(14,true), late:quickMult(16,false)}; return o}""")
    check('早撃ちブーツ：12ターン以内は役あり×5・役なし混じり×2／15ターン以内は×1.5・×1.1／16ターン以降は等倍',r['ok']==5 and r['no']==2 and r['t15']==1.5 and abs(r['t15n']-1.1)<1e-9 and r['late']==1,r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0}); applyEnemyEvent('autonum'); await new Promise(r=>setTimeout(r,200));
      const el=document.querySelector('.pcard.auto-enemy'); const c=flags.flatMap(f=>f.cards).find(c=>c.autoPlaced);
      return {has:!!el, fresh:!!document.querySelector('.pcard.auto-new'), flag:!!c, normal:c&&c.kind==='troop'&&c.temp}}""")
    check('敵が置いた数字カードに赤い枠と「敵」の印が付き、置いた直後は光る（中身は普通の数字カード）',r['has'] and r['fresh'] and r['flag'] and r['normal'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; await new Promise(r=>setTimeout(r,900)); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;inPrep=false;
      flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0}); enemyTurn=5; enemySched={8:'autonum'}; autoQ={}; autoSeq=0; render();
      const o={}; const fc=autoForecast(); const fi=+Object.keys(fc)[0]; o.k=fc[fi]&&fc[fi][0].k; o.badge=!!document.querySelector('.flag[data-index="'+fi+'"] .auto-fc'); 
      // 予定の旗が埋まったら、別の旗へ移る（移った先に表示される）
      flags[fi].cards=[{kind:'troop',color:'red',value:3,uid:uid()},{kind:'troop',color:'red',value:4,uid:uid()},{kind:'troop',color:'red',value:5,uid:uid()}]; render(); const fc2=autoForecast(); const fi2=+Object.keys(fc2)[0]; o.moved=fi2!==fi && !!document.querySelector('.flag[data-index="'+fi2+'"] .auto-fc');
      // 命乞いで3ターン遅れると予定も一緒にずれる
      hand[0]=Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='plead'),{uid:uid()}); usePlead(0); await new Promise(r=>setTimeout(r,500)); o.shift=(autoQ.autonum||[]).length===1; o.k2=(Object.values(autoForecast())[0]||[{}])[0].k;
      // 発動すると予定どおりのカードが予定の旗に置かれる
      const want={...autoQ.autonum[0]}, tgt=autoTargetIdx(autoQ.autonum[0]); enemyTurn=11; applyEnemyEvent('autonum'); const c=flags[tgt].cards.find(c=>c.autoPlaced); o.fire=!!c&&c.color===want.col&&c.value===want.v; o.cleared=(autoQ.autonum||[]).length===0;
      return o}""")
    check('敵の数字カード：旗の右上に「あとNターン・色と数字」が出る／旗が埋まると別の旗へ移る／命乞いで一緒にずれる／予定どおりに置かれる',r['k']==3 and r['badge'] and r['moved'] and r['shift'] and r['fire'] and r['cleared'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; await new Promise(r=>setTimeout(r,900)); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;inPrep=false;
      const o={}, mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()});
      for(const ev of ['minus','ghost','deatheater','assassin']){
        flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0;f.bomb=0}); haunt={}; flags[1].cards=[mk('red',3),mk('red',4)]; enemyTurn=5; enemySched={8:ev}; autoQ={}; render();
        const fc=autoForecast(), fi=+Object.keys(fc)[0]; const has=!!document.querySelector('.flag[data-index="'+fi+'"] .auto-fc'); const tgt=autoTargetIdx(autoQ[ev][0]);
        enemyTurn=8; const before=flags.map(f=>f.cards.length).join(); applyEnemyEvent(ev); const after=flags.map(f=>f.cards.length).join();
        o[ev]={has, fi, tgt, changed: ev==='ghost'?(haunt[tgt]>0):ev==='deatheater'?(flags[tgt].eater>enemyTurn):(before!==after), onTgt: ev==='ghost'||ev==='deatheater'?true:flags[tgt].cards.length!==(+before.split(',')[tgt])};
      }
      return o}""")
    ok=all(r[k]['has'] and r[k]['fi']==r[k]['tgt'] and r[k]['changed'] and r[k]['onTgt'] for k in ['minus','ghost','deatheater','assassin'])
    check('旗を狙う妨害（マイナスの武器・ワームホール・デスイーター・暗殺）：旗の右上に予定が出て、予定の旗に発動する',ok,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); introOn=false; busy=false;pending=null;gameEnded=false;inPrep=false; const o={}, mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()});
      const setup=()=>{ flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0;f.eater=0}); flags[1].cards=[mk('red',3),mk('red',4)]; enemyTurn=5; autoQ={}; };
      // 発動：旗に居座る（まだ食べない）
      setup(); enemySched={8:'deatheater'}; autoForecast(); enemyTurn=8; const t=autoTargetIdx(autoQ.deatheater[0]); applyEnemyEvent('deatheater'); o.sit=flags[t].eater===8+EATER_TURNS&&flags[t].cards.length===2; o.badge=(render(),!!document.querySelector('.flag[data-index="'+t+'"]')&&document.body.innerText.includes('デスイーター あと3'));
      // 置いたカードが食べられる
      const f=flags[t]; hand=[mk('blue',9)]; const g0=graveyard.length; f.cards.push(hand[0]); const ok=eaterEatPlaced(f,f.cards[2],null,-1); o.eatPlaced=ok&&f.cards.length===2&&graveyard.length===g0+1&&!f.eater;
      // 3ターン置かなければ、1枚目が食べられる
      setup(); enemySched={}; flags[1].eater=enemyTurn+3; const first=flags[1].cards[0]; enemyTurn+=2; eaterExpire(); o.early=flags[1].cards.length===2; enemyTurn+=1; eaterExpire(); o.expire=flags[1].cards.length===1&&flags[1].cards[0]!==first&&!flags[1].eater;
      return o}""")
    check('デスイーター：旗に居座り（あとNターン表示）、置いたカードを食べる／3ターン置かなければ1枚目を食べる',r['sit'] and r['badge'] and r['eatPlaced'] and r['early'] and r['expire'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; await new Promise(r=>setTimeout(r,900)); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); inPrep=false; openAccModal(); await new Promise(r=>setTimeout(r,300));
      const b=document.querySelector('#accModal .reward-box').getBoundingClientRect(), u=document.getElementById('accUpper').getBoundingClientRect(); document.getElementById('accModal').style.display='none'; return {bh:b.height,uh:u.height}}""")
    check('戦闘中にアクセサリー画面（🎒）を開いても、中身が見える（空の枠にならない）',r['bh']>300 and r['uh']>200,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); let bad=0, n=0; WAVES.forEach((w,i)=>{ stageIndex=i; for(let k=0;k<12;k++){ autoSeq=k; const pl=newAutoPlan('autonum'); n++; if(pl.col==='orange'||!GAME_COLORS.includes(pl.col)) bad++; } }); for(let k=0;k<200;k++){ if(makeColorField().color==='orange') bad++; } return {bad,n}}""")
    check('敵が置く数字カード・カラフルフィールドに、今のゲームには無いオレンジが使われない',r['bad']==0,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); flags.forEach(f=>{f.cards=[];f.closed=false}); enemyTurn=5; enemySched={8:'autonum',12:'autonum'}; autoQ={}; autoSeq=0; render();
      const sig=()=>{ const a=autoForecast(); const q=autoQ.autonum[0]; return JSON.stringify([q.col,q.v,q.flag]); };
      const c1=sig();
      enemyTurn=0; enemySched={3:'autonum',9:'autonum'}; render(); const c2=sig();
      const saved=JSON.stringify(autoQ); autoQ={}; autoQ=JSON.parse(saved); const c3=sig();
      return {c1,c2,c3}}""")
    check('敵の数字カードの予定は、リセット（ラウンドの組み直し）やセーブ・ロードをまたいでも固定',r['c1']==r['c2']==r['c3'] if False else (r['c1']==r['c2'] and r['c2']==r['c3']),r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); flags.forEach(f=>{f.cards=[];f.closed=false}); enemyTurn=5; enemySched={8:'pfield'}; autoQ={}; autoSeq=0; render();
      const a=autoForecast(), fi=+Object.keys(a)[0], hand0=hand.length; enemyTurn=7; applyEnemyEvent('pfield');
      const on=flags.map((f,i)=>flagMonster(f)&&flagMonster(f).sub==='pfield'?i:-1).filter(i=>i>=0);
      return {fi,on,handSame:hand.length===hand0}}""")
    check('パニックフィールドは手札ではなく、予告した旗に直接置かれる',r['on']==[r['fi']] and r['handSame'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); flags.forEach(f=>{f.cards=[];f.closed=false}); enemyTurn=0; enemySched={8:'minus'}; autoQ={}; render();
      const pl=autoQ.minus&&autoQ.minus[0]; const cell=[...document.querySelectorAll('#upcomingRow2 .fc[data-ev="minus"]')][0];
      return {v:pl&&pl.v, txt:cell?cell.textContent:null}}""")
    check('妨害レーンのマイナスの武器に、数字（予定の値）が出る',r['txt'] is not None and str(r['v']) in r['txt'],r)
    JS_ENC="""(mode)=>{ CHARACTER=CHARACTERS[2]; init(); lsSet('soloSiegeAlienBeat','[]'); lsSet('soloSiegeAlienMet','[]');
      stageIndex=WAVES.findIndex(w=>w.lv===20); battleNo=2; alienEnc=null; playerHp=0; gameEnded=true;
      showEnd('hpzero'); const o={appear:!!document.getElementById('alienGo')};
      document.getElementById('alienGo').onclick(); o.enc=alienEnc&&alienEnc.id; o.stage=WAVES[stageIndex].id; o.alive=playerHp>0&&!gameEnded; o.cards=flags.length>0&&hand.length>0;
      if(mode==='lose'){ playerHp=0; playerLost(0); } else { bossHp=0; finishWaveOutcome(true,WAVES[stageIndex]); }
      return new Promise(res=>setTimeout(()=>{ o.surg=!!document.getElementById('alienOk'); if(o.surg) document.getElementById('alienOk').onclick();
        o.beat=alienBeatList().includes('月の民'); o.unres=!comboRestricted(); o.encCleared=alienEnc===null; o.ended=gameEnded; res(o); },1300)); }"""
    for mode in ('lose','win'):
        r=pg.evaluate(JS_ENC,mode)
        check('負けた後に宇宙人が現れて戦い、'+('負け' if mode=='lose' else '勝ち')+'でも手術を受けて強化される（月の民：コンボ制限解除）',
              r['appear'] and r['enc']=='月の民' and r['stage']=='月の民' and r['alive'] and r['cards'] and r['surg'] and r['beat'] and r['unres'] and r['encCleared'] and r['ended'],r)
    r=ev("""()=>{ lsSet('soloSiegeAlienBeat','[]'); lsSet('soloSiegeAlienMet','[]'); stageIndex=WAVES.findIndex(w=>w.lv>=26&&!w.boss); const a=alienEncounterId(); alienMetAdd(a); const b=alienEncounterId(); lsSet('soloSiegeAlienMet','[]'); return {a,b} }""")
    check('宇宙人：一度戦ったら（勝っても負けても）もう現れない',r['a'] and r['b']!=r['a'],r)
    pg.evaluate("localStorage.setItem('soloSiegeAlienBeat',JSON.stringify(['月の民']))")
    r=pg.evaluate("""()=>{ unlockMon('ミジンコキング'); ['月の民','火星人','水星人','金星人','太陽神'].forEach(unlockMon); buildCharList(); const g=document.getElementById('monGrid');
      const t=[...g.querySelectorAll('.mon-tile')].map(e=>({n:e.querySelector('b').textContent.replace(/\\s/g,''),a:e.classList.contains('alien')}));
      const ix=n=>t.findIndex(x=>x.n===n); return {n:t.length,aliens:t.filter(x=>x.a).map(x=>x.n),moonAfterSpider:ix('月の民')>ix('大グモ')&&ix('月の民')<ix('コボルト'),marsBetween:ix('火星人')>ix('モンク')&&ix('火星人')<ix('侍'),lastNotAlien:!t[t.length-1].a||t[t.length-1].n==='太陽神'} }""")
    check('モンスター一覧：宇宙人は強さの位置に並び（下に固まらない）、背景色で見分けられる',len(r['aliens'])>=5 and r['moonAfterSpider'] and r['marsBetween'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); flags.forEach(f=>{f.cards=[];f.closed=false;f.blindUntil=0}); enemyTurn=5; enemySched={8:'blind'}; autoQ={}; autoSeq=0; render();
      const a=autoForecast(), fi=+Object.keys(a)[0]; enemyTurn=7; applyEnemyEvent('blind'); const o={fi,on:flags.map(f=>blindOn(f)),smoke:document.querySelectorAll('.smoke').length};
      // 煙の間は、他の妨害の対象から外れる
      o.cand=evCands('autonum').map(c=>c.i).includes(fi); o.candMinus=evCands('assassin').map(c=>c.i).includes(fi);
      enemyTurn=7+DIS_PARAM.blindTurns; o.after=blindOn(flags[fi]);
      // コウモリの特殊技：旗をタップして煙で覆う
      enemyTurn=2; flags.forEach(f=>{f.blindUntil=0}); CHARACTER=makeMonChar(WAVES.findIndex(w=>w.baseId==='コウモリの群れ'));
      o.skill=CHARACTER.monSkill&&CHARACTER.monSkill.kind; monSkillUse(); o.pend=pending&&pending.type; tapFlag(1); o.skillOn=flags.map(f=>blindOn(f));
      const bat=WAVES.find(w=>w.name==='コウモリ'); o.batDis=disList(bat).slice(0,3);
      return o}""")
    check('ブラインド：敵の予告→旗が煙に覆われ、煙の間は他の妨害の対象外／コウモリの特殊技で好きな旗を覆える',
          r['on'][r['fi']] and r['on'].count(True)==1 and r['smoke']==1 and not r['cand'] and not r['candMinus'] and not r['after'] and r['skill']=='blind' and r['pend']=='blindpick' and r['skillOn']==[False,True,False,False][:len(r['skillOn'])] and r['batDis'][0]=='blind',r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); flags.forEach(f=>{f.cards=[];f.closed=false}); busy=false; pending=null;
      const c={kind:'troop',color:'red',value:7,uid:uid()}; flags[0].cards.push(c); const g={kind:'tactic',type:'guidance',name:'撤収',uid:uid()}; hand.push(g);
      const n0=hand.length; useGuidance(hand.findIndex(x=>x.uid===g.uid)); const p1=pending&&pending.type; tapFlag(0);
      return {p1,inHand:hand.some(x=>x.uid===c.uid),flagLeft:flags[0].cards.length,usedGone:!hand.some(x=>x.uid===g.uid),pend:pending}}""")
    check('撤収：旗のカードが手札に戻り、撤収カードは使われる',r['p1']=='guidance' and r['inHand'] and r['flagLeft']==0 and r['usedGone'] and r['pend'] is None,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); const o={}; busy=false; pending=null; gameEnded=false;
      // 毒：5ターン、毎ターン2ダメージ
      playerHp=100; playerHpMax=100; applyEnemyEvent('poison'); const ci=hand.findIndex(c=>c.type==='curse_poison'); o.gotCard=ci>=0; if(ci>=0){ doCurse(ci,0); busy=false; } const hp0=playerHp; advanceTurn(null); advanceTurn(null); o.venom=hp0-playerHp; o.venomOn=turnCounter<=dis.venomUntil;
      for(let k=0;k<6;k++) advanceTurn(null); o.venomEnd=(hp0-playerHp);
      // 暗闇は妨害に出ない
      o.noDark=!WAVES.some(w=>disList(w).includes('dark'));
      // 物理攻撃：当たれば70、外れれば0
      playerHp=100; const rnd=Math.random; Math.random=()=>0.1; applyEnemyEvent('punch'); o.hit=100-playerHp; playerHp=100; Math.random=()=>0.9; applyEnemyEvent('punch'); o.miss=100-playerHp; Math.random=rnd;
      const w=WAVES.find(x=>x.baseId==='巨大ムカデ'); o.name=w.name; o.dis=disList(w).slice(0,1); o.spr=monSprKey(w);
      // 行動封じ：次の妨害を無効にする
      { const keepC=CHARACTER, wj=WAVES.find(x=>x.baseId==='巨大ムカデ'); CHARACTER=makeMonChar(WAVES.indexOf(wj)); init(); busy=false; pending=null; enemyTurn=2; enemySched={5:'rage',6:'half',10:'minus'}; const smon=spec.mon;
        Math.random=()=>0.9; monSkillUse(); o.jamNg=enemySched[6]==='half'&&spec.mon===smon+1;   // 外れ：消えない・もう一度使える
        Math.random=()=>0.1; monSkillUse(); o.jamOk=enemySched[6]===undefined&&enemySched[10]==='minus'&&enemySched[5]==='rage'&&spec.mon===smon+2; Math.random=rnd; CHARACTER=keepC; }
      // 名前・特殊技・絵
      const ma=makeMonChar(WAVES.indexOf(w)); o.jamKind=ma.monSkill&&ma.monSkill.kind;
      const mb=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); o.bashKind=mb.monSkill&&mb.monSkill.kind; o.bandit=WAVES.find(x=>x.baseId==='野盗の一団').name;
      return o}""")
    check('毒は毎ターン2ダメージ／暗闇は出ない／野盗の物理攻撃・アサシンの行動封じ',
          r['gotCard'] and r['venom']==4 and r['venomOn'] and r['venomEnd']==10 and r['noDark'] and r['hit']==70 and r['miss']==0 and r['jamOk'] and r['jamNg'] and r['name']=='アサシン' and r['dis']==['assassin'] and r['spr']=='assassin' and r['jamKind']=='jam' and r['bashKind']=='bash',r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; const o={}; const rnd=Math.random; bossHp=1e9; hand=[0,1,2,3].map(()=>({kind:'troop',color:'red',value:3,uid:uid()})); Math.random=()=>0.9; monSkillUse(); o.missDmg=bashDmg; o.rate=bashRateNow; o.d0=bossHp; advanceTurn(null); advanceTurn(null); o.rate2=bashRateNow; resetBattleRound(); o.rate3=bashRateNow; Math.random=()=>0.1; monSkillUse(); o.hitDmg=bashDmg; o.dealt=1e9-bossHp; Math.random=rnd; return o}""")
    check('バイキングの斧で攻撃：外れてもダメージは変わらない・命中率は1ターンごとに5％下がり新waveで70％に戻る／当たると200ダメージで次は手札の数字カード数×0.3倍',r['missDmg']==200 and abs(r['rate']-0.7)<1e-9 and abs(r['rate2']-0.6)<1e-9 and abs(r['rate3']-0.7)<1e-9 and r['dealt']==200 and r['hitDmg']==240,r)
    r=ev("""()=>{ const w=WAVES.find(x=>x.name==='沼のリザードマン'); const dl=disList(w), wt=disWeights(w,dl), tot=Object.values(wt).reduce((a,b)=>a+b,0);
      CHARACTER=makeMonChar(WAVES.indexOf(w)); init(); flags.forEach(f=>{f.cards=[];f.closed=false}); busy=false; pending=null; const o={share:wt.pfield/tot, first:dl[0], kind:CHARACTER.monSkill&&CHARACTER.monSkill.kind};
      monSkillUse(); o.pend=pending&&pending.type; tapFlag(2); o.placed=flags.map(f=>!!(flagMonster(f)&&flagMonster(f).sub==='pfield')); o.pendEnd=pending;
      return o}""")
    check('沼のリザードマン：パニックフィールドが妨害の約半分以上／特殊技で好きな旗にパニックフィールドを置ける',r['share']>=0.5 and r['first']=='pfield' and r['kind']=='pfsk' and r['pend']=='pfpick' and r['placed']==[False,False,True,False][:len(r['placed'])] and r['pendEnd'] is None,r)
    r=ev("""()=>{ const o={}; const first=w=>{ stageIndex=WAVES.indexOf(w); const sc=genSchedule(); const ks=Object.keys(sc).map(Number).filter(t=>isDisEv(sc[t])).sort((a,b)=>a-b); return ks[0]; };
      const ns=WAVES.filter(w=>!w.boss&&disList(w).length);
      o.early=ns.filter(w=>w.lv<DIS_PARAM.earlyLv).map(w=>[w.name,first(w)]); o.late=ns.filter(w=>w.lv>=DIS_PARAM.earlyLv&&w.lv<DIS_PARAM.softLv).map(w=>[w.name,first(w)]);
      const st=document.createElement('style'); st.textContent='*{animation:none!important}'; document.head.appendChild(st);
      const d=document.createElement('div'); d.innerHTML=spriteSVG('slime',50,'',true); document.body.appendChild(d); o.frA=getComputedStyle(d.querySelector('.frA')).visibility; d.remove(); st.remove(); return o}""")
    check('序盤（earlyLv未満）の敵は最初の妨害が10ターン目以降',all((f or 99)>=10 for n,f in r['early']),r['early'])
    check('earlyLv以降の敵は最初の妨害が6ターン目前後から出る',any((f or 99)<=7 for n,f in r['late']),r['late'][:6])
    check('動く敵の絵：アニメが止まっても基本の絵は見える（敵が消えない）',r['frA']=='visible',r['frA'])
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); gold=SWAP_PRICE*3; swapLeft=99; startSwap(); renderPicker(); const cards=document.querySelectorAll('#pickGrid .db-card'); for(let i=0;i<5;i++) cards[i].click(); const o={sel:pk.sel.length,count:pk.count}; pk=null; document.getElementById('pickModal').style.display='none'; return o}""")
    check('山札の入れ替え：払える枚数まで、画面で実際に複数選べる',r['count']==3 and r['sel']==3,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); gold=SWAP_PRICE*3; swapLeft=99; startSwap(); const its=pk.tabs[0].items; const n0=activeDeck.length+hand.length; const outs=its.slice(0,3); pk.sel=outs.slice(); const cnt=pk.count; pk.done(pk.sel); const o={cnt, gold, deckKept:outs.every(it=>!deckUids.has(it.c.uid)), srRows:document.querySelectorAll('#srList > div').length, n0, n1:activeDeck.length+hand.length}; document.getElementById('srOk').click(); return o}""")
    check('山札の入れ替え：複数まとめて選んで一気に入れ替わる（枚数は変わらない・お金は枚数分）',r['cnt']==3 and r['gold']==0 and r['deckKept'] and r['srRows']==3 and r['n0']==r['n1'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); busy=false; pending=null; enemyTurn=5; flags.forEach(f=>{f.cards=[];f.closed=false;f.blindUntil=0}); flags[1].blindUntil=enemyTurn+3; const o={cand:holyFlagCands().map(c=>c.i)}; hand=[{kind:'tactics',type:'holy',name:'聖水',uid:uid()}]; useHoly(0); resolveHolyFlag(1); o.after=blindOn(flags[1]); return o}""")
    check('聖水：ブラインドの煙も取り除ける',r['cand']==[1] and r['after']==False,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; hand=[{kind:'tactics',type:'defend',name:'防御',uid:uid()},...hand]; useDefend(0); const o={on:defendOn, sw:document.getElementById('plAtkSw').textContent, inDeck:[...new Set([...grandDeck,...activeDeck,...hand,...graveyard])].filter(c=>c.type==='defend').length-1}; return o}""")
    check('防御カード：使うと剣が盾になり、山札に2枚入っている',r['on']==True and r['sw']=='🛡' and r['inDeck']==2,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; defendOn=true; const hp=bossHp, php=playerHp; prevSnap=null; score=500; enemyTurn=3; const e=enemyAtkAt(3); checkWaveOutcome(); return {used:defendOn, bossSame:bossHp===hp, e, php, php2:playerHp}}""")
    check('防御カード：攻撃力が勝っていても敵のHPは減らず、使用後は解除される',r['used']==False and r['bossSame'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); const c={kind:'monster',sub:'number',value:6,uid:uid(),pf:true}; flags[0].cards=[c]; advanceWaveAttempt(); return {pf:!!c.pf}}""")
    check('パニックフィールドの🌀印は、攻撃が終わったら装備から消える（山札に残らない）',r['pf']==False,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); hpStock=3; plAtkMult=0.5; advanceToNextStage(); return {hs:hpStock, pm:plAtkMult}}""")
    check('細胞分裂のストック・攻撃力半分は、次の戦いに持ち越さない',r['hs']==(0 if True else 0) and r['pm']==1,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false}); autoQ={}; const pl=planAt('autonum',0); pl.flag=0; flags[0].cards=[{kind:'troop',color:'red',value:3,uid:uid()},{kind:'troop',color:'red',value:4,uid:uid()}]; const fi=autoTargetIdx(pl); return {fi}}""")
    check('敵の数字カードの予告：2枚目を置いても予告の旗は動かない',r['fi']==0,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); enemySched={}; slowWins=[]; const base=enemyAtkAt(10); const w=WAVES[stageIndex]; slowWins=[[0,10]]; const one=enemyAtkAt(10); slowWins=[[0,10],[0,10]]; const two=enemyAtkAt(10); const fk=FLAG_COUNT/BALANCE.flagCountAtkBase; return {base,one,two, okOne:Math.abs((one-w.atk*fk)/(base-w.atk*fk)-0.5)<0.02, okTwo:Math.abs((two-w.atk*fk)/(base-w.atk*fk)-0.25)<0.02, n:slowN(5)}}""")
    check('殴る：重ね掛けで敵の攻撃力の上昇が1/2→1/4になる',r['okOne'] and r['okTwo'] and r['n']==2,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); turnCounter=12; render(); const a=document.querySelector('.wt-meta').textContent; advanceWaveAttempt(); render(); return {a,b:document.querySelector('.wt-meta').textContent}}""")
    check('ターン表示：攻撃（wave）が終わるたびに0へ戻る',('ターン12' in r['a']) and ('ターン0/' in r['b']),r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); autoQ={}; const pl=planAt('cfield',0); const col=pl.col; const h0=hand.length; applyEnemyEvent('cfield'); const c=flags.map(flagMonster).find(x=>x&&x.sub==='cfield'); return {col, got:c&&c.color, inHand:hand.some(x=>x.sub==='cfield')}}""")
    check('カラフルフィールド：予測した色のまま、旗に直接置かれる',r['col']==r['got'] and not r['inHand'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); carryMap={red:30,blue:30}; const f=flags[0]; f.cards=[]; f.closed=false; f.cards.push(makeColorField('red')); busy=false; pending=null; hand=[{kind:'troop',color:'blue',value:4,uid:uid()}]; playOnFlag(0,0,null,true); return {red:carryMap.red,blue:carryMap.blue}}""")
    check('カラフルフィールドに逆らうと、その色のコンボだけ−5',r['red']==25 and r['blue']==30,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false});
      flags[0].cards=[makeColorField('blue')]; flags[1].cards=[makeColorField('red')];
      const w={kind:'monster',sub:'number',value:8,uid:uid()}, mk={kind:'monster',sub:'number',value:-3,uid:uid()}; hand.push(w,mk);
      const o={w0:targetsFor(w).includes(0), neg:targetsFor(mk).includes(0)}; playOnFlag(hand.indexOf(w),0,null,true);
      const m=flagMonster(flags[0]); o.sub=m&&m.sub; o.val=m&&m.value; o.col=m&&m.color;
      const ok=hand.find(c=>c.kind==='troop'); const lo={kind:'troop',color:'blue',value:3,uid:uid()}, hi={kind:'troop',color:'blue',value:9,uid:uid()}, wr={kind:'troop',color:'red',value:9,uid:uid()};
      o.lo=satisfiesMonster(lo,flags[0]); o.hi=satisfiesMonster(hi,flags[0]); o.wr=satisfiesMonster(wr,flags[0]); return o}""")
    check('カラフルフィールドの上に力の装備を重ねると「その色で、その数字以上」になる',r['w0'] and not r['neg'] and r['sub']=='combined' and r['val']==8 and r['col']=='blue' and not r['lo'] and r['hi'] and not r['wr'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); autoQ={}; busy=false; pending=null; carryMap={red:30}; hand=[{kind:'troop',color:'red',value:3,uid:uid()},{kind:'troop',color:'blue',value:4,uid:uid()}];
      const o={}; o.col=GAME_COLORS.filter(c=>!hand.some(h=>h.color===c)).includes(newAutoPlan('cfield').col);
      applyEnemyEvent('bomb'); const b=hand.find(c=>c.type==='curse_bomb'); o.fuse=b&&b.fuse; o.max=DIS_PARAM.bombFuse;
      for(let i=0;i<DIS_PARAM.bombFuse;i++) tickBombs(); o.gone=!hand.some(c=>c.type==='curse_bomb'); o.carry=carryMap.red; return o}""")
    check('ボム：手札に来た時点でカウント開始、置かずに持っていると爆発して消える／カラフルは手札に無い色',r['col'] and r['fuse']==r['max'] and r['gone'] and r['carry']==30-20,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); busy=false; pending=null; autoQ={}; const errs=[]; const t=enemyTurn+3; enemySched={}; enemySched[t]='cfield';
      try{ render(); }catch(e){ errs.push(String(e)); } const fc=autoForecast(); const txt=Object.values(fc).flat().filter(x=>x.type==='cfield').length;
      const lab=document.querySelector('.auto-fc')&&document.querySelector('.auto-fc').textContent; return {errs,txt,lab}}""")
    check('カラフルフィールドが予定にあっても、描画でエラーにならない',not r['errs'],r)
    r=ev("""async()=>{ try{ lsSet('soloSiegeMons',JSON.stringify(WAVES.filter(w=>!w.boss).map(w=>w.baseId))); }catch(e){} document.getElementById('appRoot').style.display='none'; document.getElementById('titleScreen').style.display='flex'; CHARACTER=null;
      document.getElementById('titleStartBtn').click(); const o={char:getComputedStyle(document.getElementById('charScreen')).display, noBtn:!document.getElementById('titleCharBtn')};
      document.getElementById('charDecide').click(); await new Promise(r=>setTimeout(r,1000)); o.title=getComputedStyle(document.getElementById('titleScreen')).display; o.app=getComputedStyle(document.getElementById('appRoot')).display; o.started=!!CHARACTER; return o}""")
    check('はじめる→必ずキャラ選択→決定でゲーム開始（タイトルへ戻らない／タイトルにキャラ選択ボタンなし）',r['char']=='flex' and r['noBtn'] and r['title']=='none' and r['app']!='none' and r['started'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='沼のリザードマン')); init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false});
      flags[0].cards=[{kind:'monster',sub:'number',value:8,uid:uid()}]; flags[1].cards=[{kind:'monster',sub:'number',value:-3,uid:uid(),enemyCard:true}];
      const o={c0:pfCands().includes(0), c1:pfCands().includes(1)}; monSkillUse(); o.pend=pending&&pending.type; tapFlag(0);
      const m=flagMonster(flags[0]); o.pf=!!(m&&m.pf); o.sub=m&&m.sub; o.cards=flags[0].cards.length;
      const lo={kind:'troop',color:'red',value:9,uid:uid()}, hi={kind:'troop',color:'red',value:2,uid:uid()};
      o.nine=satisfiesMonster(lo,flags[0]); o.two=satisfiesMonster(hi,flags[0]); return o}""")
    check('パニックフィールド：自分の装備の上にも置ける／逆転後の数字で置ける・置けないを判定（装備8：2→9は可、9→2は不可）',r['c0'] and not r['c1'] and r['pf'] and r['sub']=='number' and r['cards']==1 and r['two'] and not r['nine'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false});
      const mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()}); flags[3].cards=[mk('green',10),mk('blue',10)]; flags[3].cards.push(makePanicField());
      const o={}; const one=mk('red',1); const ring=hasAcc; hasAcc=id=>id==='yaku_only'; o.one=targetsFor(one).includes(3); o.two=targetsFor(mk('red',2)).includes(3); hasAcc=ring; return o}""")
    check('役のみの指輪＋パニックフィールド：逆転後の数字で役が成り立つ（10,10の旗に赤1＝10が置ける／赤2＝9は置けない）',r['one'] and not r['two'],r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0});
      const mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()}); const o={};
      flags[0].closed=true; o.closed=whyNotPlace(mk('red',3),0);
      flags[1].lockedUntil=turnCounter+3; o.lock=whyNotPlace(mk('red',3),1);
      flags[2].cards=[mk('red',1),mk('red',2),mk('red',3)]; o.full=whyNotPlace(mk('blue',3),2);
      flags[3].cards=[{kind:'monster',sub:'number',value:8,uid:uid()}]; o.low=whyNotPlace(mk('blue',3),3);
      hand=[mk('red',3)]; picked=0; render(); playOnFlag(0,0,null); o.alert=!!document.querySelector('.reward-title')&&[...document.querySelectorAll('.reward-title')].some(e=>e.textContent.includes('できません')); return o}""")
    check('置けない時は理由をアラートで出す（完成済み／封鎖／3枚／数字不足）',('完成' in r['closed']) and ('封鎖' in r['lock']) and ('3枚' in r['full']) and ('8以上' in r['low']) and r['alert'],r)
    r=ev("""()=>{ const o={}; CHARACTER=makeMonChar(WAVES.findIndex(x=>x.name==='侍')); init(); busy=false; gold=500; render(); o.coin=document.getElementById('specMonL').textContent; o.punch=document.getElementById('specPunch').textContent;
      CHARACTER=makeMonChar(WAVES.findIndex(x=>x.name==='ガーゴイル')); init(); busy=false; bossHp=3000; render(); o.fire=document.getElementById('specMonL').textContent; return o }""")
    check('特殊技のダメージを使う前に表示する（銭投げ＝所持金×100／ファイアブレス＝敵HPの3分の1／殴る）','💥50k' in r['coin'] and '💥' in r['punch'] and '💥1k' in r['fire'],r)
    r=ev("""()=>{ stageIndex=26; lastPower=90750; powerHist=[3095,5176,90750]; const spike=pickJump(77286); stageIndex=14; lastPower=3095; powerHist=[1561,3095]; const norm=pickJump(218); return {spike,norm} }""")
    check('飛び級：たまたまの最高の1撃（9万）では飛びすぎない（侍から小竜まで／78には行かない）。普通の勝ち方なら今まで通り飛ぶ',r['spike']<60 and r['spike']>r['norm']-1 and r['norm']>=15,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); const t=condPool().map(x=>x.g.text); return {col:t.filter(x=>/[赤青緑紫黄橙]旗/.test(x)), any:t.some(x=>/どれかの色でスーパーコンボ/.test(x))} }""")
    check('アクセサリー獲得条件：色を指定するスーパーコンボの条件は出ない（「どれかの色で」だけ）',not r['col'] and r['any'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='沼のリザードマン')); init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0});
      const mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()}); flags[0].cards=[mk('red',10),mk('red',10),{kind:'monster',sub:'number',value:5,uid:uid(),pf:true}];
      pending={type:'skillplace',card:{kind:'troop',color:'red',value:1,uid:uid(),temp:true},mk:'sting'}; tapFlag(0);
      return new Promise(res=>setTimeout(()=>{ const f=flags[0]; res({n:f.cards.length, mon:!!flagMonster(f), closed:f.closed, vals:f.cards.map(c=>c.value).join(',')}); },900))}""")
    check('蚊の一刺し：装備（5以上）の乗った旗でも、装備を置き換えて旗が完成する（赤1→10で赤10×3）',r['n']==3 and not r['mon'] and r['closed'] and r['vals']=='10,10,10',r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false});
      const mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()}); const eq={kind:'monster',sub:'number',value:5,uid:uid()};
      flags[0].cards=[mk('red',10),mk('blue',10),eq]; flags[0].eater=enemyTurn+3; hand=[mk('green',8)]; playOnFlag(0,0,null,true);
      return new Promise(res=>setTimeout(()=>{ const f=flags[0]; res({mon:!!flagMonster(f), eqInGrave:graveyard.includes(eq), bonus:f.eqBonus||0, n:f.cards.length}); },900))}""")
    check('デスイーターに置いたカードを食べられても、装備は墓地へ行かず旗に残る（装備の二重取り・消失がない）',r['mon'] and not r['eqInGrave'] and r['bonus']==0 and r['n']==3,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[2]; init(); busy=false; pending=null; flags.forEach(f=>{f.cards=[];f.closed=false;f.eater=0});
      const mk=(c,v)=>({kind:'troop',color:c,value:v,uid:uid()});
      flags[0].cards=[mk('red',3)]; flags[1].cards=[mk('red',10),mk('blue',10),{kind:'monster',sub:'number',value:5,uid:uid(),pf:true}];
      hand=[{kind:'tactics',type:'guidance',uid:uid()}]; pending={type:'guidance',step:'dest',from:0,cardIdx:0,handUid:hand[0].uid}; resolveGuidance(1);
      return new Promise(res=>setTimeout(()=>{ const f=flags[1]; res({closed:f.closed, vals:f.cards.map(x=>x.value).join(','), pf:f.cards.some(x=>x.pf)}); },900))}""")
    check('撤収：パニックフィールドの旗へ動かすと、普通に置く時と同じく数字が逆転する（3→8）',r['closed'] and r['vals']=='10,10,8' and not r['pf'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e9; displayedBossHp=1e9; hand=[0,1,2,3].map(()=>({kind:'troop',color:'red',value:3,uid:uid()})); render(); const o={}; o.name=CHARACTER.monSkill.name; o.l0=document.getElementById('specMonL').textContent;
      const rnd=Math.random; Math.random=()=>0.1; monSkillUse(); Math.random=rnd; o.msg=(document.getElementById('hint')||{}).textContent||''; o.next=bashDmg; o.info=specInfoFor('mon').desc; busy=false; render(); o.l1=document.getElementById('specMonL').textContent; return o}""")
    check('斧で攻撃：ボタンに今のダメージが出る／当たると「攻撃力が〇〇に上がった」と出る',r['name']=='斧で攻撃' and '斧' in r['l0'] and '200' in r['l0'] and '240' in r['l1'] and '攻撃力が240に上がった' in r['msg'] and '240' in r['info'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=100; displayedBossHp=100; bashDmg=1000000; const rnd=Math.random; Math.random=()=>0.1; monSkillUse(); Math.random=rnd; return {p:lastPower,d:lastDealt}}""")
    check('斧で攻撃で倒した時、ジャンプの基準には敵HPで切らない本当のダメージが使われる',r['p']==1000000 and r['d']==999900,r)
    r=ev("""()=>{ const keep=dbgLog; dbgLog=[]; for(let g=0;g<8;g++){ dbgLog.push({seq:g*10,type:'game_start',time:'g'+g}); dbgLog.push({seq:g*10+1,type:'turn'}); dbgLog.push({seq:g*10+2,type:'stage_advance'}); }
      const rec=dbgRecent(), n=rec.filter(e=>e.type==='game_start').length, first=rec[0].time, txt=dbgText().split('\\n')[0]; dbgLog=keep; return {n,first,txt}}""")
    check('デバッグログの書き出しは直近5ゲームまで',r['n']==5 and r['first']=='g3' and '5ゲーム' in r['txt'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e9; displayedBossHp=1e9;
      const T=n=>({kind:'troop',color:'red',value:3,uid:uid()}); hand=[T(),T(),T(),T(),T(),{kind:'tactics',type:'holy',uid:uid()}]; const o={five:bashMulNow()}; hand=[T()]; o.one=bashMulNow(); hand=[]; o.zero=bashMulNow();
      hand=[T(),T(),T(),T(),T(),T()]; const rnd=Math.random; Math.random=()=>0.1; bashDmg=1000; monSkillUse(); Math.random=rnd; o.next=bashDmg; return o}""")
    check('斧：当たると 手札の数字カードの枚数×0.3倍（5枚で1.5倍・戦術カードは数えない・0枚なら0倍）',abs(r['five']-1.5)<1e-9 and abs(r['one']-0.3)<1e-9 and r['zero']==0 and r['next']==1800,r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e9; displayedBossHp=1e9; hand=[0,1,2,3].map(()=>({kind:'troop',color:'red',value:3,uid:uid()})); render(); advanceTurn(null); advanceTurn(null);
      const rnd=Math.random; Math.random=()=>0.1; monSkillUse(); Math.random=rnd; busy=false; render(); const o={btn:document.getElementById('specMonL').textContent, chip:!!document.getElementById('axeChip'), info:specInfoFor('mon').desc};
      resetBattleRound(); render(); o.after=document.getElementById('specMonL').textContent; return o}""")
    check('斧：特殊技のボタンに攻撃力と命中率が並び、説明に推移が出る（浮かぶ表示は出さない）','240' in r['btn'] and '50％' in r['btn'] and '×' in r['btn'] and not r['chip'] and '200→240' in r['info'] and '70→65→60→50' in r['info'] and '70％' in r['after'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e12; displayedBossHp=1e12; const o={}; const rnd=Math.random; Math.random=()=>0.1;
      hand=[]; bashDmg=500; monSkillUse(); o.zero=bashDmg; busy=false; monSkillUse(); o.back=bashDmg; o.msg=(document.getElementById('hint')||{}).textContent||''; Math.random=rnd; return o}""")
    check('斧：手札0枚で当てると次は0、その0を撃つと初期値200に戻る',r['zero']==0 and r['back']==200 and '初期値' in r['msg'],r)
    r=ev("""()=>{ document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); gameEnded=false; CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='洞窟のヘビ')); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; init(); const o={}; o.ids=[...document.querySelectorAll('.modal-bg')].filter(m=>getComputedStyle(m).display!=='none').map(m=>m.id); return o}""")
    check('ゲーム開始時：取得条件のポップアップは出ない（条件は戦闘画面のバーに出る）','condModal' not in r['ids'] and 'deckBuildModal' in r['ids'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e12; displayedBossHp=1e12; const o={}; const rnd=Math.random; bashRateNow=0.7; Math.random=()=>0.99; monSkillUse(); o.miss=bashRateNow; busy=false; Math.random=()=>0.1; monSkillUse(); o.hit=bashRateNow; Math.random=rnd; return o}""")
    check('斧：当たると命中率が10％下がり、外れたら据え置き',abs(r['miss']-0.7)<1e-9 and abs(r['hit']-0.6)<1e-9,r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); const o={}; o.base=specMax('mon'); specBonusK.mon=9; o.cap=specMax('mon'); return o}""")
    r=ev("()=>Object.values(MON_SKILL).filter(m=>m.kind&&!['punch','bullet'].includes(m.kind)).map(m=>m.name).filter(n=>SPEC_CAP[n]==null)")
    check('モンスター技はすべて技ごとの上限値を持つ',r==[],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); specBonusK.mon=9; return {cap:specMax('mon')} }""")
    check('特殊技の回数は上限5回を超えない',r['cap']<=5,r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; const o={}; o.before=specMax('mon'); specProg.mon=0; spec.mon=1; render(); const bt=document.getElementById('specMon'); o.gp1=bt.style.getPropertyValue('--gp'); o.has=bt.hasAttribute('data-gp'); advanceToNextStage(); o.mid=specMax('mon'); o.prog=specProg.mon; spec.mon=1; advanceToNextStage(); o.after=specMax('mon'); specBonusK.mon=9; spec.mon=9; advanceToNextStage(); o.cap=specMax('mon'); return o}""")
    check('特殊技：使った回数を戦いをまたいで貯め、上限に届いたら+1（ゲージで見える・上限5まで）',r['has'] and abs(float(r['gp1'])-1/r['before'])<1e-6 and r['prog']==1 and r['mid']==r['before'] and r['after']==r['before']+1 and r['cap']<=5,r)
    r=ev("()=>WAVES.filter(w=>!w.boss&&disList(w).includes('colhalf')).map(w=>w.lv)")
    check('色コンボ半減が、色封じを持つ偶数レベルの敵（lv30以上）に割り当てられている',len(r)>=5 and all(l>=30 and l%2==0 for l in r),r)
    r=ev("""()=>{ CHARACTER=Object.assign({},CHARACTERS[1],{combo:true}); init(); busy=false; const o={}; carryMap={}; flags.forEach(f=>{f.closed=false;f.baseCombo=false;f.symbolColor=null;f.capturedByEnemy=false});
      flags[0].closed=true; flags[0].baseCombo=true; flags[0].symbolColor='red'; flags[0].closeSeq=1; o.single=superMults()[0]||1; o.next=carryNext().red||0;
      carryMap={blue:4}; o.keep=carryNext().blue||0; SUPER_PARAM.keepSkipped=false; o.offKeep=carryNext().blue||0; SUPER_PARAM.keepSkipped=true; return o}""")
    check('スーパーコンボ：旗が1つだけなら×1のまま／役の無かった色の貯まりは消えない（SUPER_PARAMで元に戻せる）',r['single']==1 and r['next']==1 and r['keep']==4 and r['offKeep']==0,r)
    r=ev("""()=>{ const o={}; CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; updateTelops(); o.on=document.querySelector('.telops').style.display; o.txt=document.getElementById('telopNow').textContent;
      CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); updateTelops(); o.off=document.querySelector('.telops').style.display; return o}""")
    check('ミジンコの間だけ、HOWの案内が常時出る（ほかのモンスターでは出ない）',r['on']=='flex' and '手札' in r['txt'] and r['txt']=='手札のカードをドラッグして４枚のシートになんでも良いから３枚づつカードを置こう。' and r['off']=='none',r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; const o={}; updateTelops(); o.d0=document.getElementById('tutArrow').dataset.deg; o.t0=document.getElementById('telopNow').textContent;
      flags[0].closed=true; flags[0].baseCombo=true; flags[0].symbolColor='red'; updateTelops(); turnCounter+=3; updateTelops(); turnCounter+=3; updateTelops(); o.d1=document.getElementById('tutArrow').dataset.deg; o.t1=document.getElementById('telopNow').textContent; return o}""")
    check('ミジンコ：スーパーコンボの説明のあと、HOWが「墓地に手札のカードを捨てて交換出来るぞ」になり、矢印が墓地の方向を向く',r['t0'].startswith('手札のカード') and r['d0']=='0' and r['t1']=='墓地に手札のカードを捨てて交換出来るぞ' and r['d1']!='0',r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; const w=WAVES[stageIndex]; finishWaveOutcome(true,w); return [...document.querySelectorAll('.modal-bg')].filter(m=>getComputedStyle(m).display!=='none').map(m=>m.textContent.slice(0,20))}""")
    pg.wait_for_timeout(1300); r2=ev("()=>[...document.querySelectorAll('.modal-bg')].filter(m=>getComputedStyle(m).display!=='none').map(m=>m.textContent.slice(0,20))")
    check('ミジンコの勝利後は「準備万端」の画面だけが出る（新モンスターなどのポップアップは出さない）',any('準備万端' in x for x in r2) and not any('新しい' in x for x in r2),r2)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; const o={}; updateTelops(); o.a0=document.getElementById('tutArrow').style.display; o.g0=document.querySelector('.upcoming-wrap').classList.contains('tut-glow');
      discardDraw(0,true); busy=false; updateTelops(); o.a1=document.getElementById('tutArrow').style.display; o.g1=document.querySelector('.upcoming-wrap').classList.contains('tut-glow'); o.txt=document.getElementById('telopNow').textContent; return o}""")
    check('ミジンコ：墓地へ捨てたら矢印が消え、敵の攻撃レーンが光り、HOWが攻撃力の説明になる',r['a0']=='flex' and not r['g0'] and r['a1']=='none' and r['g1'] and r['txt']=='ターン毎に敵の攻撃力は上がっていくぞ！\n時々2倍になるから注意が必要だ！',r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; const o={}; const T=()=>{ updateTelops(); return [tutStep, document.getElementById('telopNow').textContent, document.getElementById('tutArrow').style.display, document.querySelector('.upcoming-wrap').classList.contains('tut-glow'), document.querySelector('.nextbar').classList.contains('tut-glow')] };
      o.s0=T(); flags[0].closed=true; flags[0].baseCombo=true; o.s1=T(); const t1=turnCounter; turnCounter=t1+3; o.s2=T(); const t2=turnCounter; turnCounter=t2+3; o.s3=T(); flags[1].closed=true; flags[1].baseCombo=true; o.s4=T(); const t4=turnCounter; turnCounter=t4+3; o.s5=T(); return o}""")
    check('ミジンコの案内：置く→（シート完成）役の説明→スーパーコンボ→墓地→（役2つか捨てる）敵の攻撃レーン→カード予測レーン',
      r['s0'][0]==0 and r['s1'][0]==1 and '同じ色か数' in r['s1'][1] and r['s2'][0]==2 and 'シート同士で同じマーク' in r['s2'][1] and r['s2'][2]=='none' and r['s3'][0]==3 and '墓地' in r['s3'][1] and r['s3'][2]=='flex' and r['s4'][0]==4 and r['s4'][3] and r['s5'][0]==5 and r['s5'][4] and not r['s5'][3] and '次くるカード' in r['s5'][1],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; tutStep=2; updateTelops(); const sv=document.getElementById('tutFlagArrows'); const o={disp:sv&&sv.style.display, n:document.querySelectorAll('#tutFlagArrows line').length}; tutStep=0; updateTelops(); o.off=document.getElementById('tutFlagArrows').style.display; return o}""")
    check('ミジンコの案内：「同じマーク」の段階で、シート同士を時計回りの矢印でつなぐ（それ以外では消える）',r['disp']!='none' and r['n']>=4 and r['off']=='none',r)
    r=ev("""()=>{ const o={}; const w=WAVES.filter(x=>!x.boss); const late=w[w.length-1], mid=w.find(x=>x.lv===50), early=w.find(x=>x.lv===30); o.late=disEveryAt(late); o.mid=disEveryAt(mid); o.early=disEveryAt(early); o.base=DIS_PARAM.every;
      o.pois=disList(late).includes('poison')&&disList(late).includes('seal'); CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); stageIndex=WAVES.indexOf(late); init(); stageIndex=WAVES.indexOf(late); addWaveCurses(); o.deckCurse=activeDeck.some(c=>c.type==='curse_poison'||c.type==='curse_seal'); return o}""")
    check('後半の敵ほど妨害の間隔が短くなる／毒・封鎖の呪いは最初の山札に入れず、妨害レーンの技になる',r['late']<r['mid']<r['early']==r['base'] and r['pois'] and not r['deckCurse'],r)
    r=ev("""()=>{ const o={}; const top=WAVES.findIndex(x=>x.id==='全てを無に帰すもの'); ['ミジンコ','ミジンコリーダー','ミジンコキング'].forEach(id=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id===id)); stageIndex=top>=0?top:WAVES.length-1; try{ localStorage.removeItem('soloSiegeAlienBeat'); }catch(e){} o[id]=alienEncounterId(); }); return o}""")
    check('ミジンコ・ミジンコリーダーの体では宇宙人が出ない（ミジンコキングは別）',r['ミジンコ'] is None and r['ミジンコリーダー'] is None and r['ミジンコキング'] is not None,r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; const o={}; flags[0].closed=true; flags[0].baseCombo=false; updateTelops(); o.t=document.getElementById('telopNow').textContent;
      flags[0].cards=[{kind:'troop',color:'red',value:1,uid:uid()},{kind:'troop',color:'blue',value:5,uid:uid()}]; flags[0].closed=false; tutStep=0; hand=[{kind:'troop',color:'green',value:9,uid:uid()}]; picked=0; playOnFlag(0,0,null); o.ask=[...document.querySelectorAll('.modal-bg')].some(m=>getComputedStyle(m).display!=='none'&&m.textContent.includes('役なしになります'));
      document.querySelectorAll('.modal-bg').forEach(m=>{ if(m.textContent.includes('役なしになります')) m.remove(); }); busy=false; tutStep=1; flags[1].closed=false; flags[1].cards=[{kind:'troop',color:'red',value:1,uid:uid()},{kind:'troop',color:'blue',value:5,uid:uid()}]; hand=[{kind:'troop',color:'green',value:9,uid:uid()}]; picked=0; playOnFlag(0,1,null); o.ask2=[...document.querySelectorAll('.modal-bg')].some(m=>getComputedStyle(m).display!=='none'&&m.textContent.includes('役なしになります')); return o}""")
    check('ミジンコ：役無しでもシートが1つ完成したら「同じ色か数、または連番…」を出す。役なしの確認は、最初の「なんでも良いから」の段階だけ出さない',r['t']=='同じ色か数、または連番にして置くと更に攻撃力アップ！' and not r['ask'] and r['ask2'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false; flags.forEach(f=>{f.closed=false;f.baseCombo=false;f.cards=[]}); tutStep=5; tutT=turnCounter; tutDiscarded=true; updateTelops(); const o={a:tutStep}; turnCounter+=TUT_STEP_TURNS; updateTelops(); o.b=tutStep; o.d=tutDiscarded; o.t=document.getElementById('telopNow').textContent; return o}""")
    check('ミジンコの案内：カード予測のあと、最初（置く）に戻ってくり返す',r['a']==5 and r['b']==0 and not r['d'] and r['t'].startswith('手札のカードをドラッグして'),r)
    r=ev("""()=>{ const o={}; const setup=nm=>{ const i=WAVES.findIndex(w=>dispName(w.id)===nm); CHARACTER=makeMonChar(i,WAVES[i].id); init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false; };
      setup('若いオーク'); carryMap={}; hand=[makeCurse('poison'),{kind:'troop',color:'red',value:3,uid:uid()}]; monSkillUse(); o.orcLow=hand.length>=2&&hand.some(isCurse)&&!carryMap.green;
      carryMap={green:10}; monSkillUse(); o.orc=!hand.some(isCurse)&&carryMap.green===9;
      setup('ゴブリン'); carryMap={yellow:20}; hand=[]; monSkillUse(); monSkillUse(); monSkillUse(); o.gob=carryMap.yellow===20-1-2-4&&hand.filter(c=>c.type==='duplicate').length===3&&copyN===3;
      resetBattleRound(); o.gobReset=copyN===0; carryMap={yellow:3}; hand=[]; copyN=2; monSkillUse(); o.gobLow=hand.length===0&&carryMap.yellow===3;
      setup('ミイラ'); carryMap={purple:10}; monSkillUse(); o.mum=mummyOn&&carryMap.purple===9;
      setup('ガーゴイル'); carryMap={red:12}; const hp0=bossHp; monSkillUse(); o.gar=carryMap.red===7&&bossHp<=hp0-Math.floor(hp0/3)+1&&bossHp>=hp0-Math.floor(hp0/3)-1;
      setup('ガーゴイル'); carryMap={red:4}; const hp1=bossHp; monSkillUse(); o.garLow=bossHp===hp1&&carryMap.red===4;
      setup('ゾンビ'); carryMap={green:5}; monSkillUse(); o.zom=zombieRevive&&!carryMap.green; playerHp=0; o.zrev=tryRevive()&&playerHp===Math.ceil(playerHpMax/2)&&!zombieRevive;
      setup('モンク'); monSkillUse(); o.mon=monkQ.join()==='0.5,2';
      setup('侍'); gold=7; const hp2=bossHp; monSkillUse(); o.sam=gold===0&&bossHp===Math.max(0,hp2-700);
      setup('農夫'); playerHp=Math.max(1,playerHpMax-500); const h3=playerHp; monSkillUse(); o.farm0=playerHp===h3&&farmerHealAt>0; advanceTurn(null); o.farm=playerHp===h3+MONSK.farmerHeal&&farmerHealAt===0;
      o.names=['ガーゴイル','モンク','侍','農夫'].map(n=>WAVES.some(w=>dispName(w.id)===n)).every(Boolean);
      setup('騎士'); carryMap={red:5}; const nb={kind:'monster',sub:'number',value:6}; const b0=monsterBonusFor(nb); monSkillUse(); o.arm=armedOn&&carryMap.red===2&&b0===6&&monsterBonusFor(nb)===12; resetBattleRound(); o.armOff=!armedOn&&monsterBonusFor(nb)===6;
      setup('メデューサ'); carryMap={purple:2}; busy=false; monSkillUse(); const et0=enemyTurn, tc0=turnCounter; o.sto0=stoneLeft===3&&carryMap.purple===1; for(let i=0;i<3;i++) advanceTurn(null); o.sto=enemyTurn===et0&&turnCounter===tc0+3&&stoneLeft===0;
      setup('ドラキュラ'); playerHp=10; bossHp=1000; score=400; prevSnap={t:0,pp:0}; enemyTurn=0; const hpd=playerHp; try{ checkWaveOutcome(); }catch(e){} o.vamp=playerHp>hpd;
      setup('トロル'); carryMap={green:3}; score=0; monSkillUse(); o.troll=score===10000&&carryMap.green===2; carryMap={}; monSkillUse(); o.trollLow=score===10000;
      setup('狼男'); carryMap={yellow:5}; hand=[{kind:'tactics',type:'scout',name:'補充',uid:uid()},{kind:'troop',color:'red',value:4,uid:uid()}]; const dk0=activeDeck.slice(-3).map(c=>c.uid); monSkillUse(); o.moon=carryMap.yellow===4&&hand.every(c=>c.kind==='troop')&&hand[1].moon&&ptv(hand[1])===8&&val(hand[1])===4&&activeDeck.slice(-10).every(c=>c.kind==='troop'); moonClear(); o.moonBack=hand[0].type==='scout'&&!hand[1].moon;
      setup('若いオーク'); carryMap={green:5}; busy=false; render(); o.lbl=/×1/.test(document.getElementById('specMonL').textContent)&&!!document.querySelector('#specMonL svg');
      return o}""")
    check('特殊技21〜35：月光・大巨漢・きれい好き・模造品・財宝・完全武装・石化・吸血・ファイアブレス・蘇り・ためる・銭投げ・収穫祭・ファイアブレス・蘇り・ためる・銭投げ・収穫祭（足りない時は使えない）',all(r.values()),r)
    r=ev("""()=>{ const o={}; lsSet('soloSiegeAlienBeat','[]'); o.res=comboRestricted(); CHARACTER=makeMonChar(WAVES.findIndex(x=>x.id==='ミジンコ')); init(); document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); carryMap={red:3}; nextStageIdx=INTRO_LEADER; advanceToNextStage(); o.mijinko=carryMap.red===3; lsSet('soloSiegeAlienBeat',JSON.stringify(['月の民'])); return o}""")
    check('ミジンコの間はスーパーコンボを次の戦いへ引き継げる',r['mijinko'] and r['res'],r)
    r=ev("""async()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      flags[0].cards=[makePanicField()]; hand=[{kind:'troop',color:'red',value:3,uid:uid()}]; const hl=hand.length; playOnFlag(0,0,null); o.ask=[...document.querySelectorAll('.modal-bg')].some(m=>m.textContent.includes('になるけど良いですか')&&m.textContent.includes('8')); o.notYet=hand.length===hl&&flags[0].cards.length===1;
      const y=document.getElementById('pfYes'); if(y) y.click(); await new Promise(r=>setTimeout(r,1500)); o.placed=flags[0].cards.some(c=>c.kind==='troop'&&c.value===8);
      document.querySelectorAll('.modal-bg').forEach(m=>{ if(m.id!=='x') m.style.display='none'; }); busy=false;
      enemySched={}; enemyTurn=3; enemySched[4]='autonum'; warnedDisTurn=-1; advanceTurn(null); o.warn=warnedDisTurn===enemyTurn+1||warnedDisTurn===4; 
      return o}""")
    check('パニックフィールド：数字を置く前に「置いた時に○になるけど良いですか？」を出す／妨害が1ターン前に予告される',r['ask'] and r['notYet'] and r['placed'],r)
    r=ev("""async()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const f=flags[0]; f.cards=[]; enemySched={}; applyEnemyEvent('autonum'); const c=f.cards.find(x=>x.autoPlaced)||flags.flatMap(g=>g.cards).find(x=>x.autoPlaced); o.flying=!!(c&&c.flying); o.fly=!!document.querySelector('.enemy-fly'); await new Promise(r=>setTimeout(r,ENEMY_FLY_MS+600)); o.after=!document.querySelector('.enemy-fly')&&!(c&&c.flying); return o}""")
    check('敵がカードを置く時、敵からシートへ飛んでくる演出が出て、あとで消える',r['flying'] and r['fly'] and r['after'],r)
    r=ev("""async()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const cf=makeColorField('red'); flags[0].cards=[cf]; hand=[{kind:'monster',sub:'mark',color:'blue',uid:uid()}]; o.can=targetsFor(hand[0]).includes(0); playOnFlag(0,0,null); await new Promise(r=>setTimeout(r,1500)); o.color=cf.color; o.still=flags[0].cards.length===1&&flags[0].cards[0]===cf; return o}""")
    check('カラフルフィールドに色の装備を置くと、フィールドがその色に変わる',r['can'] and r['color']=='blue' and r['still'],r)
    r=ev("""async()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const cf=makeColorField('red'); flags[0].cards=[cf]; hand=[{kind:'monster',sub:'mark',color:'red',uid:uid()}]; playOnFlag(0,0,null); await new Promise(r=>setTimeout(r,1500)); o.n=flags[0].cards.length; return o}""")
    check('カラフルフィールドに同じ色の装備を置くと、フィールドが消える',r['n']==0,r)
    r=ev("""async()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      flags[0].cards=[{kind:'monster',sub:'combined',color:'red',value:8,enemyCard:false,uid:uid()}]; const lo={kind:'troop',color:'blue',value:5,uid:uid()}, hi={kind:'troop',color:'blue',value:9,uid:uid()}, ok={kind:'troop',color:'red',value:9,uid:uid()};
      o.hiOk=targetsFor(hi).includes(0); o.loNo=!targetsFor(lo).includes(0); o.okOk=targetsFor(ok).includes(0); return o}""")
    check('色＋数字の条件の旗：違う色でも数字が足りていれば置ける（数字が足りないカードは置けない）',all(r.values()),r)
    r=ev("""()=>{ const o={}; CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false; autoQ={};
      flags.forEach(f=>{ f.cards=[]; f.closed=false; }); const pl=planAt('pfield',0); pl.flag=1; flags[1].cards=[{kind:'monster',sub:'number',value:6,uid:uid()}];
      o.stay=autoTargetIdx(pl)===1; applyEnemyEvent('pfield'); o.pf=flagMonster(flags[1]).pf===true&&flags[1].cards.length===1; return o}""")
    check('パニックフィールドの予告：予告した旗に武器を置いても、予告は他の旗へ移らない（装備に逆転がかかる）',r['stay'] and r['pf'],r)
    b.close()
print('FAILED' if fails else 'ALL OK',len(fails)); sys.exit(1 if fails else 0)
