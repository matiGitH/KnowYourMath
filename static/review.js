function toggleTopic(header) {
    const topic = header.parentElement;
    const materials = topic.querySelector('.materials');
    const isOpen = topic.classList.contains('open');

    if (isOpen) {
    materials.style.height = materials.scrollHeight + 'px';
    requestAnimationFrame(() => {
        topic.classList.remove('open');
        materials.style.height = '0px';
    });
    } else {
    topic.classList.add('open');
    materials.style.height = materials.scrollHeight + 'px';
    materials.addEventListener('transitionend', () => {
        if (topic.classList.contains('open')) {
        materials.style.height = 'auto';
        }
    }, { once: true });
    }
}

function showDesc(material) {
    const desc = material.querySelector('.material-desc');

    // Fase 1: set max-height dinámico
    desc.style.maxHeight = desc.scrollHeight + 'px';

    // Fase 2: luego de un delay, activamos opacidad
    setTimeout(() => {
    desc.style.opacity = '1';
    desc.style.pointerEvents = 'auto';
    }, 150);
}

function hideDesc(material) {
    const desc = material.querySelector('.material-desc');

    // Fase 1: ocultar opacidad
    desc.style.opacity = '0';
    desc.style.pointerEvents = 'none';

    // Fase 2: luego de fade out, colapsamos altura
    setTimeout(() => {
    desc.style.maxHeight = '0';
    }, 300); // coincidir con transition-duration de opacity
}