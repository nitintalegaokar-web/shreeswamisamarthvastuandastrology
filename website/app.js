(() => {
  'use strict';
  const phone = '918412098690';
  document.querySelectorAll('.whatsapp-link').forEach((link) => {
    const message = link.dataset.message || 'Hello, please share KP MASTER details.';
    link.href = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });

  const menuButton = document.querySelector('.menu-button');
  const navigation = document.querySelector('#site-nav');
  const closeMenu = () => {
    navigation.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
  };
  menuButton.addEventListener('click', () => {
    const isOpen = navigation.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
  });
  navigation.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });
  document.querySelector('#year').textContent = new Date().getFullYear();
})();
