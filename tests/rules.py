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
    check('通常の敵が82体',ev("()=>WAVES.filter(w=>!w.boss).length")==82)
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
      o.in12=quickMult(ACC_PARAM.quickTurns); o.out=quickMult(ACC_PARAM.quickTurns+1);
      accOwned.push({aid:accSeq++,id:'double_x'}); accEq.push(accOwned[accOwned.length-1].aid); o.dbl=quickMult(3); return o}""")
    check('早撃ちのブーツ：持っていなければ等倍',r['none']==1,r)
    check('早撃ちのブーツ：12ターン以内は×5、13ターン目からは等倍',r['in12']==5 and r['out']==1,r)
    check('早撃ちのブーツ：倍の腕輪で増え分が2倍（×9）',r['dbl']==9,r)
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); battleGoals=['quick_boots']; accOwned=accOwned.filter(a=>a.id!=='quick_boots'); const o={price:accPrice(accDef('quick_boots')),before:goalMet('quick_boots',true)};
      accStat.fastAtk=1; o.after=goalMet('quick_boots',true); const got=acquireNew(true); o.got=got.some(d=>d.id==='quick_boots'); o.owned=accOwned.some(a=>a.id==='quick_boots'); return o}""")
    check('早撃ちのブーツ：条件（12ターン以内に攻撃）を満たすと戦闘後にもらえる',r['before']==False and r['after']==True and r['got'] and r['owned'],r)
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
      const o={kind:CHARACTER.monSkill&&CHARACTER.monSkill.kind, stock0:hpStock, hp0:playerHp}; specUse('mon'); await new Promise(r=>setTimeout(r,200));
      o.stock1=hpStock; o.hp1=playerHp; o.atk=plAtkMult;
      // ストックがあればHP0で復活／無ければ死ぬ
      playerHp=0; o.rev=tryRevive(); o.hpRev=playerHp; o.stock2=hpStock; o.revNone=tryRevive();
      return o}""")
    check('スライム：細胞分裂でHP・攻撃力が半分になり体力ストック+1／ストックで1回復活（初期は0）',r['kind']=='cell' and r['stock0']==0 and r['stock1']==1 and r['hp1']==-(-r['hp0']//2) and r['atk']==0.5 and r['rev'] and r['hpRev']>0 and r['stock2']==0 and not r['revNone'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const o={}; flags.forEach(f=>{f.cards=[];f.closed=false;f.lockedUntil=0}); applyEnemyEvent('assassin'); o.none=true;
      flags[1].cards=[{kind:'troop',color:'red',value:9,uid:uid()},{kind:'troop',color:'red',value:8,uid:uid()},{kind:'troop',color:'red',value:7,uid:uid()}]; const g0=graveyard.length;
      applyEnemyEvent('assassin'); o.left=flags[1].cards.length; o.grave=graveyard.length-g0; o.banner=document.getElementById('evBanner').classList.contains('dis')&&document.getElementById('evBanner').textContent.includes('妨害');
      const w=WAVES.find(x=>!x.boss&&x.lv>=30); o.inList=disList(w).includes('assassin'); const lo=WAVES.find(x=>!x.boss&&x.lv===25); o.early=lo?disList(lo).includes('assassin'):true;
      return o}""")
    check('暗殺：旗のカードが1枚ランダムに墓地へ／妨害の発動を大きな帯で知らせる／中盤以降の敵が出す',r['left']==2 and r['grave']==1 and r['banner'] and r['inList'] and r['early'],r)
    b.close()
print('FAILED' if fails else 'ALL OK',len(fails)); sys.exit(1 if fails else 0)
