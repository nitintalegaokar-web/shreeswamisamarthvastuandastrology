(() => {
  'use strict';
  const tabs = [...document.querySelectorAll('.account-tabs [role="tab"]')];
  const panels = tabs.map((tab) => document.querySelector(`#${tab.getAttribute('aria-controls')}`));
  const selectTab = (selected) => {
    tabs.forEach((tab, index) => {
      const active = tab === selected;
      tab.setAttribute('aria-selected', String(active));
      panels[index].hidden = !active;
    });
    selected.focus();
  };
  tabs.forEach((tab) => tab.addEventListener('click', () => selectTab(tab)));
  tabs.forEach((tab) => tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft','ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const next = (tabs.indexOf(tab) + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    selectTab(tabs[next]);
  }));

  document.querySelectorAll('[data-password-toggle]').forEach((button) => button.addEventListener('click', () => {
    const input = document.querySelector(`#${button.dataset.passwordToggle}`);
    const showing = input.type === 'text';
    input.type = showing ? 'password' : 'text';
    button.textContent = showing ? 'Show' : 'Hide';
    button.setAttribute('aria-label', `${showing ? 'Show' : 'Hide'} password`);
  }));

  const showStatus = (id, message, type) => {
    const status = document.querySelector(`#${id}`);
    status.textContent = message;
    status.dataset.type = type;
  };
  document.querySelector('#customer-login').addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    showStatus('login-status','Secure customer sign-in will be connected when the online service is published. No information was sent.','notice');
  });
  document.querySelector('#forgot-password').addEventListener('click', () => showStatus('login-status','Password recovery will be available after the secure customer service is connected.','notice'));
  document.querySelector('#customer-register').addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const password = document.querySelector('#register-password');
    const confirmation = document.querySelector('#confirm-password');
    const mobile = document.querySelector('#mobile');
    const postalCode = document.querySelector('#postal-code');
    mobile.setCustomValidity(mobile.value.replace(/\D/g,'').length >= 8 ? '' : 'Enter a valid mobile or WhatsApp number.');
    postalCode.setCustomValidity(/^[A-Za-z0-9 -]{3,12}$/.test(postalCode.value) ? '' : 'Enter a valid PIN or postal code.');
    confirmation.setCustomValidity(password.value === confirmation.value ? '' : 'Passwords do not match.');
    if (!/[A-Za-z]/.test(password.value) || !/[0-9]/.test(password.value)) password.setCustomValidity('Use at least one letter and one number.');
    else password.setCustomValidity('');
    if (!form.reportValidity()) return;
    showStatus('register-status','Registration form completed successfully. Secure submission will be enabled when the website service is connected. No personal information was saved or sent from this review page.','success');
  });
  document.querySelector('#confirm-password').addEventListener('input', (event) => event.currentTarget.setCustomValidity(''));
  document.querySelector('#mobile').addEventListener('input', (event) => event.currentTarget.setCustomValidity(''));
  document.querySelector('#postal-code').addEventListener('input', (event) => event.currentTarget.setCustomValidity(''));
})();
