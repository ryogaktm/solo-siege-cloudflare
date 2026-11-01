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
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={}; hand[0]=Object.assign({kind:'tactics'},TACTICS.find(t=>t.type==='scout'),{uid:uid()}); render();
      const h0=hand.map(c=>c.uid).join(), d0=activeDeck.map(c=>c.uid).join(), t0=turnCounter, g0=graveyard.length;
      useScout(0); await sleep(700); o.pend=pending&&pending.type==='discard'&&pending.scout; o.handUp=hand.length; o.turnHeld=turnCounter===t0; o.btn=document.getElementById('cancelPendingBtn').style.display!=='none';
      cancelPending(); await sleep(200); o.restored=hand.map(c=>c.uid).join()===h0 && activeDeck.map(c=>c.uid).join()===d0 && turnCounter===t0 && graveyard.length===g0 && !pending;
      useScout(0); await sleep(700); discardTap(1); discardTap(2); confirmDiscard(); await sleep(700); o.dd=[!!pending,turnCounter,t0,graveyard.length,g0,hand.length,h0.split(',').length]; o.done=!pending && turnCounter===t0+1 && graveyard.length===g0+3 && hand.length===h0.split(',').length;
      return o}""")
    check('補充：捨てるカードを選んでいる間はキャンセルでき（手札・山札・ターンが元に戻る）、確定でターンが進む',r['pend'] and r['turnHeld'] and r['btn'] and r['restored'] and r['done'],r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false; stageIndex=WAVES.findIndex(w=>w.lv===30); introOn=false; rollGoals();
      document.getElementById('cardListModal').style.display='flex'; document.getElementById('specModal').style.display='flex';
      grantStageReward(); await new Promise(r=>setTimeout(r,300));
      return {list:document.getElementById('cardListModal').style.display, spec:document.getElementById('specModal').style.display, chest:document.getElementById('chestModal').style.display}}""")
    check('戦いが終わったら、開きっぱなしのポップアップ（一覧・特殊技など）が閉じて宝箱だけが出る',r['list']=='none' and r['spec']=='none' and r['chest']=='flex',r)
    r=ev("""async()=>{ CHARACTER=CHARACTERS[2]; init(); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); busy=false;pending=null;gameEnded=false;inPrep=false; stageIndex=WAVES.findIndex(w=>w.lv===30); introOn=false;
      const sleep=ms=>new Promise(r=>setTimeout(r,ms)), o={}; startBattleGoals(); await sleep(1000); const cm=document.getElementById('condModal'); o.cond=!!cm&&cm.style.display==='flex'; if(cm) cm.style.display='none';
      renderBattle(); o.before=document.querySelectorAll('.modal-bg[style*="10003"]').length; const aid=accSeq++; accOwned.push({aid,id:'sp_double'}); accEq.push(aid); renderBattle(); o.alert=document.querySelectorAll('.modal-bg[style*="10003"]').length; o.txt=(document.querySelector('.modal-bg[style*="10003"]')||{}).innerText||'';
      return o}""")
    check('戦闘の最初に取得条件の一覧が出る／戦闘中に特殊技の回数の上限が上がるとアラートが出る',r['cond'] and r['before']==0 and r['alert']==1 and '回' in r['txt'],r)
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
      flags[fi].cards=[{kind:'troop',color:'red',value:3,uid:uid()},{kind:'troop',color:'red',value:4,uid:uid()}]; render(); const fc2=autoForecast(); const fi2=+Object.keys(fc2)[0]; o.moved=fi2!==fi && !!document.querySelector('.flag[data-index="'+fi2+'"] .auto-fc');
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
        o[ev]={has, fi, tgt, changed: ev==='ghost'?(haunt[tgt]>0):(before!==after), onTgt: ev==='ghost'?true:flags[tgt].cards.length!==(+before.split(',')[tgt])};
      }
      return o}""")
    ok=all(r[k]['has'] and r[k]['fi']==r[k]['tgt'] and r[k]['changed'] and r[k]['onTgt'] for k in ['minus','ghost','deatheater','assassin'])
    check('旗を狙う妨害（マイナスの武器・ワームホール・デスイーター・暗殺）：旗の右上に予定が出て、予定の旗に発動する',ok,r)
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
    JS_ENC="""(mode)=>{ CHARACTER=CHARACTERS[2]; init(); lsSet('soloSiegeAlienBeat','[]');
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
    pg.evaluate("localStorage.setItem('soloSiegeAlienBeat',JSON.stringify(['月の民']))")
    r=pg.evaluate("""()=>{ unlockMon('ミジンコキング'); ['月の民','火星人','水星人','金星人','太陽神'].forEach(unlockMon); buildCharList(); const g=document.getElementById('monGrid');
      const t=[...g.querySelectorAll('.mon-tile')].map(e=>({n:e.querySelector('b').textContent.replace(/\\s/g,''),a:e.classList.contains('alien')}));
      const ix=n=>t.findIndex(x=>x.n===n); return {n:t.length,aliens:t.filter(x=>x.a).map(x=>x.n),moonAfterSpider:ix('月の民')>ix('大グモ')&&ix('月の民')<ix('コボルト'),marsBetween:ix('火星人')>ix('呪われた農夫')&&ix('火星人')<ix('骸骨戦士'),lastNotAlien:!t[t.length-1].a||t[t.length-1].n==='太陽神'} }""")
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
      playerHp=100; playerHpMax=100; applyEnemyEvent('poison'); const hp0=playerHp; advanceTurn(null); advanceTurn(null); o.venom=hp0-playerHp; o.venomOn=turnCounter<=dis.venomUntil;
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
          r['venom']==4 and r['venomOn'] and r['venomEnd']==10 and r['noDark'] and r['hit']==70 and r['miss']==0 and r['jamOk'] and r['jamNg'] and r['name']=='アサシン' and r['dis']==['assassin'] and r['spr']=='assassin' and r['jamKind']=='jam' and r['bashKind']=='bash',r)
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
    r=ev("""()=>{ CHARACTER=CHARACTERS[1]; init(); autoQ={}; const pl=planAt('cfield',0); const col=pl.col; const h0=hand.length; applyEnemyEvent('cfield'); const c=flags.map(flagMonster).find(x=>x&&x.sub==='cfield'); return {col, got:c&&c.color, inHand:hand.some(x=>x.sub==='cfield'), left:(autoQ.cfield||[]).length}}""")
    check('カラフルフィールド：予測した色のまま、手札ではなく旗に直接置かれる',r['col']==r['got'] and not r['inHand'],r)
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
    check('カラフルフィールドの予測が旗の右上に出て、描画でエラーにならない（進行不能の再発防止）',not r['errs'] and r['txt']==1 and r['lab'] and 'カラフル' in r['lab'],r)
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
    check('斧：特殊技のボタンに攻撃力と命中率が並び、説明に推移が出る（浮かぶ表示は出さない）','240' in r['btn'] and '60％' in r['btn'] and '×' in r['btn'] and not r['chip'] and '200→240' in r['info'] and '70→65→60' in r['info'] and '70％' in r['after'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e12; displayedBossHp=1e12; const o={}; const rnd=Math.random; Math.random=()=>0.1;
      hand=[]; bashDmg=500; monSkillUse(); o.zero=bashDmg; busy=false; monSkillUse(); o.back=bashDmg; o.msg=(document.getElementById('hint')||{}).textContent||''; Math.random=rnd; return o}""")
    check('斧：手札0枚で当てると次は0、その0を撃つと初期値200に戻る',r['zero']==0 and r['back']==200 and '初期値' in r['msg'],r)
    r=ev("""()=>{ document.querySelectorAll('.modal-bg').forEach(m=>m.style.display='none'); gameEnded=false; CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='洞窟のヘビ')); document.getElementById('titleScreen').style.display='none'; document.getElementById('appRoot').style.display=''; init(); const o={}; o.ids=[...document.querySelectorAll('.modal-bg')].filter(m=>getComputedStyle(m).display!=='none').map(m=>m.id); return o}""")
    check('ゲーム開始と同時に取得条件の画面が出る（戦闘画面が見えてから出ない）','condModal' in r['ids'] and 'deckBuildModal' in r['ids'],r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); busy=false; pending=null; bossHp=1e12; displayedBossHp=1e12; const o={}; const rnd=Math.random; bashRateNow=0.7; Math.random=()=>0.99; monSkillUse(); o.miss=bashRateNow; busy=false; Math.random=()=>0.1; monSkillUse(); o.hit=bashRateNow; Math.random=rnd; return o}""")
    check('斧：当たると命中率が10％下がり、外れたら据え置き',abs(r['miss']-0.7)<1e-9 and abs(r['hit']-0.6)<1e-9,r)
    r=ev("""()=>{ CHARACTER=makeMonChar(WAVES.findIndex(x=>x.baseId==='野盗の一団')); init(); const o={}; o.base=specMax('mon'); specBonusK.mon=9; o.cap=specMax('mon'); return o}""")
    r=ev("()=>Object.values(MON_SKILL).filter(m=>m.kind&&!['punch','bullet'].includes(m.kind)).map(m=>m.name).filter(n=>SPEC_CAP[n]==null)")
    check('モンスター技はすべて技ごとの上限値を持つ',r==[],r)
    check('特殊技の回数は上限5回を超えない',r['cap']<=5,r)
    b.close()
print('FAILED' if fails else 'ALL OK',len(fails)); sys.exit(1 if fails else 0)
