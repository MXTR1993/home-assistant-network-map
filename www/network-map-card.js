class NetworkMapCard extends HTMLElement {
  constructor() {
    super();
    this._dragState = null;
    this._nodes = new Map();
  }

  setConfig(config) {
    this._config = config || {};
  }

  set hass(hass) {
    this._hass = hass;
    if (!hass) return;
    if (!this._content) {
      this._build();
    }
    this._update();
  }

  _build() {
    this.innerHTML = '';
    const card = document.createElement('ha-card');
    card.style.padding = '16px';
    card.style.display = 'block';

    const title = this._config.title || 'Network Map';
    const header = document.createElement('div');
    header.style.fontSize = '18px';
    header.style.fontWeight = 'bold';
    header.style.marginBottom = '12px';
    header.style.color = 'var(--primary-text-color, #212121)';
    header.textContent = title;
    card.appendChild(header);

    const container = document.createElement('div');
    container.style.width = '100%';
    container.style.height = (this._config.height || '500') + 'px';
    container.style.overflow = 'hidden';
    container.style.position = 'relative';
    container.style.background = 'var(--card-background-color, #fafafa)';
    container.style.borderRadius = '12px';
    container.style.border = '1px solid var(--divider-color, #e0e0e0)';

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', '0 0 1600 1200');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.style.cursor = 'grab';

    const defs = document.createElementNS(svgNS, 'defs');
    const pattern = document.createElementNS(svgNS, 'pattern');
    pattern.setAttribute('id', 'grid');
    pattern.setAttribute('width', '40');
    pattern.setAttribute('height', '40');
    pattern.setAttribute('patternUnits', 'userSpaceOnUse');
    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('d', 'M 40 0 L 0 0 0 40');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', 'var(--divider-color, #e0e0e0)');
    path.setAttribute('stroke-width', '1');
    pattern.appendChild(path);
    defs.appendChild(pattern);
    svg.appendChild(defs);

    const bg = document.createElementNS(svgNS, 'rect');
    bg.setAttribute('width', '1600');
    bg.setAttribute('height', '1200');
    bg.setAttribute('fill', 'url(#grid)');
    svg.appendChild(bg);

    this._svg = svg;
    this._svgNS = svgNS;

    container.appendChild(svg);
    card.appendChild(container);
    this.appendChild(card);
    this._content = card;

    window.addEventListener('mouseup', () => this._endDrag());
    window.addEventListener('touchend', () => this._endDrag());
    window.addEventListener('mousemove', (e) => this._onDrag(e));
    window.addEventListener('touchmove', (e) => this._onDrag(e), { passive: false });
  }

  _getEntities() {
    if (!this._hass || !this._hass.states) return [];
    return Object.values(this._hass.states).filter((e) => {
      if (e.entity_id.startsWith('binary_sensor.network_map_')) return true;
      if (e.entity_id.startsWith('binary_sensor.') && e.attributes && e.attributes.device_id) return true;
      return false;
    });
  }

  _update() {
    const entities = this._getEntities();
    const currentIds = new Set(entities.map((e) => e.entity_id));

    for (const [id, node] of this._nodes) {
      if (!currentIds.has(id)) {
        node.g.remove();
        this._nodes.delete(id);
      }
    }

    if (entities.length === 0) {
      this._showHelpMessage();
    } else {
      this._hideHelpMessage();
    }

    for (const entity of entities) {
      const attr = entity.attributes || {};
      const x = attr.position_x ?? 100;
      const y = attr.position_y ?? 100;
      const type = attr.device_type || 'generic';
      const online = entity.state === 'on';
      const name = attr.friendly_name || entity.entity_id;

      if (this._nodes.has(entity.entity_id)) {
        this._updateNode(entity.entity_id, x, y, online, name, type);
      } else {
        this._createNode(entity.entity_id, x, y, online, name, type);
      }
    }
  }

  _showHelpMessage() {
    if (this._helpMessage) return;
    const svgNS = this._svgNS;
    const g = document.createElementNS(svgNS, 'g');
    g.setAttribute('id', 'network-map-help');

    const text = document.createElementNS(svgNS, 'text');
    text.setAttribute('x', '800');
    text.setAttribute('y', '500');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '24');
    text.setAttribute('fill', 'var(--primary-text-color, #999)');
    text.setAttribute('font-family', 'sans-serif');
    text.textContent = 'Nessun dispositivo trovato.';

    const text2 = document.createElementNS(svgNS, 'text');
    text2.setAttribute('x', '800');
    text2.setAttribute('y', '540');
    text2.setAttribute('text-anchor', 'middle');
    text2.setAttribute('font-size', '18');
    text2.setAttribute('fill', 'var(--secondary-text-color, #777)');
    text2.setAttribute('font-family', 'sans-serif');
    text2.textContent = 'Aggiungi dispositivi da Impostazioni -> Dispositivi e servizi -> Network Map.';

    g.appendChild(text);
    g.appendChild(text2);
    this._svg.appendChild(g);
    this._helpMessage = g;
  }

  _hideHelpMessage() {
    if (this._helpMessage) {
      this._helpMessage.remove();
      this._helpMessage = null;
    }
  }

  _createNode(entityId, x, y, online, name, type) {
    const svgNS = this._svgNS;
    const g = document.createElementNS(svgNS, 'g');
    g.style.cursor = 'pointer';
    g.setAttribute('transform', `translate(${x}, ${y})`);

    const circle = document.createElementNS(svgNS, 'circle');
    circle.setAttribute('r', '36');
    circle.setAttribute('fill', online ? '#4caf50' : '#f44336');
    circle.setAttribute('stroke', 'var(--card-background-color, #fff)');
    circle.setAttribute('stroke-width', '4');
    circle.setAttribute('filter', 'drop-shadow(0px 3px 6px rgba(0,0,0,0.25))');

    const emoji = this._getEmoji(type);
    const text = document.createElementNS(svgNS, 'text');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('dy', '0.35em');
    text.setAttribute('font-size', '32');
    text.setAttribute('pointer-events', 'none');
    text.textContent = emoji;

    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('y', '58');
    label.setAttribute('font-size', '14');
    label.setAttribute('fill', 'var(--primary-text-color, #212121)');
    label.setAttribute('font-family', 'var(--paper-font-body1_-_font-family, sans-serif)');
    label.setAttribute('font-weight', '600');
    label.setAttribute('pointer-events', 'none');
    label.textContent = name;

    // Status dot (green pulse for online)
    const dot = document.createElementNS(svgNS, 'circle');
    dot.setAttribute('cx', '24');
    dot.setAttribute('cy', '-24');
    dot.setAttribute('r', '6');
    dot.setAttribute('fill', online ? '#81c784' : '#e57373');
    dot.setAttribute('stroke', '#fff');
    dot.setAttribute('stroke-width', '2');
    dot.setAttribute('pointer-events', 'none');

    g.appendChild(circle);
    g.appendChild(text);
    g.appendChild(dot);
    g.appendChild(label);

    const startDrag = (e) => {
      e.preventDefault();
      const evt = e.touches ? e.touches[0] : e;
      const pt = this._svg.createSVGPoint();
      pt.x = evt.clientX;
      pt.y = evt.clientY;
      const svgP = pt.matrixTransform(this._svg.getScreenCTM().inverse());
      this._dragState = {
        entityId,
        startX: x,
        startY: y,
        mouseStartX: svgP.x,
        mouseStartY: svgP.y,
        g,
      };
      this._svg.style.cursor = 'grabbing';
    };

    g.addEventListener('mousedown', startDrag);
    g.addEventListener('touchstart', startDrag, { passive: false });

    this._svg.appendChild(g);
    this._nodes.set(entityId, { g, circle, text, label, dot });
  }

  _updateNode(entityId, x, y, online, name, type) {
    const node = this._nodes.get(entityId);
    if (!node) return;
    node.g.setAttribute('transform', `translate(${x}, ${y})`);
    node.circle.setAttribute('fill', online ? '#4caf50' : '#f44336');
    node.text.textContent = this._getEmoji(type);
    node.label.textContent = name;
    node.dot.setAttribute('fill', online ? '#81c784' : '#e57373');
  }

  _onDrag(e) {
    if (!this._dragState) return;
    e.preventDefault();
    const evt = e.touches ? e.touches[0] : e;
    const pt = this._svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    const svgP = pt.matrixTransform(this._svg.getScreenCTM().inverse());

    const dx = svgP.x - this._dragState.mouseStartX;
    const dy = svgP.y - this._dragState.mouseStartY;

    const newX = this._dragState.startX + dx;
    const newY = this._dragState.startY + dy;

    this._dragState.g.setAttribute('transform', `translate(${newX}, ${newY})`);
    this._dragState.currentX = newX;
    this._dragState.currentY = newY;
  }

  _endDrag() {
    if (!this._dragState) return;
    const { entityId, currentX, currentY } = this._dragState;
    this._svg.style.cursor = 'grab';
    this._dragState = null;

    if (currentX !== undefined && this._hass) {
      const entity = this._hass.states[entityId];
      if (entity && entity.attributes.device_id) {
        this._hass.callService('network_map', 'update_position', {
          device_id: entity.attributes.device_id,
          x: Math.round(currentX),
          y: Math.round(currentY),
        });
      }
    }
  }

  _getEmoji(type) {
    const map = {
      camera: '📹',
      nas: '💾',
      switch: '🔀',
      access_point: '📡',
      router: '🌐',
      server: '🖥️',
      generic: '💻',
    };
    return map[type] || map.generic;
  }

  getCardSize() {
    return 5;
  }
}

customElements.define('network-map-card', NetworkMapCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'network-map-card',
  name: 'Network Map Card',
  description: 'Visualizza i dispositivi della rete su una mappa interattiva.',
});
