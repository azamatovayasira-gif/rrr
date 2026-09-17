(() => {
  const toggle = document.querySelector('[data-theme-toggle]');
  const savedTheme = localStorage.getItem('anonka-theme');
  if (savedTheme === 'night') document.body.classList.add('night');
  toggle?.setAttribute('aria-pressed', String(document.body.classList.contains('night')));
  toggle?.addEventListener('click', () => {
    const isNight = document.body.classList.toggle('night');
    localStorage.setItem('anonka-theme', isNight ? 'night' : 'day');
    toggle.setAttribute('aria-pressed', String(isNight));
  });

  const mapElement = document.getElementById('leaflet-map');
  if (mapElement && window.L) {
    const regions = {
      kyrgyzstan: { center: [41.2044, 74.7661], zoom: 7 },
      kazakhstan: { center: [48.0196, 66.9237], zoom: 5 },
      uzbekistan: { center: [41.3775, 64.5853], zoom: 6 },
      tajikistan: { center: [38.861, 71.2761], zoom: 7 },
      turkey: { center: [38.9637, 35.2433], zoom: 6 },
      world: { center: [35, 55], zoom: 3 },
    };
    const regionSelect = document.getElementById('region-select');
    const savedRegion = localStorage.getItem('anonka-region') || 'kyrgyzstan';
    if (regionSelect) regionSelect.value = savedRegion;
    const initialRegion = regions[savedRegion] || regions.kyrgyzstan;
    const map = L.map(mapElement, { zoomControl: false }).setView(initialRegion.center, initialRegion.zoom);
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 19 });
    let tileErrors = 0;
    tiles.on('tileerror', () => {
      tileErrors += 1;
      if (tileErrors === 1) {
        const status = document.createElement('div');
        status.className = 'map-status';
        status.textContent = 'Не удалось загрузить часть карты. Проверь интернет и обнови страницу.';
        mapElement.append(status);
      }
    });
    tiles.addTo(map);
    setTimeout(() => map.invalidateSize(), 150);
    regionSelect?.addEventListener('change', () => {
      const region = regions[regionSelect.value] || regions.kyrgyzstan;
      localStorage.setItem('anonka-region', regionSelect.value);
      map.setView(region.center, region.zoom);
    });
    fetch(window.mapDataUrl).then(response => response.ok ? response.json() : []).then(markers => {
      markers.forEach((marker, index) => {
        const icon = L.divIcon({ className: 'numbered-marker', html: `<span>${index + 1}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
        L.marker([marker.lat, marker.lng], { icon }).addTo(map).bindPopup(marker.label);
      });
      if (markers.length) map.setView([markers[0].lat, markers[0].lng], 12);
    }).catch(() => {});
  }

  document.querySelectorAll('.share-location').forEach(button => button.addEventListener('click', () => {
    if (!navigator.geolocation) return alert('Геолокация недоступна. Разреши её в браузере или открой сайт через localhost.');
    navigator.geolocation.getCurrentPosition(position => {
      const form = document.getElementById('location-form');
      form.querySelector('[name=friend_id]').value = button.dataset.friendId;
      form.querySelector('[name=latitude]').value = position.coords.latitude.toFixed(6);
      form.querySelector('[name=longitude]').value = position.coords.longitude.toFixed(6);
      form.submit();
    }, () => alert('Не удалось получить текущую метку.'));
  }));

  document.querySelectorAll('.share-post').forEach(button => button.addEventListener('click', async () => {
    const url = button.dataset.shareUrl;
    try {
      if (navigator.share) await navigator.share({ title: 'anonka', text: 'Пост из anonka', url });
      else { await navigator.clipboard.writeText(url); alert('Ссылка на пост скопирована.'); }
    } catch (error) { if (error.name !== 'AbortError') alert(`Ссылка на пост: ${url}`); }
  }));

  document.querySelectorAll('.copy-contact').forEach(button => button.addEventListener('click', async () => {
    await navigator.clipboard.writeText(button.dataset.copy);
    button.textContent = 'Скопировано';
  }));

  const imageInput = document.querySelector('.post-image-input');
  const imagePreview = document.getElementById('image-preview');
  imageInput?.addEventListener('change', () => {
    const image = imageInput.files?.[0];
    if (!image) {
      imagePreview.hidden = true;
      imagePreview.innerHTML = '';
      return;
    }
    imagePreview.hidden = false;
    imagePreview.innerHTML = `<img src="${URL.createObjectURL(image)}" alt="Предпросмотр фото"><span>${image.name}</span>`;
  });

  const videoInput = document.querySelector('.post-video-input');
  const videoPreview = document.getElementById('video-preview');
  videoInput?.addEventListener('change', () => {
    const video = videoInput.files?.[0];
    if (!video) {
      videoPreview.hidden = true;
      videoPreview.innerHTML = '';
      return;
    }
    videoPreview.hidden = false;
    videoPreview.innerHTML = `<video controls src="${URL.createObjectURL(video)}"></video><span>${video.name}</span>`;
  });

  const chatMessages = document.getElementById('chat-messages');
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

  document.getElementById('save-map-location')?.addEventListener('click', () => {
    const status = document.querySelector('.map-number');
    if (!navigator.geolocation) {
      if (status) status.textContent = 'Геолокация недоступна';
      return;
    }
    navigator.geolocation.getCurrentPosition(position => {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/location/save/';
      form.innerHTML = `<input name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''}"><input name="latitude" value="${position.coords.latitude}"><input name="longitude" value="${position.coords.longitude}">`;
      document.body.append(form);
      form.submit();
    }, () => { if (status) status.textContent = 'Разреши доступ к геолокации'; });
  });

  document.querySelectorAll('[data-sticker]').forEach(button => button.addEventListener('click', () => {
    const input = document.querySelector('#message-form input[name=sticker]');
    const text = document.querySelector('#message-form input[name=text]');
    input.value = button.dataset.sticker;
    text.value = `${text.value}${button.dataset.sticker}`;
    text.focus();
  }));

  const voiceButton = document.getElementById('voice-button');
  const voiceStatus = document.getElementById('voice-status');
  let recorder;
  let voiceChunks = [];
  voiceButton?.addEventListener('click', async () => {
    if (recorder?.state === 'recording') {
      recorder.stop();
      voiceButton.textContent = '● Голос';
      voiceStatus.textContent = 'Отправляю голосовое...';
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      voiceStatus.textContent = 'Запись голоса не поддерживается этим браузером.';
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    voiceChunks = [];
    recorder.ondataavailable = event => voiceChunks.push(event.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach(track => track.stop());
      const form = document.getElementById('message-form');
      const data = new FormData(form);
      data.set('text', '');
      data.set('sticker', '');
      data.append('audio', new Blob(voiceChunks, { type: recorder.mimeType || 'audio/webm' }), 'voice.webm');
      await fetch(form.action, { method: 'POST', body: data, headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } });
      window.location.reload();
    };
    recorder.start();
    voiceButton.textContent = '■ Остановить';
    voiceStatus.textContent = 'Идёт запись...';
  });
})();
