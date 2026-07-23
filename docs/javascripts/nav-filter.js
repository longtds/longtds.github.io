// 访问 /ops 页面时,左侧导航仅保留"运维实践"部分
(function() {
  'use strict';

  var OPS_KEYWORD = '运维实践';

  function filterNav() {
    var path = window.location.pathname;
    // 判定:路径含 /ops/ 或正好是 /ops 或 /ops/ 结尾
    var isOpsPage = /\/ops\/?$/.test(path) || /\/ops\//.test(path);

    var items = document.querySelectorAll('.md-nav__item--nested');
    items.forEach(function(item) {
      var link = item.querySelector('.md-nav__link');
      if (!link) return;

      var text = link.textContent.trim();
      var isOps = text === OPS_KEYWORD;

      item.style.display = isOpsPage && !isOps ? 'none' : '';
    });
  }

  // 页面加载后执行
  if (document.readyState === 'complete') {
    filterNav();
  } else {
    window.addEventListener('load', filterNav);
  }

  // MkDocs 使用 History API 切换页面,监听 URL 变化
  var lastUrl = location.href;
  var observer = new MutationObserver(function() {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      setTimeout(filterNav, 100);
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
