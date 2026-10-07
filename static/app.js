const brandSelect = document.querySelector('#brand-select');
const modelSelect = document.querySelector('#model-select');
const serviceSelect = document.querySelector('#service-select');
const priceResult = document.querySelector('#price-result');
const emptyMessage = document.querySelector('#empty-message');
const priceValue = document.querySelector('#price-value');
const priceLabel = document.querySelector('#price-label');
const whatsappButton = document.querySelector('#whatsapp-button');
const whatsappNumber = '5491178310481';

const pesos = (cents) => `$ ${Number(cents).toLocaleString('es-AR')}`;

function resetServices(message) {
  serviceSelect.innerHTML = `<option value="">${message}</option>`;
  serviceSelect.disabled = true;
  priceResult.hidden = true;
  emptyMessage.hidden = false;
}

if (brandSelect && modelSelect) {
  brandSelect.addEventListener('change', async () => {
    const brandId = brandSelect.value;
    modelSelect.innerHTML = '<option value="">Cargando modelos...</option>';
    modelSelect.disabled = true;
    resetServices('Primero selecciona un modelo');

    if (!brandId) {
      modelSelect.innerHTML = '<option value="">Primero selecciona una marca</option>';
      return;
    }

    const response = await fetch(`/api/models/${brandId}`);
    const models = await response.json();
    modelSelect.innerHTML = models.length
      ? '<option value="">Selecciona un modelo</option>' + models.map((model) => `<option value="${model.id}">${model.name}</option>`).join('')
      : '<option value="">No hay modelos cargados todavía</option>';
    modelSelect.disabled = models.length === 0;
  });

  modelSelect.addEventListener('change', async () => {
    const modelId = modelSelect.value;
    resetServices('Cargando servicios...');
    if (!modelId) return;

    const response = await fetch(`/api/services/${modelId}`);
    const services = await response.json();
    serviceSelect.innerHTML = services.length
      ? '<option value="">Selecciona un servicio</option>' + services.map((service) => `<option value="${service.id}" data-price="${service.price_cents}" data-name="${service.name}">${service.name}</option>`).join('')
      : '<option value="">No hay servicios cargados todavía</option>';
    serviceSelect.disabled = services.length === 0;
  });

  serviceSelect.addEventListener('change', () => {
    const option = serviceSelect.selectedOptions[0];
    if (!option || !option.dataset.price) {
      priceResult.hidden = true;
      emptyMessage.hidden = false;
      return;
    }
    priceValue.textContent = pesos(option.dataset.price);
    priceLabel.textContent = option.dataset.name;
    priceResult.hidden = false;
    emptyMessage.hidden = true;
    const brand = brandSelect.selectedOptions[0]?.textContent.trim();
    const model = modelSelect.selectedOptions[0]?.textContent.trim();
    const message = `Hola, quisiera consultar por mi ${brand} ${model}. Me interesa el servicio de ${option.dataset.name}.`;
    whatsappButton.href = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
    whatsappButton.removeAttribute('aria-disabled');
  });
}