(() => {
  const locale = document.documentElement.lang === 'bn' ? 'bn-BD' : 'en-GB';
  const iso = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  const parse = value => new Date(`${value}T12:00:00`);
  const start = document.getElementById('search-start');
  const end = document.getElementById('search-end');
  const pairs = [['.search-date-toggle', 'date-picker'], ['.search-guests-toggle', 'guest-picker']];
  const closePickers = () => pairs.forEach(([selector, id]) => {
    const button = document.querySelector(selector);
    const panel = document.getElementById(id);
    if (button && panel) { panel.hidden = true; button.setAttribute('aria-expanded', 'false'); }
  });
  pairs.forEach(([selector, id]) => {
    const button = document.querySelector(selector);
    const panel = document.getElementById(id);
    if (!button || !panel) return;
    button.addEventListener('click', () => {
      const opening = panel.hidden;
      closePickers();
      panel.hidden = !opening;
      button.setAttribute('aria-expanded', String(opening));
      if (opening) panel.querySelector('input')?.focus();
    });
    panel.querySelector('.btn')?.addEventListener('click', () => { closePickers(); button.focus(); });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.date-control, .guest-control')) closePickers();
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closePickers(); });
  if (start && end) {
    let month = parse(start.value || iso(new Date()));
    month.setDate(1);
    let choosingEnd = false;
    const display = document.getElementById('calendar-months');
    const updateSummary = () => {
      if (start.value && end.value) document.getElementById('date-summary').textContent = `${parse(start.value).toLocaleDateString(locale, {day: 'numeric', month: 'short'})} — ${parse(end.value).toLocaleDateString(locale, {day: 'numeric', month: 'short'})}`;
    };
    const render = () => {
      display.replaceChildren();
      for (let offset = 0; offset < 2; offset++) {
        const current = new Date(month.getFullYear(), month.getMonth() + offset, 1, 12);
        const section = document.createElement('section');
        const heading = document.createElement('h3');
        heading.textContent = current.toLocaleDateString(locale, {month: 'long', year: 'numeric'});
        section.append(heading);
        const grid = document.createElement('div'); grid.className = 'calendar-days';
        for (let day = 0; day < 7; day++) {
          const label = document.createElement('span');
          label.textContent = new Date(2026, 10, 2 + day).toLocaleDateString(locale, {weekday: 'narrow'});
          label.className = 'weekday'; grid.append(label);
        }
        const blanks = (current.getDay() + 6) % 7;
        for (let blank = 0; blank < blanks; blank++) grid.append(document.createElement('span'));
        const count = new Date(current.getFullYear(), current.getMonth() + 1, 0).getDate();
        for (let day = 1; day <= count; day++) {
          const date = new Date(current.getFullYear(), current.getMonth(), day, 12);
          const value = iso(date);
          const button = document.createElement('button'); button.type = 'button';
          button.textContent = day.toLocaleString(locale);
          button.setAttribute('aria-label', date.toLocaleDateString(locale, {dateStyle: 'full'}));
          button.disabled = value < start.min || (start.max && value > start.max && !choosingEnd);
          button.classList.toggle('selected', value === start.value || value === end.value);
          button.classList.toggle('in-range', value > start.value && value < end.value);
          button.addEventListener('click', () => {
            if (!choosingEnd || value <= start.value) {
              start.value = value;
              const next = new Date(date); next.setDate(next.getDate() + 1); end.value = iso(next);
              choosingEnd = true;
            } else { end.value = value; choosingEnd = false; }
            updateSummary(); render();
          });
          grid.append(button);
        }
        section.append(grid); display.append(section);
      }
    };
    document.querySelectorAll('[data-month]').forEach(button => button.addEventListener('click', () => {
      month.setMonth(month.getMonth() + Number(button.dataset.month)); render();
    }));
    [start, end].forEach(input => {
      input.addEventListener('change', () => { updateSummary(); render(); });
      input.addEventListener('invalid', () => { document.getElementById('date-picker').hidden = false; });
    });
    updateSummary(); render();
  }
  const guests = document.getElementById('search-guests');
  if (guests) {
    const update = () => { document.getElementById('guest-summary').textContent = guests.value; };
    document.querySelectorAll('[data-guest-step]').forEach(button => button.addEventListener('click', () => {
      guests.value = Math.max(Number(guests.min), Math.min(Number(guests.max), Number(guests.value) + Number(button.dataset.guestStep)));
      update();
    }));
    guests.addEventListener('input', update);
    guests.addEventListener('invalid', () => { document.getElementById('guest-picker').hidden = false; });
  }
  document.getElementById('sort-order')?.addEventListener('change', () => document.getElementById('asset-search').requestSubmit());
  document.getElementById('map-toggle')?.addEventListener('click', event => {
    const map = document.getElementById('availability-map'); map.hidden = !map.hidden;
    event.currentTarget.setAttribute('aria-expanded', String(!map.hidden));
  });
  document.getElementById('show-all-listings')?.addEventListener('click', event => {
    document.querySelectorAll('[data-extra-card]').forEach(card => { card.hidden = false; });
    event.currentTarget.hidden = true;
  });
  const unit = document.getElementById('reservation-unit');
  if (unit) {
    const from = document.getElementById('reservation-start');
    const until = document.getElementById('reservation-end');
    const slot = document.getElementById('reservation-slot');
    const update = () => {
      const option = unit.selectedOptions[0]; const hall = option.dataset.hall === '1';
      document.getElementById('reservation-slot-wrap').hidden = !hall;
      slot.required = hall;
      if (hall && !slot.value) slot.value = 'morning';
      if (!hall) slot.value = '';
      until.readOnly = hall;
      if (hall && from.value) { const date = parse(from.value); date.setDate(date.getDate() + 1); until.value = iso(date); }
      document.getElementById('reservation-guests').max = option.dataset.capacity;
    };
    unit.addEventListener('change', update); from.addEventListener('change', update); update();
  }
})();
