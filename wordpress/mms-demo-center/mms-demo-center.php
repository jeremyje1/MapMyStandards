<?php
/**
 * Plugin Name: MMS Demo Center
 * Description: Adds a [mms_demo_center] shortcode that renders a self-contained Demo Center (styles inlined) for Elementor/WordPress.
 * Version: 1.0.0
 * Author: MapMyStandards
 */

if (!defined('ABSPATH')) { exit; }

function mms_demo_center_shortcode($atts = []) {
    $assets_base = plugins_url('assets', __FILE__);
    ob_start();
    ?>
    <div id="mms-demo-center" style="background:#fff7ed;border:1px solid #fdba74;border-radius:12px;padding:16px;max-width:900px;margin:16px auto;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111827;">
        <h3 style="margin:0 0 8px 0;color:#7c2d12;font-size:18px;font-weight:700;">🧪 Demo Center</h3>
        <p style="margin:0 0 12px 0;color:#7c2d12;font-size:14px;">Run the local demo: imports a sample standard and uploads the demo evidence pack to your running API.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin-bottom:8px;">
            <a href="https://raw.githubusercontent.com/jeremyje1/MapMyStandards/HEAD/examples/demo_pack/mms_demo_evidence_pack.zip" target="_blank" style="color:#1d4ed8;text-decoration:underline;">Download Demo Pack (zip)</a>
            <a href="#" onclick="event.preventDefault(); alert('Standards JSON is embedded in this demo widget.');" style="color:#1d4ed8;text-decoration:underline;">View Standards JSON</a>
            <a href="https://github.com/jeremyje1/MapMyStandards/tree/HEAD/examples/demo_pack" target="_blank" style="color:#1d4ed8;text-decoration:underline;">Demo Files Repo</a>
        </div>
        <label style="display:block;font-size:12px;color:#7c2d12;margin-bottom:6px;">API Base URL (auto-detected). Change if needed and Save.</label>
        <div style="display:flex;gap:8px;margin-bottom:8px;">
            <input id="mms-demo-base" placeholder="https://api.mapmystandards.ai" style="flex:1;border:1px solid #fdba74;border-radius:6px;padding:8px 10px;font-size:14px;" />
            <button id="mms-demo-save" style="background:#b45309;color:white;border:none;padding:8px 10px;border-radius:6px;font-weight:600;cursor:pointer;">Save</button>
            <button id="mms-run-demo" style="background:#2563eb;color:white;border:none;padding:8px 10px;border-radius:6px;font-weight:600;cursor:pointer;">Run Demo</button>
        </div>
        <button id="mms-clear-log" style="background:#f3f4f6;color:#111827;border:1px solid #e5e7eb;padding:6px 10px;border-radius:6px;font-size:12px;cursor:pointer;">Clear Log</button>
        <pre id="mms-demo-log" style="margin-top:8px;background:#fff;border:1px solid #fed7aa;border-radius:8px;padding:8px;font-size:12px;max-height:220px;overflow:auto;"></pre>
    </div>
        <script type="application/json" id="mms-standards-json">
        {
            "metadata": {"key":"SACSCOC_2024_DEMO","name":"SACSCOC Principles of Accreditation (Demo Subset)","version":"2024.demo","publisher":"SACSCOC (Demo subset for testing)","notes":"Paraphrased demo subset for testing MapMyStandards import. NOT official text."},
            "items": [
                {"code":"CR 1.1","title":"Institutional Integrity (Core Requirement)","description":"The institution operates with integrity and consistent ethical standards across governance, academics, and operations. (Paraphrased demo text)","level":1,"parent":null,"weight":1.0,
                 "evidenceExamples":["Board minutes referencing ethics policy review","Annual compliance attestation documents"],
                 "rubric":{"levels":["Insufficient","Developing","Meets","Exceeds"],
                                     "anchors":["Policies absent or not applied","Policies exist with inconsistent application","Policies exist and are consistently applied","Policies are exemplary and externally benchmarked"]}},
                {"code":"7.1","title":"Institutional Planning","description":"The institution engages in ongoing, comprehensive, and integrated planning processes. (Paraphrased demo text)","level":1,"parent":null,"weight":1.0,
                 "evidenceExamples":["Strategic plan with KPIs","Annual planning cycle calendar"],
                 "rubric":{"levels":["Insufficient","Developing","Meets","Exceeds"]}},
                {"code":"8.2.a","title":"Student Achievement","description":"The institution identifies, evaluates, and publishes goals and outcomes for student achievement. (Paraphrased demo text)","level":2,"parent":"7.1","weight":1.0,
                 "evidenceExamples":["Student achievement dashboard or fact book","Program-level outcomes with thresholds"],
                 "rubric":{"levels":["Insufficient","Developing","Meets","Exceeds"]}},
                {"code":"9.1","title":"Program Length","description":"The institution ensures program length is appropriate to the degree level. (Paraphrased demo text)","level":1,"parent":null,"weight":1.0},
                {"code":"10.4","title":"Academic Governance","description":"The institution demonstrates effective academic governance and faculty role in curriculum and assessment. (Paraphrased demo text)","level":1,"parent":null,"weight":1.0}
            ]
        }
        </script>
        <script>(function(){
        const logEl=document.getElementById('mms-demo-log');
        const baseInput=document.getElementById('mms-demo-base');
        const saveBtn=document.getElementById('mms-demo-save');
        const runBtn=document.getElementById('mms-run-demo');
        const clearBtn=document.getElementById('mms-clear-log');
        if(!logEl||!baseInput||!runBtn) return;
        function detectDefaultBase(){
            const saved=localStorage.getItem('mms_demo_base'); if(saved) return saved;
            if(location.hostname.endsWith('mapmystandards.ai')) return 'https://api.mapmystandards.ai';
            return location.origin||'http://localhost:3000';
        }
        function setBase(){ baseInput.placeholder=detectDefaultBase(); baseInput.value=localStorage.getItem('mms_demo_base')||''; }
        function log(msg,data){ const t=new Date().toISOString(); logEl.textContent += `[${t}] ${msg}` + (data?`\n${typeof data==='string'?data:JSON.stringify(data,null,2)}`:'') + '\n\n'; logEl.scrollTop=logEl.scrollHeight; }
        async function postJson(url,payload){ const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); const tx=await res.text(); let body; try{body=JSON.parse(tx);}catch{body=tx;} if(!res.ok) throw new Error(`HTTP ${res.status}: ${tx}`); return body; }
        async function postFile(url,blob,filename){ const form=new FormData(); form.append('file',blob,filename); const res=await fetch(url,{method:'POST',body:form}); const tx=await res.text(); let body; try{body=JSON.parse(tx);}catch{body=tx;} if(!res.ok) throw new Error(`HTTP ${res.status}: ${tx}`); return body; }
        async function runDemo(){
            const base=(baseInput.value||detectDefaultBase()).replace(/\/$/,''); localStorage.setItem('mms_demo_base',base); log(`Using API base: ${base}`);
            try{
                                log('Loading embedded standards template...');
                                const jsonEl=document.getElementById('mms-standards-json');
                                const std=JSON.parse(jsonEl.textContent || '{}');
                log('Importing standards ...'); const imp=await postJson(`${base}/api/standards/import`, std); log('Standards imported:', imp);
                                // Try to fetch zip; if unavailable, fall back to generated CSV
                                let uploaded=false;
                                try{
                                        log('Attempting to fetch demo evidence pack (zip)...');
                                        const zipResp=await fetch('https://raw.githubusercontent.com/jeremyje1/MapMyStandards/HEAD/examples/demo_pack/mms_demo_evidence_pack.zip');
                                        if(!zipResp.ok) throw new Error('Zip not available');
                                        const zipBlob=await zipResp.blob();
                                        log('Uploading evidence pack (zip) ...'); const up=await postFile(`${base}/api/upload`, zipBlob, 'mms_demo_evidence_pack.zip'); log('Upload done:', up);
                                        uploaded=true;
                                }catch(e){
                                        log('Zip not accessible, generating CSV fallback...');
                                        const csv='filename,content\npolicy.pdf,"Policy document excerpt for CR 1.1"\nplanning.pdf,"Planning KPIs for 7.1"\nachievement.csv,"Student achievement data for 8.2.a"\n';
                                        const blob=new Blob([csv],{type:'text/csv'});
                                        const up=await postFile(`${base}/api/upload`, blob, 'demo_evidence_fallback.csv');
                                        log('CSV fallback uploaded:', up);
                                        uploaded=true;
                                }
                                if(!uploaded) log('No evidence uploaded.');
                try{ log('Triggering mapping ...'); const mapRes=await fetch(`${base}/api/map`,{method:'POST'}); log('Mapping result:', await mapRes.text()); }catch(e){ log('Map endpoint not available (continuing).'); }
                try{ log('Running gaps ...'); const gapsRes=await fetch(`${base}/api/gaps/run`,{method:'POST'}); log('Gaps result:', await gapsRes.text()); }catch(e){ log('Gaps endpoint not available (continuing).'); }
                log('Demo finished.');
            }catch(err){ log('Demo failed:', String(err)); }
        }
        setBase();
        saveBtn&&saveBtn.addEventListener('click',()=>{ const v=baseInput.value||detectDefaultBase(); localStorage.setItem('mms_demo_base',v); log(`Saved API base: ${v}`); });
        runBtn.addEventListener('click', runDemo);
        clearBtn&&clearBtn.addEventListener('click',()=>{ logEl.textContent=''; });
    })();</script>
    <?php
    return ob_get_clean();
}
add_shortcode('mms_demo_center', 'mms_demo_center_shortcode');
