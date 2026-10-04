/* =========================================================
   assets/story.js
   Logika klien Web Story (dimuat & disuntikkan oleh app.py)
   1. Animasi kemunculan SEKALI SAJA (reveal-once) berbasis memori "sudah dilihat"
   2. Animasi saat filter / dropdown diganti (morph titik, bar tumbuh, cascade, fokus)
   3. Penanda bab yang selalu terlihat (chapter indicator) + scroll-spy + progress bar
   ========================================================= */
(function () {
    'use strict';

    let P, D;
    try { P = window.parent; D = P.document; } catch (e) { return; }
    if (!D || !D.body) return;

    /* ---------------------------------------------------------
       0. STATE PERSISTEN
       Disimpan di window induk agar tidak hilang ketika iframe skrip
       dimuat ulang atau Streamlit mengganti node DOM.
       --------------------------------------------------------- */
    const ST = (P.__storyState = P.__storyState || {});
    ST.seen = ST.seen || new Set();   // kunci elemen yang sudah pernah dianimasikan
    ST.sigs = ST.sigs || {};          // tanda tangan (signature) filter terakhir per grafik
    ST.snaps = ST.snaps || {};        // snapshot posisi titik scatter per grafik
    ST.pending = ST.pending || {};    // permintaan morph yang menunggu grafik selesai digambar
    ST.shown = ST.shown || {};        // bab yang sudah pernah memunculkan toast
    ST.lastText = ST.lastText || {};  // teks takeaway terakhir per kunci
    ST.dir = ST.dir || 'down';        // arah scroll terakhir
    ST.lastTop = ST.lastTop || 0;

    if (typeof P.__storyCleanup === 'function') { try { P.__storyCleanup(); } catch (e) {} }
    const cleanups = [];
    P.__storyCleanup = () => { cleanups.forEach(fn => { try { fn(); } catch (e) {} }); };

    // Timer & rAF memakai window induk supaya tetap hidup walau iframe dibongkar
    const setT = (fn, ms) => P.setTimeout(fn, ms);
    const clearT = (id) => P.clearTimeout(id);
    const raf = (fn) => P.requestAnimationFrame(fn);
    const reduceMotion = !!(P.matchMedia && P.matchMedia('(prefers-reduced-motion: reduce)').matches);

    const getScroller = () =>
        D.querySelector('[data-testid="stMain"]') ||
        D.querySelector('section.main') ||
        D.querySelector('.main') ||
        D.documentElement;

    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const hash = (str) => {
        let h = 5381;
        for (let i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) | 0;
        return (h >>> 0).toString(36);
    };
    const inView = (el) => {
        const r = el.getBoundingClientRect();
        const vh = P.innerHeight || 800;
        return r.bottom > 40 && r.top < vh - 40;
    };

    const CHAPTERS = [
        ['bab-1', 'Lanskap Makro'],
        ['bab-2', 'Dimensi Spasial'],
        ['bab-3', 'Dimensi Multivariat'],
        ['bab-4', 'Dimensi Hierarkis'],
        ['bab-5', 'Sintesis & Wawasan']
    ];
    const WIDGET_SEL = '[data-testid="stPlotlyChart"], [data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stMetric"], .chart-takeaway';

    /* ---------------------------------------------------------
       1. ELEMEN UI TETAP: progress bar, back-to-top, toast & indikator bab
       --------------------------------------------------------- */
    let progBar = D.getElementById('reading-progress-bar');
    if (!progBar) {
        progBar = D.createElement('div');
        progBar.id = 'reading-progress-bar';
        D.body.appendChild(progBar);
    }

    let bttBtn = D.getElementById('back-to-top-btn');
    if (!bttBtn) {
        bttBtn = D.createElement('button');
        bttBtn.id = 'back-to-top-btn';
        bttBtn.innerHTML = '↑';
        bttBtn.title = 'Kembali ke atas';
        bttBtn.addEventListener('click', () => getScroller().scrollTo({ top: 0, behavior: 'smooth' }));
        D.body.appendChild(bttBtn);
    }

    let ind = D.getElementById('chapter-indicator');
    if (!ind) {
        ind = D.createElement('div');
        ind.id = 'chapter-indicator';
        D.body.appendChild(ind);
    }
    let indChapter = -1;
    function setIndicator(idx, visible) {
        if (visible && indChapter !== idx) {
            indChapter = idx;
            const dots = CHAPTERS.map((c, i) =>
                '<i class="' + (i < idx ? 'on' : (i === idx ? 'cur' : '')) + '"></i>').join('');
            ind.innerHTML =
                '<span class="ci-num">' + (idx + 1) + '</span>' +
                '<span class="ci-text"><span class="ci-k">BAB ' + (idx + 1) + ' / ' + CHAPTERS.length + '</span>' +
                '<span class="ci-n">' + esc(CHAPTERS[idx][1]) + '</span></span>' +
                '<span class="ci-dots">' + dots + '</span>';
        }
        ind.classList.toggle('show', !!visible);
    }

    function showChapterPill(idx) {
        let t = D.getElementById('chapter-pill');
        if (!t) {
            t = D.createElement('div');
            t.id = 'chapter-pill';
            D.body.appendChild(t);
        }
        t.innerHTML = '<div class="cp-num">' + (idx + 1) + '</div>' +
            '<div><div class="cp-label">Sekarang membaca · BAB ' + (idx + 1) + '</div>' +
            '<div class="cp-name">' + esc(CHAPTERS[idx][1]) + '</div></div>';
        t.classList.remove('show');
        void t.offsetWidth;
        t.classList.add('show');
        clearT(t._hide);
        t._hide = setT(() => t.classList.remove('show'), 3100);
    }

    /* ---------------------------------------------------------
       2. SCROLL-SPY, ARAH SCROLL, PROGRESS
       --------------------------------------------------------- */
    function updateSpy() {
        const sc = getScroller();
        const top = sc.scrollTop || D.documentElement.scrollTop || 0;
        const sh = sc.scrollHeight || D.documentElement.scrollHeight || 1;
        const ch = sc.clientHeight || D.documentElement.clientHeight || 1;
        const vh = P.innerHeight || 800;

        progBar.style.width = Math.min(100, Math.max(0, (top / Math.max(1, sh - ch)) * 100)) + '%';
        bttBtn.classList.toggle('visible', top > 350);

        // bab aktif untuk sidebar & indikator
        let active = 0;
        CHAPTERS.forEach((c, i) => {
            const el = D.getElementById(c[0]);
            if (el && el.getBoundingClientRect().top <= vh * 0.45) active = i;
        });
        const activeId = CHAPTERS[active][0];
        D.querySelectorAll('.toc-link').forEach(l =>
            l.classList.toggle('active', (l.getAttribute('href') || '') === '#' + activeId));

        // sub-bab (Bab 3)
        let activeSub = null;
        if (activeId === 'bab-3') {
            ['bab-3-1', 'bab-3-2', 'bab-3-3', 'bab-3-4'].forEach(sid => {
                const el = D.getElementById(sid);
                if (el && el.getBoundingClientRect().top <= vh * 0.5) activeSub = sid;
            });
        }
        D.querySelectorAll('.subnav-pill').forEach(p =>
            p.classList.toggle('active', !!activeSub && p.getAttribute('href') === '#' + activeSub));

        // indikator bab permanen: muncul setelah Bab 1 mulai terlihat
        const b1 = D.getElementById('bab-1');
        setIndicator(active, !!b1 && b1.getBoundingClientRect().top <= vh * 0.6);

        // pengaman: pembuka bab yang sudah melewati batas bawah layar tetapi belum tampil dipaksa tampil
        D.querySelectorAll('.chapter-opener.reveal:not(.revealed)').forEach(el => {
            if (el.getBoundingClientRect().top <= vh * 0.8) {
                io.unobserve(el);
                ST.seen.add(el._storyKey || keyOf(el));
                revealInstant(el);
            }
        });

        // toast pergantian bab (sekali per bab)
        let entered = 0;
        CHAPTERS.forEach((c, i) => {
            const el = D.getElementById(c[0]);
            if (el && el.getBoundingClientRect().top <= vh * 0.8) entered = i;
        });
        if (ST.lastChapter === undefined) {
            ST.lastChapter = entered;
            ST.shown[entered] = true;
        } else if (entered !== ST.lastChapter) {
            ST.lastChapter = entered;
            if (!ST.shown[entered]) {
                ST.shown[entered] = true;
                setT(() => showChapterPill(entered), 200);
            }
        }
    }

    const onScroll = () => {
        const sc = getScroller();
        const top = sc.scrollTop || D.documentElement.scrollTop || 0;
        if (Math.abs(top - ST.lastTop) > 2) {
            ST.dir = top > ST.lastTop ? 'down' : 'up';
            ST.lastTop = top;
        }
        updateSpy();
    };
    D.addEventListener('scroll', onScroll, { passive: true, capture: true });
    cleanups.push(() => D.removeEventListener('scroll', onScroll, true));

    // Klik tautan navigasi bab / sub-bab -> scroll halus
    const onNavClick = (e) => {
        const a = e.target.closest && (e.target.closest('a[href^="#bab-"]') || e.target.closest('.toc-link'));
        if (!a) return;
        const id = (a.getAttribute('href') || '').replace('#', '');
        const target = id && D.getElementById(id);
        if (!target) return;
        e.preventDefault();
        e.stopPropagation();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (/^bab-[0-9]$/.test(id)) {
            D.querySelectorAll('.toc-link').forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + id));
        }
    };
    D.addEventListener('click', onNavClick, true);
    cleanups.push(() => D.removeEventListener('click', onNavClick, true));

    /* ---------------------------------------------------------
       3. REVEAL-ONCE: animasi kemunculan hanya pada pertama kali terlihat
          saat scroll ke bawah. Status disimpan per KUNCI (bukan per node DOM),
          sehingga node yang diganti Streamlit tidak mengulang animasi.
       --------------------------------------------------------- */
    function anchorsList() { return Array.from(D.querySelectorAll('[id^="bab-"]')); }
    function anchorOf(n, anchors) {
        let a = null;
        for (const x of anchors) {
            if (x.compareDocumentPosition(n) & 4) a = x; else break;
        }
        return a;
    }

    // Kunci identitas: id -> (tipe widget + bab + urutan di bab) -> (kelas + hash teks)
    function keyOf(el) {
        if (el.id) return 'id:' + el.id;
        const tid = el.getAttribute('data-testid');
        if (tid || el.classList.contains('chart-takeaway')) {
            const sel = tid ? '[data-testid="' + tid + '"]' : '.chart-takeaway';
            const anchors = anchorsList();
            const mine = anchorOf(el, anchors);
            const aid = mine ? mine.id : 'top';
            let idx = 0;
            const all = D.querySelectorAll(sel);
            for (const n of all) {
                if (n === el) break;
                const a = anchorOf(n, anchors);
                if ((a ? a.id : 'top') === aid) idx++;
            }
            return sel + '@' + aid + '#' + idx;
        }
        const cls = Array.from(el.classList).filter(c => c !== 'reveal' && c !== 'revealed').join('.');
        const txt = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160);
        return 'rv:' + cls + ':' + hash(txt);
    }

    const animateCountUp = (el) => {
        if (el._counted) return;
        el._counted = true;
        const text = el.innerText.trim();
        const match = text.match(/([0-9]+[.,]?[0-9]*)/);
        if (!match) return;
        const target = parseFloat(match[0].replace(',', '.'));
        if (isNaN(target)) return;
        const isDecimal = text.includes('.') || text.includes(',');
        const t0 = performance.now();
        const step = (now) => {
            const p = Math.min((now - t0) / 1100, 1);
            const v = target * (1 - Math.pow(1 - p, 3));
            el.innerHTML = text.replace(match[0], isDecimal ? v.toFixed(2) : Math.round(v).toLocaleString());
            if (p < 1) raf(step); else el.innerHTML = text;
        };
        raf(step);
    };

    function revealAnimated(el) {
        if (el.classList.contains('reveal')) {
            el.classList.add('revealed');
            el.querySelectorAll('.stis-card-value').forEach(animateCountUp);
        } else {
            el.setAttribute('data-seen', '1');
        }
    }
    // Tampil seketika tanpa transisi (untuk elemen yang sudah pernah dilihat / scroll ke atas)
    function revealInstant(el) {
        el.classList.add('no-anim');
        if (el.classList.contains('reveal')) {
            el.classList.add('revealed');
            el.querySelectorAll('.stis-card-value').forEach(v => { v._counted = true; });
        } else {
            el.setAttribute('data-seen', '1');
        }
        raf(() => raf(() => el.classList.remove('no-anim')));
    }

    const io = new P.IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            io.unobserve(el);
            ST.seen.add(el._storyKey || keyOf(el));
            // Animasi hanya untuk kemunculan pertama saat membaca ke bawah
            if (ST.dir === 'up' || reduceMotion) revealInstant(el); else revealAnimated(el);
        });
    }, { threshold: 0.12 });
    cleanups.push(() => io.disconnect());

    function scanReveal() {
        D.querySelectorAll('.reveal:not(.revealed), ' + WIDGET_SEL).forEach(el => {
            if (el.classList.contains('revealed') || el.hasAttribute('data-seen') || el._storyWatched) return;
            el._storyWatched = true;
            el._storyKey = keyOf(el);
            if (ST.seen.has(el._storyKey)) revealInstant(el);
            else io.observe(el);
        });
    }

    // Kedipan lembut pada kotak takeaway ketika isinya berubah akibat filter
    function scanTakeaways() {
        D.querySelectorAll('.chart-takeaway').forEach(el => {
            const k = el._storyKey;
            if (!k) return;
            const h = hash((el.textContent || '').trim());
            const prev = (el._txt !== undefined) ? el._txt : ST.lastText[k];
            el._txt = h;
            ST.lastText[k] = h;
            if (prev !== undefined && prev !== h && el.hasAttribute('data-seen') && inView(el) && !reduceMotion) {
                el.classList.remove('ta-updated');
                void el.offsetWidth;
                el.classList.add('ta-updated');
                setT(() => el.classList.remove('ta-updated'), 1300);
            }
        });
    }

    /* ---------------------------------------------------------
       4. ANIMASI SAAT FILTER / DROPDOWN BERUBAH
          app.py menaruh penanda tersembunyi  <div class="chart-sig" data-chart data-sig data-fx>
          tepat sebelum tiap grafik. Ketika data-sig berubah (filter berganti),
          efek yang sesuai dengan data-fx dimainkan pada grafik di bawahnya:
            morph   : titik bergeser/mengubah ukuran dari posisi lama ke baru (scatter)
            grow    : batang tumbuh dari sumbu (bar chart)
            cascade : irisan muncul berurutan (treemap / sunburst)
            focus   : redup + blur lalu menajam (peta, tabel)
       --------------------------------------------------------- */
    const FX_TARGET_SEL = '[data-testid="stPlotlyChart"], [data-testid="stDataFrame"]';
    const EASE = 'cubic-bezier(0.22, 1, 0.36, 1)';

    const markerEl = (name) => D.querySelector('.chart-sig[data-chart="' + name + '"]');
    const rootOf = (m) => m.closest('[data-testid="stVerticalBlock"]') || D.body;

    function findTarget(m) {
        const box = m.closest('[data-testid="stElementContainer"], .element-container') || m.parentElement;
        let n = box ? box.nextElementSibling : null;
        for (let i = 0; i < 4 && n; i++, n = n.nextElementSibling) {
            const t = n.matches(FX_TARGET_SEL) ? n : n.querySelector(FX_TARGET_SEL);
            if (t) return t;
        }
        return null;
    }
    const innerOf = (t) => t.querySelector('.js-plotly-plot') || t.firstElementChild || t;

    // Tunggu sampai DOM di sekitar grafik "tenang" setelah Streamlit memperbarui figure
    function afterSettle(m, cb, opts) {
        const o = Object.assign({ minWait: 240, quiet: 90, maxWait: 1500 }, opts || {});
        const t0 = Date.now();
        let last = t0, mutated = false;
        const obs = new P.MutationObserver(() => { last = Date.now(); mutated = true; });
        obs.observe(rootOf(m), { childList: true, subtree: true, attributes: true });
        (function poll() {
            const now = Date.now();
            if ((now - t0 >= o.minWait && now - last >= o.quiet && mutated) || now - t0 >= o.maxWait) {
                obs.disconnect();
                cb();
            } else {
                setT(poll, 40);
            }
        })();
    }

    function sheen(t) {
        t.classList.add('fx-sheen');
        setT(() => t.classList.remove('fx-sheen'), 1050);
    }
    function clearOut(t) {
        t.classList.remove('fx-out');
        t.querySelectorAll('.fx-out').forEach(e => e.classList.remove('fx-out'));
    }
    function snapBack(el) {
        el.classList.add('fx-snap');
        el.classList.remove('fx-out');
        raf(() => raf(() => el.classList.remove('fx-snap')));
    }

    /* --- morph (scatter): FLIP berbasis snapshot posisi titik --- */
    function readPoints(t) {
        let best = [];
        t.querySelectorAll('.scatterlayer .trace').forEach(tr => {
            const pts = Array.from(tr.querySelectorAll('.points path.point'));
            if (pts.length > best.length) best = pts;
        });
        return best;
    }
    function pointInfo(el) {
        const tr = (el.getAttribute('transform') || '').match(/translate\(\s*([-+\d.eE]+)[\s,]+([-+\d.eE]+)\s*\)/);
        const rr = (el.getAttribute('d') || '').match(/^M\s*([-+\d.eE]+)/);
        return {
            x: tr ? parseFloat(tr[1]) : NaN,
            y: tr ? parseFloat(tr[2]) : NaN,
            r: rr ? Math.abs(parseFloat(rr[1])) : NaN,
            fill: el.style.fill || '',
            op: el.style.opacity || ''
        };
    }
    const pointsSig = (arr) => arr.map(p => [p.x, p.y, p.r, p.fill, p.op].join(',')).join(';');

    function snapshotAll() {
        D.querySelectorAll('.chart-sig[data-fx="morph"]').forEach(m => {
            const name = m.getAttribute('data-chart');
            const p = ST.pending[name];
            if (p && Date.now() - p.t < 4000) return;   // jangan timpa snapshot lama saat menunggu morph
            const t = findTarget(m);
            if (!t) return;
            const pts = readPoints(t).map(pointInfo);
            if (pts.length) ST.snaps[name] = pts;
        });
    }
    let snapTimer = null;
    function scheduleSnapshot() {
        clearT(snapTimer);
        snapTimer = setT(snapshotAll, 700);
    }

    function playMorph(t, els, oldPts, newPts) {
        let moved = false;
        els.forEach((el, i) => {
            const o = oldPts[i], n = newPts[i];
            if (!o || !n || !isFinite(o.x) || !isFinite(n.x)) return;
            const ratio = (isFinite(o.r) && isFinite(n.r) && n.r > 0) ? o.r / n.r : 1;
            const dist = Math.abs(o.x - n.x) + Math.abs(o.y - n.y);
            if (dist < 0.5 && Math.abs(ratio - 1) < 0.02) return;
            if (dist >= 0.5) moved = true;
            el.animate([
                { transform: 'translate(' + o.x + 'px, ' + o.y + 'px) scale(' + ratio + ')' },
                { transform: 'translate(' + n.x + 'px, ' + n.y + 'px) scale(1)' }
            ], { duration: 850, delay: Math.min(i, 60) * 8, easing: EASE, fill: 'backwards' });
        });
        if (moved) {
            // garis tren, garis rata-rata & anotasi muncul perlahan agar tidak "melompat"
            t.querySelectorAll('.scatterlayer path.js-line, .shapelayer path, g.annotation').forEach(e => {
                e.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 650, delay: 250, easing: 'ease-out', fill: 'backwards' });
            });
        }
    }

    function resolveMorph(name, tries, visible) {
        const p = ST.pending[name];
        if (!p) return;
        const m = markerEl(name);
        const t = m && findTarget(m);
        if (!t) { delete ST.pending[name]; return; }
        const els = readPoints(t);
        const now = els.map(pointInfo);
        const old = ST.snaps[name];
        const changed = !old || old.length !== now.length || pointsSig(old) !== pointsSig(now);
        if (!changed && tries < 4) {
            setT(() => resolveMorph(name, tries + 1, visible), 220);
            return;
        }
        delete ST.pending[name];
        if (changed && old && old.length === now.length && visible && !reduceMotion) playMorph(t, els, old, now);
        if (now.length) ST.snaps[name] = now;
    }

    /* --- grow (bar) & cascade (treemap/sunburst) --- */
    function playGrow(t) {
        t.querySelectorAll('.barlayer .point path').forEach((b, i) => {
            b.style.transformBox = 'fill-box';
            b.style.transformOrigin = '0 50%';
            const a = b.animate([{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }],
                { duration: 720, delay: i * 18, easing: EASE, fill: 'backwards' });
            const done = () => { b.style.transformBox = ''; b.style.transformOrigin = ''; };
            a.onfinish = done; a.oncancel = done;
        });
        t.querySelectorAll('.barlayer .point text').forEach((x, i) => {
            x.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 450, delay: 320 + i * 18, fill: 'backwards' });
        });
    }
    function playCascade(t) {
        t.querySelectorAll('.slice').forEach((s, i) => {
            s.animate([{ opacity: 0 }, { opacity: 1 }],
                { duration: 560, delay: Math.min(i, 60) * 14, easing: 'ease-out', fill: 'backwards' });
        });
    }

    function triggerFx(name, fx) {
        const m = markerEl(name);
        if (!m) return;
        const t = findTarget(m);
        if (!t) return;
        const visible = t.hasAttribute('data-seen') && inView(t);

        if (fx === 'morph') {
            ST.pending[name] = { t: Date.now() };
            if (visible && !reduceMotion) sheen(t);
            afterSettle(m, () => resolveMorph(name, 0, visible));
            return;
        }
        if (!visible || reduceMotion) return;

        const inner = innerOf(t);
        inner.classList.add('fx-t', 'fx-out');
        setT(() => clearOut(t), 2600); // jaring pengaman: jangan pernah tertinggal redup

        if (fx === 'focus') {
            setT(() => { clearOut(t); sheen(t); }, 280);
            return;
        }
        afterSettle(m, () => {
            const t2 = findTarget(m) || t;
            if (fx === 'grow') playGrow(t2); else if (fx === 'cascade') playCascade(t2);
            [inner, innerOf(t2)].forEach(snapBack);
            sheen(t2);
        }, { minWait: 220 });
    }

    function scanMarkers() {
        D.querySelectorAll('.chart-sig').forEach(m => {
            const name = m.getAttribute('data-chart');
            if (!name) return;
            const sig = m.getAttribute('data-sig');
            const prev = ST.sigs[name];
            ST.sigs[name] = sig;
            if (prev === undefined || prev === sig) return; // render pertama / tidak ada perubahan
            triggerFx(name, m.getAttribute('data-fx') || 'focus');
        });
    }

    /* ---------------------------------------------------------
       5. PENGAMAT PERUBAHAN DOM STREAMLIT
       --------------------------------------------------------- */
    let spyQueued = false;
    function onMutate() {
        // Sinkron (sebelum paint) agar node pengganti tidak sempat berkedip tersembunyi
        scanReveal();
        scanMarkers();
        scanTakeaways();
        scheduleSnapshot();
        if (!spyQueued) {
            spyQueued = true;
            raf(() => { spyQueued = false; updateSpy(); });
        }
    }
    const mo = new P.MutationObserver(onMutate);
    mo.observe(D.body, { childList: true, subtree: true });
    cleanups.push(() => mo.disconnect());

    D.documentElement.classList.add('story-js');
    onMutate();
    updateSpy();
})();
