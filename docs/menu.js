// Shared menu: one place to edit nav for every page.
(function(){
  const pages=[['index.html','🎬 Demo'],['performance.html','⚡ Performance'],['architecture.html','🏗️ Architecture'],['method.html','🧪 Method'],['compare.html','⚖️ vs Resolve'],['code.html','💻 Code'],['skills.html','🧰 Skills'],['recommendations.html','💡 Recommendations']];
  const cur=location.pathname.split('/').pop()||'index.html';
  const nav=document.createElement('nav');
  nav.innerHTML='<span class="brand">🟢 RVM Green Screen</span>'+pages.map(([h,t])=>`<a href="${h}" class="${h===cur?'active':''}">${t}</a>`).join('')
   +'<a href="https://github.com/rifaterdemsahin/rvm" style="margin-left:auto">🐙 GitHub</a>';
  document.body.prepend(nav);
})();
