async(page)=>{
  const base=new URL('./',page.url()).href,errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'?match=2026-10-25&section=overview');
  await page.evaluate(()=>document.fonts.ready);
  const shell=await page.evaluate(()=>{
    const style=el=>{const s=getComputedStyle(el);return {font:s.fontFamily,weight:s.fontWeight,transform:s.textTransform,colour:s.color,background:s.backgroundColor}};
    return {heading:style(document.querySelector('h1')),body:style(document.body),button:style(document.getElementById('share')),loaded:document.fonts.check('800 24px Oxanium')&&document.fonts.check('400 14px "Instrument Sans"'),logos:[...document.querySelectorAll('.brand-lockup img')].map(el=>({src:el.currentSrc,loaded:el.complete&&el.naturalWidth>0})),iframeSrc:document.getElementById('report-frame').src};
  });
  if(!shell.heading.font.includes('Oxanium')||shell.heading.weight!=='800'||shell.heading.transform!=='uppercase'||!shell.body.font.includes('Instrument Sans')||shell.button.background!=='rgb(213, 43, 39)'||!shell.loaded||shell.logos.some(x=>!x.loaded))throw Error('Brand mismatch '+JSON.stringify(shell));
  const frame=page.frameLocator('#report-frame');
  await frame.getByRole('tab',{name:'Team strength',exact:true}).waitFor({state:'visible'});
  const inner=await frame.locator('h2').first().evaluate(el=>({font:getComputedStyle(el).fontFamily,weight:getComputedStyle(el).fontWeight}));
  if(!inner.font.includes('Oxanium')||inner.weight!=='800')throw Error('Embedded report branding mismatch');
  await page.screenshot({path:'qa/rebrand-desktop.png'});
  await frame.getByRole('tab',{name:'Team strength',exact:true}).click();
  if(await frame.locator('#strength-chart circle').count()!==271)throw Error('Strength flags changed');
  await page.getByRole('tab',{name:'Compare matches',exact:true}).click();
  await page.screenshot({path:'qa/rebrand-compare.png'});
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>innerWidth===390);
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  await page.screenshot({path:'qa/rebrand-mobile.png'});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(overflow)throw Error('Mobile overflow');
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('tab',{name:'Match report',exact:true}).click();
  if(errors.length)throw Error(errors.join('\n'));
  return {shell,inner,mobileOverflow:overflow,pageErrors:errors};
}
