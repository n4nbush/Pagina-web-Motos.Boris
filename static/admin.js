const priceSearch = document.querySelector('#price-search');
const brandFilter = document.querySelector('#brand-filter');
const serviceFilter = document.querySelector('#service-filter');
const priceCards = [...document.querySelectorAll('.price-card')];
const catalogCount = document.querySelector('#catalog-count');
const filteredEmpty = document.querySelector('#filtered-empty');

function filterPrices() {
  const search = priceSearch.value.trim().toLowerCase();
  const brand = brandFilter.value;
  const service = serviceFilter.value;
  let visibleCount = 0;

  priceCards.forEach((card) => {
    const matches = card.dataset.search.includes(search)
      && (!brand || card.dataset.brand === brand)
      && (!service || card.dataset.service === service);
    card.hidden = !matches;
    if (matches) visibleCount += 1;
  });

  catalogCount.textContent = `${visibleCount} ${visibleCount === 1 ? 'registro' : 'registros'}`;
  filteredEmpty.hidden = visibleCount !== 0;
}

if (priceSearch && brandFilter && serviceFilter) {
  priceSearch.addEventListener('input', filterPrices);
  brandFilter.addEventListener('change', filterPrices);
  serviceFilter.addEventListener('change', filterPrices);
}