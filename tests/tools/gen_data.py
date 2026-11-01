"""データ帳の元データを、いまのゲーム（public/index.html）から取り出して JSON にする。
使い方: python3 tests/tools/gen_data.py out.json   →  data帳HTMLの `const D=...;` に差し込む"""
import sys,os,json
from playwright.sync_api import sync_playwright
GAME='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','public','index.html'))
JS=r"""()=>{
 lsSet('soloSiegeAlienBeat',JSON.stringify(['月の民']));   // 妨害は月の民を倒した後だけ出る
 const NM={autonum:'敵数字',cfield:'カラフル',pfield:'パニック',minus:'マイナス',bomb:'ボム',half:'防御',colnull:'色封じ',guard:'ｺﾝﾎﾞ↓',bguard:'ｺﾝﾎﾞ↓↓',comboreset:'ｺﾝﾎﾞ0',minusrain:'ﾏｲﾅｽ雨',deatheater:'ﾃﾞｽｲｰﾀｰ',ghost:'ワーム',null:'無効',dark:'暗闇',freeze:'いてつく',wipe:'全滅',assassin:'暗殺',blind:'ブラインド'};
 const nm=t=>NM[t]||(EVENT_INFO[t]&&EVENT_INFO[t].label)||t;
 const skill=w=>{ const ms=MON_SKILL[w.name]; return ms?((ms.icon||'')+(ms.name||'')):''; };
 const en=[];
 WAVES.forEach((w,i)=>{
   const ec=ENEMY_CFG[w.name]||{}; let dis='', first='', gap='';
   if(w.fixed){ dis='（固定スケジュール）'; }
   else { const dl=disList(w); if(dl.length){ const wt=disWeights(w,dl), tot=Object.values(wt).reduce((a,b)=>a+b,0);
     dis=Object.entries(wt).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).map(([t,v])=>nm(t)+Math.round(v/tot*100)+'%').join(' → ');
     const soft=(!w.boss&&w.lv<DIS_PARAM.softLv); gap=ec.gap?Math.max(2,ec.gap):Math.max(2,Math.round(w.gap*DIS_PARAM.every*(soft?DIS_PARAM.softEvery:1))); first=ec.first||DIS_PARAM.startTurn; } }
   en.push([w.boss?'★':w.lv, w.name, w.hp, w.atk, w.grow, w.first, w.gap, skill(w)||(MON_SKILL[w.name]?'':'なし'), first, gap, dis]);
 });
 const acc=ACC_DEFS.map(d=>[d.name,d.icon||'',d.desc||'',d.id]);
 const curse=Object.entries(CURSE_DEF).map(([k,v])=>[v.name,v.desc||'',k]);
 const price=Object.entries(CARD_PRICE);
 const skills=Object.entries(MON_SKILL).map(([k,v])=>[k,((v.icon||'')+' '+(v.name||'')).trim(),v.desc||'']);
 const ev=Object.entries(EVENT_INFO).map(([k,v])=>[v.icon,v.label,k,(typeof EVENT_DESC!=='undefined'&&EVENT_DESC[k])?EVENT_DESC[k]():'']);
 const alien=ALIEN_GIFTS.map(g=>[g.id,g.lv,(ALIEN_SURGERY[g.id]||'（強化の内容は準備中）'),HIDDEN_BOSSES.includes(g.id)?'非公開':'']);
 return {build:BUILD_ID,enemies:en,acc,curse,price,skill:skills,ev,alien,dp:DIS_PARAM};
}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.add_init_script("localStorage.setItem('soloSiegeNoLog','1')")
    pg.goto(GAME); pg.wait_for_timeout(600)
    d=pg.evaluate(JS); b.close()
json.dump(d,open(sys.argv[1],'w'),ensure_ascii=False)
print({k:(len(v) if hasattr(v,'__len__') else v) for k,v in d.items()})
