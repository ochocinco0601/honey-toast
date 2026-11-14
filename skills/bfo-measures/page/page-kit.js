// Include with <script src="/page-kit.js"></script>. Clicking any element with data-done sends
// every named input, select and textarea; the outcome is shown in each [data-status] element.
(function () {
  var SENT = 'Saved at {time}. If Claude Code does not reply in the chat shortly, say "read it" there. You can change anything and send again.';

  function collect() {
    var out = {}, counts = {};
    var els = document.querySelectorAll('input[name], select[name], textarea[name]');
    Array.prototype.forEach.call(els, function (el) {
      if (el.type !== 'radio' && el.type !== 'checkbox') counts[el.name] = (counts[el.name] || 0) + 1;
    });
    Array.prototype.forEach.call(els, function (el) {
      var k = el.name;
      if (el.type === 'radio') {
        if (!(k in out)) out[k] = null;
        if (el.checked) out[k] = el.value;
      } else if (el.type === 'checkbox') {
        if (!(k in out)) out[k] = [];
        if (el.checked) out[k].push(el.value);
      } else if (counts[k] > 1) {
        if (!(k in out)) out[k] = [];
        out[k].push(el.value);
      } else {
        out[k] = el.value;
      }
    });
    return out;
  }

  function say(text) {
    Array.prototype.forEach.call(document.querySelectorAll('[data-status]'), function (el) { el.textContent = text; });
  }

  function send(btn) {
    if (btn) btn.disabled = true;
    fetch('/answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: document.title, submittedAt: new Date().toISOString(), answers: collect() })
    }).then(function (r) {
      say(r.ok ? SENT.replace('{time}', new Date().toLocaleTimeString())
               : 'Not accepted (' + r.status + '). Say "read it" in the chat instead.');
    }).catch(function () {
      say('Could not reach Claude Code from this page. Say "read it" in the chat instead.');
    }).then(function () { if (btn) btn.disabled = false; });
  }

  if (typeof document !== 'undefined') {
    // A form must never submit the page itself: that reloads it and puts the answers in the URL.
    document.addEventListener('submit', function (e) { e.preventDefault(); }, true);
    document.addEventListener('click', function (e) {
      var btn = e.target && e.target.closest && e.target.closest('[data-done]');
      if (!btn) return;
      e.preventDefault();
      send(btn);
    });
  }

  if (typeof module !== 'undefined') module.exports = { collect: collect, SENT: SENT };
})();
