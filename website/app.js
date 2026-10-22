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

  const slides = [
    ['assets/software-home.png','Complete Home workspace','Kundali, calculations, dasha periods and native details together.'],
    ['assets/software-north-kundali.png','North Indian kundali','KP Cusp Chart and Lagna Chart with clear planet labels.'],
    ['assets/software-kundali.png','South Indian kundali','Birth and bhav-chalit chart with connected calculation tables.'],
    ['assets/screens/basic.jpg','Birth details','Natal and KP Horary chart details, place, coordinates and time settings.'],
    ['assets/screens/basic-information.jpg','Basic information','Native chart facts and birth Panchang information.'],
    ['assets/screens/admin-calculations.jpg','Administrator calculations','Detailed calculation review for advanced users.'],
    ['assets/screens/mdcalc.jpg','DBA and MAP periods','Connected Mahadasha, Bhukti, Antara and deeper timing periods.'],
    ['assets/screens/karyesh.jpg','Significators','Planet and house significators using KP calculation methods.'],
    ['assets/screens/education-profession.jpg','Education and profession','Study of education and professional house combinations.'],
    ['assets/screens/disease.jpg','Disease analysis','Sixth-house references and health-related significator study.'],
    ['assets/screens/dasha-promise.jpg','Dasha Promise','DBA event promise, supporting periods and gochar evidence.'],
    ['assets/screens/prediction.jpg','Prediction','Relevant-house groups and prediction evidence.'],
    ['assets/screens/muhurta.jpg','Muhurta','Traditional Panchang timing with KP support.'],
    ['assets/screens/event-promise.jpg','Event Promise','Cusp and event-house analysis for a selected matter.'],
    ['assets/screens/nadi-astrology.jpg','Nadi Astrology','Planet, star and sub relationships in the Nadi workspace.'],
    ['assets/screens/matchmaking.jpg','KP Matchmaking','Traditional Ashtakoota, Manglik and KP compatibility methods.'],
    ['assets/screens/aspects.jpg','Western aspects','Planetary aspect table with configurable angles and orb limits.'],
    ['assets/screens/transit.jpg','Transit reader','All selected planets through event-significator star and sub.'],
    ['assets/screens/transit-chart.jpg','Transit chart','Transit planet positions with Rashi and Bhav charts.'],
    ['assets/screens/transit-panchang.jpg','Transit Panchang','Daily Panchang, solar times, Choghadiya and auspicious periods.'],
    ['assets/screens/ephemeris.jpg','Daily ephemeris','Date-wise planet positions for practical transit study.'],
    ['assets/screens/hit-theory.jpg','HIT Theory','HIT analysis and supporting remedial reference.'],
    ['assets/screens/vedic-kundali.jpg','Vedic Kundali','Traditional Vedic chart and report tools.'],
    ['assets/screens/south9.jpg','South Indian chart workspace','South Indian kundali with Basic, Four-fold, Six-fold, Four-step and Nadi calculations.'],
    ['assets/screens/tutorial.jpg','Software tutorial','Guidance for learning and using KP MASTER features.'],
    ['assets/screens/resources.jpg','KP Resources','Reference topics and working notes inside the software.'],
    ['assets/screens/report.jpg','Print report','A4 preview, print and PDF report workspace.'],
    ['assets/screens/astrosettings.jpg','Astrologer settings','Language, colours, chart display, place and report preferences.'],
    ['assets/screens/home.jpg','Home with live ruling planets','Current chart overview with live RP and quick tools.']
  ];
  const image = document.querySelector('#slide-image');
  const link = document.querySelector('#slide-link');
  const title = document.querySelector('#slide-title');
  const description = document.querySelector('#slide-description');
  const counter = document.querySelector('#slide-counter');
  const thumbnails = document.querySelector('#slide-thumbnails');
  const playButton = document.querySelector('#slide-play');
  if (image && link && title && description && counter && thumbnails && playButton) {
    let index = 0;
    let paused = false;
    let timer;
    const render = (nextIndex, userAction = false) => {
      index = (nextIndex + slides.length) % slides.length;
      const [src, heading, text] = slides[index];
      image.src = src;
      image.alt = `Actual KP MASTER screen: ${heading}`;
      link.href = src;
      title.textContent = heading;
      description.textContent = text;
      counter.textContent = `${index + 1} / ${slides.length}`;
      thumbnails.querySelectorAll('button').forEach((button, position) => {
        const active = position === index;
        button.setAttribute('aria-current', active ? 'true' : 'false');
        if (active && userAction) button.scrollIntoView({block:'nearest',inline:'center',behavior:'smooth'});
      });
    };
    slides.forEach(([src, heading], position) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', `Show ${heading}`);
      button.innerHTML = `<img src="${src}" alt="" loading="lazy"><span>${heading}</span>`;
      button.addEventListener('click', () => render(position, true));
      thumbnails.append(button);
    });
    const startTimer = () => {
      clearInterval(timer);
      if (!paused && !matchMedia('(prefers-reduced-motion: reduce)').matches) timer = setInterval(() => render(index + 1), 5000);
    };
    document.querySelector('#slide-previous').addEventListener('click', () => { render(index - 1, true); startTimer(); });
    document.querySelector('#slide-next').addEventListener('click', () => { render(index + 1, true); startTimer(); });
    playButton.addEventListener('click', () => {
      paused = !paused;
      playButton.textContent = paused ? 'Play slideshow' : 'Pause slideshow';
      playButton.setAttribute('aria-pressed', String(paused));
      startTimer();
    });
    image.addEventListener('error', () => { description.textContent = 'This screenshot could not be loaded. Please use the latest complete website folder.'; });
    document.querySelector('.software-slider').addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') render(index - 1, true);
      if (event.key === 'ArrowRight') render(index + 1, true);
    });
    render(0);
    startTimer();
  }
})();
