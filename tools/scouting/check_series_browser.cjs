/* Exercise the complete recording catalog, including nested Pages routes. */
const fs=require('fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
  const origin=(process.argv[2]||'http://127.0.0.1:8027').replace(/\/$/,''),out=process.argv[3]||'qa/scouting-series';
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{})});
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],bad=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(origin)&&r.status()>=400)bad.push([r.status(),r.url()])});
  const assert=(x,m)=>{if(!x)throw Error(m)};
  const catalog=await (await page.request.get(origin+'/scouting/catalog.json')).json();
  assert(catalog.length===5,'Expected original plus four new recordings');
  const results=[];
  for(const row of catalog){
    const route=origin+'/scouting/'+row.route,label=row.slug||'original';
    await page.goto(route);await page.locator('.finding').first().waitFor();
    const d=await page.evaluate(()=>window.scoutingReport.data);
    assert(d.source.video_id===row.video_id,'Catalog resolves to wrong video: '+label);
    assert(await page.locator('#recording-picker option').count()===catalog.length,'Missing selector choices');
    assert(await page.locator('#recording-picker option:checked').textContent()===row.label,'Wrong selected recording');
    assert(await page.locator('.finding').count()===d.findings.length,'Missing findings');
    await page.locator('.brand-mark').evaluate(e=>e.decode());
    for(const team of ['blue','red','green']){
      await page.locator('#team-filter').selectOption(team);
      for(const type of ['strength','weakness','adaptation']){
        await page.locator('#type-filter').selectOption(type);
        assert(await page.locator('.finding').count()===d.findings.filter(f=>f.team===team&&f.type===type).length,'Filter mismatch '+label);
      }
    }
    await page.reload();assert(await page.locator('#team-filter').inputValue()==='green','Shared filter did not persist');
    await page.locator('#team-filter').selectOption('all');await page.locator('#type-filter').selectOption('all');
    await page.screenshot({path:out+'/'+label+'-desktop.png',fullPage:true});
    await page.getByRole('button',{name:'Match timeline',exact:true}).click();
    assert(await page.locator('#score-rows tr').count()===d.score_anchors.length,'Score rows missing');
    assert(await page.locator('#score-chart circle').count()===d.score_anchors.reduce((n,r)=>n+['blue','red','green'].filter(k=>r[k]!==null).length,0),'Score dots missing');
    const headers=await page.locator('#score-head th').allTextContents();
    assert(headers.slice(2,5).join('|')===d.teams.map(t=>t.name).join('|'),'Score headings leak another recording');
    for(const e of d.evidence.filter(e=>e.clip).filter((e,i)=>!process.env.SCOUTING_QUICK_CHECK||i===0)){
      await page.evaluate(id=>window.scoutingReport.inspect(id),e.id);
      await page.locator('#evidence-image').evaluate(e=>e.decode());
      const meta=await page.locator('#evidence-video').evaluate(el=>new Promise((resolve,reject)=>{
        const done=()=>resolve({duration:el.duration,width:el.videoWidth});
        if(el.readyState>=1)return done();
        el.addEventListener('loadedmetadata',done,{once:true});el.addEventListener('error',()=>reject(Error(el.error?.message||'decode failed')),{once:true});
      }));
      assert(Math.abs(meta.duration-(e.clip.end_seconds-e.clip.start_seconds))<.25&&meta.width===1280,'Excerpt mismatch '+e.id);
      await page.getByRole('button',{name:'Play excerpt',exact:true}).click();
      await page.locator('#evidence-video').evaluate(async el=>{el.muted=true;await el.play()});
      await page.waitForFunction(()=>document.getElementById('evidence-video').currentTime>.3);
      await page.getByRole('button',{name:'Close evidence',exact:true}).click();
      assert(!await page.locator('#inspector').evaluate(el=>el.open),'Close reopened dialog');
    }
    await page.goto(route+'?view=timeline&team=red&evidence='+d.result.evidence_id);
    await page.locator('#inspector[open]').waitFor();await page.locator('#evidence-image').evaluate(e=>e.decode());
    await page.screenshot({path:out+'/'+label+'-result.png'});
    await page.keyboard.press('Escape');
    assert(!page.url().includes('evidence='),'Closed dialog retained share parameter');
    const exported=await (await page.request.get(route+'data/scouting-report.json')).json();
    assert(JSON.stringify(d)===JSON.stringify(exported),'Published JSON differs from page');
    for(const name of ['data/findings.csv','data/review-log.json'])assert((await page.request.get(route+name)).ok(),'Missing export');
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('button',{name:'The briefing',exact:true}).click();
    assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Mobile briefing overflow '+label);
    await page.screenshot({path:out+'/'+label+'-mobile.png',fullPage:true});
    await page.getByRole('button',{name:'Match timeline',exact:true}).click();
    assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Mobile timeline overflow');
    await page.evaluate(id=>window.scoutingReport.inspect(id),d.result.evidence_id);
    await page.locator('#evidence-image').evaluate(e=>e.decode());
    assert(!await page.locator('#inspector').evaluate(e=>e.scrollWidth>e.clientWidth),'Mobile evidence overflow');
    await page.screenshot({path:out+'/'+label+'-mobile-evidence.png'});await page.keyboard.press('Escape');
    await page.setViewportSize({width:1440,height:1000});
    // Navigate from each nested route to another completed recording.
    const next=catalog[(catalog.indexOf(row)+1)%catalog.length];
    const nextURL=new URL(origin+'/scouting/'+next.route).href;
    await Promise.all([page.waitForURL(nextURL),page.locator('#recording-picker').selectOption({label:next.label})]);
    await page.waitForLoadState('load');
    assert(await page.evaluate(()=>window.scoutingReport?.data.source.video_id)===next.video_id,'Selector opened wrong report');
    const clips=d.evidence.filter(e=>e.clip).length;
    results.push({video:row.video_id,route:row.route,findings:d.findings.length,evidence:d.evidence.length,anchors:d.score_anchors.length,clips,clipsTested:process.env.SCOUTING_QUICK_CHECK?Math.min(1,clips):clips});
    console.log('PASS',label);
  }
  await page.goto(origin+'/scouting/patterns/');
  assert(await page.locator('h3').count()===5,'Comparison themes missing');
  await page.screenshot({path:out+'/patterns-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Mobile comparison overflow');
  await page.screenshot({path:out+'/patterns-mobile.png',fullPage:true});
  await page.getByRole('link',{name:'Disabled spawn radar',exact:true}).click();
  await page.locator('#inspector[open]').waitFor();
  assert((await page.locator('#evidence-title').textContent()).includes('radar destroyed'),'Comparison evidence link failed');
  assert(!errors.length,errors.join('\n'));assert(!bad.length,JSON.stringify(bad));
  fs.writeFileSync(out+'/browser-results.json',JSON.stringify({recordings:results,desktopAndMobile:true,errors,badResponses:bad},null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
