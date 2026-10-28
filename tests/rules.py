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
    check('通常の敵が72体',ev("()=>WAVES.filter(w=>!w.boss).length")==72)
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
    b.close()
print('FAILED' if fails else 'ALL OK',len(fails)); sys.exit(1 if fails else 0)
